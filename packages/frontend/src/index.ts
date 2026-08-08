/**
 * JiuwenSwarm JupyterLab frontend extension.
 *
 * Registers:
 *   - Sidebar chat panel (ChatPanel)
 *   - Swarm map panel (SwarmMapPanel)
 *   - Status bar indicator (StatusIndicator)
 *   - Command palette entries
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
import { ICommandPalette, MainAreaWidget, WidgetTracker } from '@jupyterlab/apputils';
import { INotebookTracker } from '@jupyterlab/notebook';
import { IStatusBar } from '@jupyterlab/statusbar';

import { KernelCommClient } from './WsClient';
import { SessionManager } from './SessionManager';
import { SwarmStateManager } from './SwarmStateManager';
import { ChatPanel } from './ChatPanel';
import { SwarmMapPanel } from './SwarmMapPanel';
import { StatusIndicator } from './StatusIndicator';
import { NotebookContextCollector } from './NotebookContextCollector';

const PLUGIN_ID = '@jiuwenswarm/jupyterlab:plugin';

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

    // Connect comm when the first notebook kernel becomes available
    tracker.currentChanged.connect(async (_, panel) => {
      if (panel?.sessionContext?.session?.kernel) {
        const kernel = panel.sessionContext.session.kernel;
        if (!client.isConnected) {
          try {
            await client.connect(kernel);
            sessionMgr.refresh();
            console.log('[jiuwenswarm] comm connected to kernel');
          } catch (err) {
            console.warn('[jiuwenswarm] failed to connect comm', err);
          }
        }
      }
    });

    // ── Chat panel ──────────────────────────────────────────────────────────
    const chatPanel = new ChatPanel(client, sessionMgr);
    chatPanel.title.iconClass = 'jiuwenswarm-icon jp-SideBar-tabBar-icon';

    const chatTracker = new WidgetTracker<ChatPanel>({ namespace: 'jiuwenswarm-chat' });
    app.shell.add(chatPanel, 'left', { rank: 500 });
    await chatTracker.add(chatPanel);

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
      const indicator = new StatusIndicator(client, swarmMgr);
      statusBar.registerStatusItem(PLUGIN_ID, {
        item: indicator,
        align: 'right',
        rank: 100,
      });
    }

    // ── Commands ─────────────────────────────────────────────────────────────
    const commands = {
      openChat: `${PLUGIN_ID}:open-chat`,
      openSwarmMap: `${PLUGIN_ID}:open-swarm-map`,
      sendSelection: `${PLUGIN_ID}:send-selection`,
      newSession: `${PLUGIN_ID}:new-session`,
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

    if (palette) {
      const category = 'JiuwenSwarm';
      palette.addItem({ command: commands.openChat, category });
      palette.addItem({ command: commands.openSwarmMap, category });
      palette.addItem({ command: commands.newSession, category });
    }

    // Restore layout
    if (restorer) {
      restorer.add(chatPanel, 'jiuwenswarm-chat');
    }

    console.log('[jiuwenswarm] JupyterLab extension activated');
  },
};

export default extension;
