/**
 * Kernel communication bridge.
 *
 * In the IDE plugin this was a WebSocket client (WsClient.ts) connecting to
 * port 18092 over the E2AEnvelope protocol.  In JupyterLab we communicate
 * with the Python kernel directly via Jupyter comm, which avoids the need for
 * a running server process entirely.
 *
 * This module wraps the Jupyter comm API behind the same event-emitter
 * interface that ChatPanel and SwarmMapPanel already expect, so those panels
 * require minimal changes.
 *
 * Multi-kernel support: one comm per kernel, keyed by kernel.id.  The active
 * kernel is the one that send() routes to.  Legacy connect()/disconnect()/
 * isConnected are preserved as thin wrappers so existing call-sites compile.
 */

import type { KernelEvent, KernelBoundMessage } from './protocol';

type AnyComm = {
  onMsg: (msg: any) => void;
  onClose: () => void;
  open: (data: any) => Promise<void>;
  send: (data: any) => void;
  close: () => void;
};

type EventHandler = (event: KernelEvent) => void;

export class KernelCommClient {
  private _comms: Map<string, AnyComm> = new Map();
  private _activeKernelId: string | null = null;
  private _handlers: EventHandler[] = [];

  constructor(private readonly _commTarget: string = 'jiuwenswarm') {}

  // ── Multi-kernel lifecycle ─────────────────────────────────────────────────

  async connectKernel(id: string, kernel: any): Promise<void> {
    if (this._comms.has(id)) return; // idempotent

    const comm: AnyComm = kernel.createComm(this._commTarget);
    comm.onMsg = (msg: any) => {
      const data = msg.content?.data as KernelEvent | undefined;
      if (data) this._dispatch(data);
    };
    comm.onClose = () => {
      this._comms.delete(id);
      if (this._activeKernelId === id) this._activeKernelId = null;
    };

    await comm.open({});
    this._comms.set(id, comm);
  }

  disconnectKernel(id: string): void {
    const comm = this._comms.get(id);
    if (comm) {
      void comm.close();
      this._comms.delete(id);
    }
    if (this._activeKernelId === id) this._activeKernelId = null;
  }

  setActiveKernel(id: string): void {
    if (!this._comms.has(id)) {
      console.warn('[jiuwenswarm] setActiveKernel: kernel not connected', id);
      return;
    }
    this._activeKernelId = id;
  }

  isKernelConnected(id: string): boolean {
    return this._comms.has(id);
  }

  get activeKernelId(): string | null {
    return this._activeKernelId;
  }

  get connectedKernelIds(): string[] {
    return Array.from(this._comms.keys());
  }

  // ── Legacy wrappers (single-kernel callers) ────────────────────────────────

  async connect(kernel: any): Promise<void> {
    await this.connectKernel(kernel.id, kernel);
    this.setActiveKernel(kernel.id);
  }

  disconnect(): void {
    if (this._activeKernelId !== null) {
      this.disconnectKernel(this._activeKernelId);
    }
  }

  get isConnected(): boolean {
    return this._activeKernelId !== null && this._comms.has(this._activeKernelId);
  }

  // ── Messaging ─────────────────────────────────────────────────────────────

  send(message: KernelBoundMessage): void {
    const comm = this._activeKernelId ? this._comms.get(this._activeKernelId) : undefined;
    if (!comm) {
      console.warn('[jiuwenswarm] no active kernel comm, dropping message', message);
      return;
    }
    void comm.send(message as unknown as Record<string, unknown>);
  }

  // ── Subscriptions ─────────────────────────────────────────────────────────

  onEvent(handler: EventHandler): () => void {
    this._handlers.push(handler);
    return () => {
      this._handlers = this._handlers.filter(h => h !== handler);
    };
  }

  // ── Internal ──────────────────────────────────────────────────────────────

  private _dispatch(event: KernelEvent): void {
    for (const handler of this._handlers) {
      try {
        handler(event);
      } catch (err) {
        console.error('[jiuwenswarm] event handler threw', err);
      }
    }
  }
}
