/**
 * Session management for the JupyterLab sidebar panel.
 *
 * Mirrors the role of SessionManager.ts in the IDE plugin, adapted to use
 * Jupyter comm messages instead of WebSocket.
 *
 * Multi-kernel support: sessions are partitioned by kernel id.  The `sessions`
 * getter returns only the active kernel's sessions so all existing call-sites
 * (ChatPanel, SessionListPanel) work without changes.
 */

import { KernelCommClient } from './WsClient';
import { SessionInfo, KernelInfo, AgentMode } from './protocol';
import { v4 as uuidv4 } from 'uuid';

export class SessionManager {
  private _sessionsByKernel: Map<string, SessionInfo[]> = new Map();
  private _kernels: Map<string, KernelInfo> = new Map(); // id → label
  private _activeKernelId: string | null = null;
  private _activeSessionId: string | null = null;
  private _listeners: Array<() => void> = [];

  constructor(private readonly _client: KernelCommClient) {
    _client.onEvent(event => {
      if (event.type === 'sessions') {
        // Tag each session with the kernel that sent the event.
        const kernelId = this._client.activeKernelId;
        if (kernelId) {
          const tagged = event.sessions.map(s => ({ ...s, kernel_id: kernelId }));
          this._sessionsByKernel.set(kernelId, tagged);
        }
        this._notify();
      }
    });
  }

  // ── Kernel registration ────────────────────────────────────────────────────

  registerKernel(info: KernelInfo): void {
    this._kernels.set(info.id, info);
    if (!this._sessionsByKernel.has(info.id)) {
      this._sessionsByKernel.set(info.id, []);
    }
  }

  unregisterKernel(id: string): void {
    this._kernels.delete(id);
    this._sessionsByKernel.delete(id);
    if (this._activeKernelId === id) this._activeKernelId = null;
    this._notify();
  }

  setActiveKernel(id: string): void {
    this._activeKernelId = id;
    this._notify();
  }

  allKernels(): KernelInfo[] {
    return Array.from(this._kernels.values());
  }

  getKernelSessions(kernelId: string): SessionInfo[] {
    return this._sessionsByKernel.get(kernelId) ?? [];
  }

  // ── Active-kernel view (used by ChatPanel and existing callers) ────────────

  get sessions(): SessionInfo[] {
    if (!this._activeKernelId) return [];
    return this._sessionsByKernel.get(this._activeKernelId) ?? [];
  }

  get activeSessionId(): string | null {
    return this._activeSessionId;
  }

  set activeSessionId(id: string | null) {
    this._activeSessionId = id;
    this._notify();
  }

  createSession(mode: AgentMode = 'agent'): string {
    const id = `jupyter_${uuidv4().replace(/-/g, '').slice(0, 12)}`;
    const info: SessionInfo = {
      session_id: id,
      title: 'New session',
      created_at: new Date().toISOString(),
      mode,
      kernel_id: this._activeKernelId ?? undefined,
    };
    const bucket = this._sessionsByKernel.get(this._activeKernelId ?? '') ?? [];
    this._sessionsByKernel.set(this._activeKernelId ?? '', [info, ...bucket]);
    this._activeSessionId = id;
    this._notify();
    return id;
  }

  refresh(): void {
    this._client.send({ type: 'get_sessions' });
  }

  onChange(listener: () => void): () => void {
    this._listeners.push(listener);
    return () => {
      this._listeners = this._listeners.filter(l => l !== listener);
    };
  }

  private _notify(): void {
    for (const l of this._listeners) {
      try { l(); } catch { /* ignore */ }
    }
  }
}
