/**
 * Swarm map panel — displays agent team activity.
 *
 * Embeds shared-webview/swarm_map.html in an iframe and pushes swarm
 * snapshot events via postMessage, mirroring the VS Code SwarmMapPanel.
 */

import { Widget } from '@lumino/widgets';
import { SwarmStateManager } from './SwarmStateManager';
import { KernelCommClient } from './WsClient';

const SWARM_MAP_PATH = '/lab/extensions/@jiuwenswarm/jupyterlab/swarm_map.html';

export class SwarmMapPanel extends Widget {
  static readonly ID = 'jiuwenswarm-swarm-map-panel';
  static readonly TITLE = 'Swarm Map';

  private _iframe: HTMLIFrameElement;
  private _unsubscribe: (() => void) | null = null;

  constructor(
    private readonly _client: KernelCommClient,
    private readonly _swarmMgr: SwarmStateManager,
  ) {
    super();
    this.id = SwarmMapPanel.ID;
    this.title.label = SwarmMapPanel.TITLE;
    this.title.closable = true;
    this.addClass('jiuwenswarm-swarm-map-panel');

    this._iframe = document.createElement('iframe');
    this._iframe.style.cssText = 'width:100%;height:100%;border:none;';
    this._iframe.src = SWARM_MAP_PATH;
    this.node.style.cssText = 'display:flex;flex-direction:column;height:100%;overflow:hidden;';
    this.node.appendChild(this._iframe);

    this._iframe.addEventListener('load', () => this._onLoaded());

    this._unsubscribe = _swarmMgr.onChange(() => {
      this._pushSnapshot();
    });
  }

  dispose(): void {
    if (this._unsubscribe) {
      this._unsubscribe();
      this._unsubscribe = null;
    }
    super.dispose();
  }

  // ── Private ──────────────────────────────────────────────────────────────

  private _onLoaded(): void {
    // Notify swarm_map.html that we are in Jupyter mode.
    // The iframe sets up window.__swarmReceive; we call it via postMessage.
    const win = this._iframe.contentWindow;
    if (!win) return;
    win.postMessage({ type: 'swarm_ready' }, '*');

    // Push current state immediately
    this._pushSnapshot();
  }

  private _pushSnapshot(): void {
    const win = this._iframe.contentWindow;
    if (!win) return;
    const { snapshot } = this._swarmMgr.state;
    if (snapshot) {
      win.postMessage({ type: 'swarm_snapshot', snapshot }, '*');
    }
  }
}
