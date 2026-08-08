/**
 * Session management for the JupyterLab sidebar panel.
 *
 * Mirrors the role of SessionManager.ts in the IDE plugin, adapted to use
 * Jupyter comm messages instead of WebSocket.
 */

import { KernelCommClient } from './WsClient';
import { SessionInfo, AgentMode } from './protocol';
import { v4 as uuidv4 } from 'uuid';

export class SessionManager {
  private _sessions: SessionInfo[] = [];
  private _activeSessionId: string | null = null;
  private _listeners: Array<() => void> = [];

  constructor(private readonly _client: KernelCommClient) {
    _client.onEvent(event => {
      if (event.type === 'sessions') {
        this._sessions = event.sessions;
        this._notify();
      }
    });
  }

  get sessions(): SessionInfo[] {
    return this._sessions;
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
    };
    this._sessions = [info, ...this._sessions];
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
