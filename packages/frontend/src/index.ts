/**
 * JiuwenSwarm JupyterLab frontend extension.
 *
 * Registers:
 *   - Sidebar chat panel (ChatPanel)
 *   - Sidebar session list panel (SessionListPanel)
 *   - Swarm map panel (SwarmMapPanel)
 *   - Status bar indicator (StatusIndicator)
 *   - Command palette entries
 *   - Keyboard shortcuts
 *   - Comm target for agent-inserted notebook cells
 *
 * Architecture: this extension communicates with the Python kernel via Jupyter
 * comm (KernelCommClient), which bridges to the in-process JupyterSwarm
 * instance.  No external server or WebSocket connection is required.
 */

import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin,
  ILayoutRestorer,
} from '@jupyterlab/application';
import { ICommandPalette, MainAreaWidget, WidgetTracker, showDialog, Dialog } from '@jupyterlab/apputils';
import { INotebookTracker, NotebookActions } from '@jupyterlab/notebook';
import { Widget } from '@lumino/widgets';
import { IStatusBar } from '@jupyterlab/statusbar';

import { KernelCommClient } from './WsClient';
import { SessionManager } from './SessionManager';
import { SwarmStateManager } from './SwarmStateManager';
import { ChatPanel } from './ChatPanel';
import { SwarmMapPanel } from './SwarmMapPanel';
import { StatusIndicator } from './StatusIndicator';
import { NotebookContextCollector } from './NotebookContextCollector';
import { SessionListPanel } from './SessionListPanel';
import { jiuwenIcon } from './icon';

const PLUGIN_ID = '@jiuwenswarm/jupyterlab:plugin';

// ---------------------------------------------------------------------------
// Cell-insert handler (comm → NotebookActions)
// ---------------------------------------------------------------------------

async function _handleCellInsert(
  data: Record<string, any>,
  tracker: INotebookTracker,
): Promise<void> {
  const notebookPanel = tracker.currentWidget;
  if (!notebookPanel) {
    console.warn('[jiuwenswarm] cell_insert: no active notebook');
    return;
  }
  const notebook = notebookPanel.content;

  // Insert a new cell below the currently active cell
  NotebookActions.insertBelow(notebook);
  const cell = notebook.activeCell;
  if (!cell) return;

  // Set source
  cell.model.sharedModel.setSource(data.source ?? '');

  // Switch to markdown if requested (default is code)
  if (data.cell_type === 'markdown') {
    NotebookActions.changeCellType(notebook, 'markdown');
  }

  // Tag cell as jiuwen-generated so the Python side can identify it later
  if (data.jiuwen_generated) {
    cell.model.setMetadata('jiuwen_generated', true);
  }

  // Optionally execute the inserted cell, with an optional confirmation dialog
  if (data.execute) {
    let confirmed = true;
    if (data.confirm_execute) {
      const result = await showDialog({
        title: 'Run generated cell?',
        body: 'JiuwenSwarm wants to execute the cell it just inserted. Run it now?',
        buttons: [Dialog.cancelButton(), Dialog.okButton({ label: 'Run' })],
      });
      confirmed = result.button.accept;
    }
    if (confirmed) {
      await NotebookActions.run(notebook, notebookPanel.sessionContext);
    }
  }
}

// ---------------------------------------------------------------------------
// Cell-replace handler (comm → diff dialog → NotebookActions)
// ---------------------------------------------------------------------------

/** Escape HTML special characters for safe injection into innerHTML. */
function _escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

/**
 * Build a simple before/after HTML diff view for the showDialog body.
 * Shows old source with a red tint and new source with a green tint.
 */
function _buildDiffHtml(oldSource: string, newSource: string): string {
  const preStyle =
    'font-family: monospace; font-size: 12px; white-space: pre-wrap; ' +
    'padding: 8px; border-radius: 4px; margin: 4px 0; max-height: 220px; ' +
    'overflow: auto; word-break: break-all;';
  const labelStyle = 'font-size: 11px; font-weight: 600; color: #666; margin-top: 8px;';
  return (
    `<div style="${labelStyle}">BEFORE</div>` +
    `<div style="${preStyle} background: #2d1a1a; color: #f8c8c8;">${_escapeHtml(oldSource)}</div>` +
    `<div style="${labelStyle}">AFTER</div>` +
    `<div style="${preStyle} background: #1a2d1a; color: #c8f8c8;">${_escapeHtml(newSource)}</div>`
  );
}

