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
 */

import type { IComm } from '@jupyterlab/services/lib/kernel/comm';
import { KernelEvent, KernelBoundMessage } from './protocol';

type EventHandler = (event: KernelEvent) => void;

export class KernelCommClient {
  private _comm: IComm | null = null;
  private _handlers: EventHandler[] = [];
  private _connected = false;

  constructor(private readonly _commTarget: string = 'jiuwenswarm') {}

  // ── Lifecycle ─────────────────────────────────────────────────────────────

  async connect(kernel: any): Promise<void> {
    if (this._connected) return;

    this._comm = kernel.createComm(this._commTarget);
    this._comm.onMsg = (msg: any) => {
      const data = msg.content?.data as KernelEvent | undefined;
      if (data) {
        this._dispatch(data);
      }
    };
    this._comm.onClose = () => {
      this._connected = false;
    };

    await this._comm.open({});
    this._connected = true;
  }

  disconnect(): void {
    if (this._comm) {
      void this._comm.close();
      this._comm = null;
    }
    this._connected = false;
  }

  get isConnected(): boolean {
    return this._connected;
  }

  // ── Messaging ─────────────────────────────────────────────────────────────

  send(message: KernelBoundMessage): void {
    if (!this._comm || !this._connected) {
      console.warn('[jiuwenswarm] comm not connected, dropping message', message);
      return;
    }
    void this._comm.send(message as Record<string, unknown>);
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
