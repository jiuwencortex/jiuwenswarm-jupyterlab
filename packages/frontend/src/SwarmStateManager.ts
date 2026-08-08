/**
 * Manages live swarm state updates from the kernel.
 * Mirrors SwarmStateManager.ts in the IDE plugin.
 */

import { KernelCommClient } from './WsClient';
import { SwarmState, EMPTY_STATE, applySnapshot } from './SwarmState';

type StateListener = (state: SwarmState) => void;

export class SwarmStateManager {
  private _state: SwarmState = EMPTY_STATE;
  private _listeners: StateListener[] = [];

  constructor(client: KernelCommClient) {
    client.onEvent(event => {
      if (event.type === 'swarm_snapshot') {
        this._state = applySnapshot(this._state, event.snapshot);
        this._notify();
      }
    });
  }

  get state(): SwarmState {
    return this._state;
  }

  onChange(listener: StateListener): () => void {
    this._listeners.push(listener);
    return () => {
      this._listeners = this._listeners.filter(l => l !== listener);
    };
  }

  private _notify(): void {
    for (const l of this._listeners) {
      try { l(this._state); } catch { /* ignore */ }
    }
  }
}