async function _handleCellReplace(
  data: Record<string, any>,
  tracker: INotebookTracker,
): Promise<void> {
  const notebookPanel = tracker.currentWidget;
  if (!notebookPanel) {
    console.warn('[jiuwenswarm] cell_replace: no active notebook');
    return;
  }
  const notebook = notebookPanel.content;
  const oldSource: string = (data.old_source ?? '').trim();
  const newSource: string = data.new_source ?? '';

  // Find the cell whose source content matches old_source
  let targetIndex = -1;
  const cellCount = notebook.model?.cells.length ?? 0;
  for (let i = 0; i < cellCount; i++) {
    const src = notebook.model!.cells.get(i).sharedModel.getSource().trim();
    if (src === oldSource) {
      targetIndex = i;
      break;
    }
  }

  if (targetIndex === -1) {
    console.warn('[jiuwenswarm] cell_replace: no cell matched old_source');
    return;
  }

  // Show before/after diff in a dialog and ask the user to confirm
  const diffWidget = new Widget();
  diffWidget.node.innerHTML = _buildDiffHtml(data.old_source ?? '', newSource);
  diffWidget.node.style.minWidth = '520px';

  const result = await showDialog({
    title: 'Apply cell rewrite?',
    body: diffWidget,
    buttons: [Dialog.cancelButton(), Dialog.okButton({ label: 'Apply' })],
  });

  if (result.button.accept) {
    notebook.model!.cells.get(targetIndex).sharedModel.setSource(newSource);
  }
}

// ---------------------------------------------------------------------------
// Plugin definition
// ---------------------------------------------------------------------------

