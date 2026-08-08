/**
 * Status indicator widget shown in the JupyterLab status bar.
 *
 * Displays connection state and, when a swarm is active, the number of
 * live workers.  Mirrors the StatusBar.ts role in the IDE plugin.
 */

import { Widget } from '@lumino/widgets';
import { SwarmStateManager } from './SwarmStateManager';
import { KernelCommClient } from './WsClient';
import { isTeamActive, workerLanes } from './SwarmState';

export class StatusIndicator extends Widget {
  private _label: HTMLSpanElement;

  constructor(
    private readonly _client: KernelCommClient,
    private readonly _swarmMgr: SwarmStateManager,
  ) {
    super();
    this.addClass('jiuwenswarm-status-indicator');

    this._label = document.createElement('span');
    this._label.style.fontSize = '12px';
    this._label.style.padding = '0 8px';
    this._label.style.cursor = 'default';
    this.node.appendChild(this._label);

    _client.onEvent(() => this._update());
    _swarmMgr.onChange(() => this._update());
    this._update();
  }

  private _update(): void {
    const state = this._swarmMgr.state;

    if (!this._client.isConnected) {
      this._label.textContent = '⬤ JiuwenSwarm: disconnected';
      this._label.style.color = '#f14c4c';
      return;
    }

    if (isTeamActive(state)) {
      const workers = workerLanes(state).filter(l => l.status === 'ACTIVE');
      this._label.textContent = `⬤ JiuwenSwarm: ${workers.length} agent${workers.length === 1 ? '' : 's'} active`;
      this._label.style.color = '#4ec9b0';
    } else {
      this._label.textContent = '⬤ JiuwenSwarm: ready';
      this._label.style.color = '#73c991';
    }
  }
}
