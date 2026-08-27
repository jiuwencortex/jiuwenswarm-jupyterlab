/**
 * Status indicator widget shown in the JupyterLab status bar.
 *
 * Displays:
 *   - Connection state (disconnected / ready / N agents active)
 *   - Accumulated session cost (from chat.final usage.cost_usd)
 *   - Active kernel/notebook label when more than one kernel is connected
 */

import { Widget } from '@lumino/widgets';
import { SwarmStateManager } from './SwarmStateManager';
import { KernelCommClient } from './WsClient';
import { SessionManager } from './SessionManager';
import { isTeamActive, workerLanes } from './SwarmState';

export class StatusIndicator extends Widget {
  private _label: HTMLSpanElement;
  private _sessionCost: number = 0; // USD accumulated for the current active kernel

  constructor(
    private readonly _client: KernelCommClient,
    private readonly _swarmMgr: SwarmStateManager,
    private readonly _sessionMgr: SessionManager,
  ) {
    super();
    this.addClass('jiuwenswarm-status-indicator');

    this._label = document.createElement('span');
    this._label.style.fontSize = '12px';
    this._label.style.padding = '0 8px';
    this._label.style.cursor = 'default';
    this.node.appendChild(this._label);

    _client.onEvent(event => {
      if (event.type === 'chat.final' && event.usage?.cost_usd != null) {
        this._sessionCost += event.usage.cost_usd;
      }
      this._update();
    });
    _swarmMgr.onChange(() => this._update());
    // Reset cost when the active kernel changes (different notebook = different session budget)
    _sessionMgr.onChange(() => {
      this._sessionCost = 0;
      this._update();
    });
    this._update();
  }

  private _update(): void {
    const state = this._swarmMgr.state;

    if (!this._client.isConnected) {
      this._label.textContent = '⬤ JiuwenSwarm: disconnected';
      this._label.style.color = '#f14c4c';
      return;
    }

    const suffix = this._buildSuffix();

    if (isTeamActive(state)) {
      const workers = workerLanes(state).filter(l => l.status === 'ACTIVE');
      const count = workers.length;
      this._label.textContent =
        `⬤ JiuwenSwarm: ${count} agent${count === 1 ? '' : 's'} active${suffix}`;
      this._label.style.color = '#4ec9b0';
    } else {
      this._label.textContent = `⬤ JiuwenSwarm: ready${suffix}`;
      this._label.style.color = '#73c991';
    }
  }

  /** Build the ` · label · $cost` suffix shown after the main status text. */
  private _buildSuffix(): string {
    const parts: string[] = [];

    // Show active notebook filename only when multiple kernels are connected
    const kernels = this._sessionMgr.allKernels();
    if (kernels.length > 1) {
      const activeId = this._client.activeKernelId;
      const active = kernels.find(k => k.id === activeId);
      if (active) {
        parts.push(active.label);
      }
    }

    // Show accumulated cost for this kernel's session
    if (this._sessionCost > 0) {
      parts.push(`$${this._sessionCost.toFixed(4)}`);
    }

    return parts.length > 0 ? ` · ${parts.join(' · ')}` : '';
  }
}