const extension: JupyterFrontEndPlugin<void> = {
  id: PLUGIN_ID,
  description: 'JiuwenSwarm multi-agent AI for JupyterLab',
  autoStart: true,
  requires: [INotebookTracker],
  optional: [ICommandPalette, ILayoutRestorer, IStatusBar],

  activate: async (
    app: JupyterFrontEnd,
    tracker: INotebookTracker,
    palette: ICommandPalette | null,
    restorer: ILayoutRestorer | null,
    statusBar: IStatusBar | null,
  ) => {
    console.log('[jiuwenswarm] JupyterLab extension activating');

    // ── Core services ───────────────────────────────────────────────────────
    const client = new KernelCommClient('jiuwenswarm');
    const sessionMgr = new SessionManager(client);
    const swarmMgr = new SwarmStateManager(client);
    const contextCollector = new NotebookContextCollector(tracker);

    // Track which panels already have a kernelChanged listener to avoid stacking.
    const _wiredPanelIds = new Set<string>();

    /** Connect to a kernel and register it with the session manager. Idempotent. */
    async function _wireKernel(panel: any): Promise<void> {
      const kernel = panel.sessionContext?.session?.kernel;
      if (!kernel) return;

      const kernelId: string = kernel.id;
      const label: string =
        panel.title?.label || panel.sessionContext?.name || kernelId;

      // Register comm targets on this kernel (safe to call multiple times).
      kernel.registerCommTarget('jiuwenswarm_cell_insert', (comm: any) => {
        comm.onMsg = async (message: any) => {
          const data = message.content.data as Record<string, any>;
          await _handleCellInsert(data, tracker);
        };
      });
      kernel.registerCommTarget('jiuwenswarm_cell_replace', (comm: any) => {
        comm.onMsg = async (message: any) => {
          const data = message.content.data as Record<string, any>;
          await _handleCellReplace(data, tracker);
        };
      });

      // Open comm (idempotent: connectKernel guards with _comms.has(id)).
      try {
        await client.connectKernel(kernelId, kernel);
        sessionMgr.registerKernel({ id: kernelId, label });
        console.log('[jiuwenswarm] comm connected to kernel', kernelId, label);
      } catch (err) {
        console.warn('[jiuwenswarm] failed to connect comm', err);
        return;
      }

      // Switch active kernel and refresh session list from this kernel.
      client.setActiveKernel(kernelId);
      sessionMgr.setActiveKernel(kernelId);
      sessionMgr.refresh();
    }

    // currentChanged: fires when the user switches notebook tabs.
    tracker.currentChanged.connect(async (_, panel) => {
      if (!panel) return;

      const kernel = panel.sessionContext?.session?.kernel;
      if (kernel) {
        if (client.isKernelConnected(kernel.id)) {
          // Already connected — just switch the active routing target.
          client.setActiveKernel(kernel.id);
          sessionMgr.setActiveKernel(kernel.id);
        } else {
          await _wireKernel(panel);
        }
      }

      // Attach a kernelChanged listener once per panel to handle restarts.
      if (!_wiredPanelIds.has(panel.id)) {
        _wiredPanelIds.add(panel.id);
        panel.sessionContext.kernelChanged.connect(async () => {
          await _wireKernel(panel);
        });
      }
    });

    // ── Chat panel ──────────────────────────────────────────────────────────
    const chatPanel = new ChatPanel(client, sessionMgr);
    chatPanel.title.icon = jiuwenIcon;

    const chatTracker = new WidgetTracker<ChatPanel>({ namespace: 'jiuwenswarm-chat' });
    app.shell.add(chatPanel, 'left', { rank: 500 });
    await chatTracker.add(chatPanel);

    // ── Session list panel ───────────────────────────────────────────────────
    const sessionListPanel = new SessionListPanel(sessionMgr);
    const sessionListTracker = new WidgetTracker<SessionListPanel>({
      namespace: 'jiuwenswarm-sessions',
    });
    app.shell.add(sessionListPanel, 'left', { rank: 501 });
    await sessionListTracker.add(sessionListPanel);

    // ── Swarm map panel ─────────────────────────────────────────────────────
    let swarmMapWidget: MainAreaWidget<SwarmMapPanel> | null = null;

    function openSwarmMap() {
      if (!swarmMapWidget || swarmMapWidget.isDisposed) {
        const content = new SwarmMapPanel(client, swarmMgr);
        swarmMapWidget = new MainAreaWidget({ content });
        swarmMapWidget.title.label = 'Swarm Map';
        swarmMapWidget.title.closable = true;
      }
      if (!swarmMapWidget.isAttached) {
        app.shell.add(swarmMapWidget, 'main', { mode: 'split-right' });
      }
      app.shell.activateById(swarmMapWidget.id);
    }

    // ── Status bar ──────────────────────────────────────────────────────────
    if (statusBar) {
      const indicator = new StatusIndicator(client, swarmMgr, sessionMgr);
      statusBar.registerStatusItem(PLUGIN_ID, {
        item: indicator,
        align: 'right',
        rank: 100,
      });
    }

    // ── Kernel disconnect on notebook close ──────────────────────────────────
    // JupyterLab 4 has no tracker.widgetRemoved; detect closure via the panel's
    // session context `statusChanged` (becoming 'closed') or currentChanged → null.
    function _onPanelClosed(panel: any): void {
      const kernel = panel?.sessionContext?.session?.kernel;
      if (kernel) {
        client.disconnectKernel(kernel.id);
        sessionMgr.unregisterKernel(kernel.id);
        _wiredPanelIds.delete(panel.id);
        console.log('[jiuwenswarm] disconnected kernel on notebook close', kernel.id);
      }
    }

    tracker.currentChanged.connect((_, panel) => {
      // `null` means the last notebook was closed — sweep any remaining comms.
      if (!panel) {
        for (const id of client.connectedKernelIds) {
          client.disconnectKernel(id);
          sessionMgr.unregisterKernel(id);
          _wiredPanelIds.delete(id);
        }
        return;
      }
      if (panel.sessionContext) {
        panel.sessionContext.statusChanged.connect((ctx: any, status: any) => {
          if (status === 'closed') _onPanelClosed(panel);
        });
      }
    });

    // ── Commands ─────────────────────────────────────────────────────────────
    const commands = {
      openChat: `${PLUGIN_ID}:open-chat`,
      openSwarmMap: `${PLUGIN_ID}:open-swarm-map`,
      sendSelection: `${PLUGIN_ID}:send-selection`,
      newSession: `${PLUGIN_ID}:new-session`,
      openSessions: `${PLUGIN_ID}:open-sessions`,
    };

    app.commands.addCommand(commands.openChat, {
      label: 'JiuwenSwarm: Open Chat',
      execute: () => {
        app.shell.activateById(ChatPanel.ID);
      },
    });

    app.commands.addCommand(commands.openSwarmMap, {
      label: 'JiuwenSwarm: Open Swarm Map',
      execute: openSwarmMap,
    });

    app.commands.addCommand(commands.newSession, {
      label: 'JiuwenSwarm: New Session',
      execute: () => {
        sessionMgr.createSession();
        app.shell.activateById(ChatPanel.ID);
      },
    });

    app.commands.addCommand(commands.openSessions, {
      label: 'JiuwenSwarm: Open Session List',
      execute: () => {
        app.shell.activateById(SessionListPanel.ID);
      },
    });

    if (palette) {
      const category = 'JiuwenSwarm';
      palette.addItem({ command: commands.openChat, category });
      palette.addItem({ command: commands.openSwarmMap, category });
      palette.addItem({ command: commands.newSession, category });
      palette.addItem({ command: commands.openSessions, category });
    }

    // ── Keyboard shortcuts ────────────────────────────────────────────────────
    app.commands.addKeyBinding({
      command: commands.openChat,
      keys: ['Accel Shift J'],
      selector: 'body',
    });

    app.commands.addKeyBinding({
      command: commands.newSession,
      keys: ['Accel Shift N'],
      selector: 'body',
    });

    // ── Layout restorer ───────────────────────────────────────────────────────
    if (restorer) {
      restorer.add(chatPanel, 'jiuwenswarm-chat');
      restorer.add(sessionListPanel, 'jiuwenswarm-sessions');
    }

    console.log('[jiuwenswarm] JupyterLab extension activated');
  },
};

export default extension;
