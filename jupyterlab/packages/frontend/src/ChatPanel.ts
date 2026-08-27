/**
 * JupyterLab sidebar chat panel.
 *
 * Embeds the shared-webview chat.html in an iframe and bridges messages
 * via postMessage / window.__jupyter_send.  The iframe side detects
 * window.__jupyter_send (set by this panel on the iframe's contentWindow)
 * and uses it to send messages back up; events from the kernel come down
 * via postMessage.
 *
 * This mirrors the approach in ChatPanel.ts (VS Code) and the JCEF panel
 * (JetBrains), replacing vscodeApi / __jb_send with a Jupyter postMessage
 * bridge.
 */

import { Widget } from '@lumino/widgets';
import { KernelCommClient } from './WsClient';
import { SessionManager } from './SessionManager';
import { KernelEvent, KernelBoundMessage } from './protocol';

// Path to the shared-webview asset, served by the lab extension
const CHAT_HTML_PATH = '/lab/extensions/@jiuwenswarm/jupyterlab/chat.html';

export class ChatPanel extends Widget {
  static readonly ID = 'jiuwenswarm-chat-panel';
  static readonly TITLE = 'JiuwenSwarm';

  private _iframe: HTMLIFrameElement;
  private _unsubscribe: (() => void) | null = null;

  constructor(
    private readonly _client: KernelCommClient,
    private readonly _sessionMgr: SessionManager,
  ) {
    super();
    this.id = ChatPanel.ID;
    this.title.label = ChatPanel.TITLE;
    this.title.closable = true;
    this.addClass('jiuwenswarm-chat-panel');

    this._iframe = document.createElement('iframe');
    this._iframe.style.cssText = 'width:100%;height:100%;border:none;';
    this._iframe.src = CHAT_HTML_PATH;
    this.node.style.cssText = 'display:flex;flex-direction:column;height:100%;overflow:hidden;';
    this.node.appendChild(this._iframe);

    this._iframe.addEventListener('load', () => this._onIframeLoaded());
    this._unsubscribe = _client.onEvent(event => this._forwardToIframe(event));

    window.addEventListener('message', (e: MessageEvent) => this._onIframeMessage(e));
  }

  dispose(): void {
    if (this._unsubscribe) {
      this._unsubscribe();
      this._unsubscribe = null;
    }
    super.dispose();
  }

  // ── Private ──────────────────────────────────────────────────────────────

  private _onIframeLoaded(): void {
    const win = this._iframe.contentWindow;
    if (!win) return;

    // Install the __jupyter_send bridge on the iframe window
    // so that chat.html's send() function picks it up.
    (win as any).__jupyter_send = (jsonStr: string) => {
      try {
        const msg: KernelBoundMessage = JSON.parse(jsonStr);
        this._client.send(msg);
      } catch (err) {
        console.error('[jiuwenswarm] failed to parse message from iframe', err);
      }
    };

    // Also install __jupyter_dispatch so the iframe can call it directly
    // if needed (symmetric with __jb_dispatch on JetBrains).
    (win as any).__jupyter_dispatch = (event: KernelEvent) => {
      this._forwardToIframe(event);
    };

    // Notify iframe that the bridge is ready
    win.postMessage({ type: 'connected', server_version: '1.0', available_modes: ['agent', 'code', 'team', 'code.team'] }, '*');
  }

  private _forwardToIframe(event: KernelEvent): void {
    const win = this._iframe.contentWindow;
    if (!win) return;
    win.postMessage(event, '*');
  }

  private _onIframeMessage(e: MessageEvent): void {
    // Only handle messages from our own iframe
    if (e.source !== this._iframe.contentWindow) return;
    const msg = e.data as KernelBoundMessage;
    if (msg?.type) {
      this._client.send(msg);
    }
  }
}
