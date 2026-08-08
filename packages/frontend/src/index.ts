/**
 * JiuwenSwarm JupyterLab frontend extension.
 *
 * Registers:
 *   - Sidebar chat panel (ChatPanel)
 *   - Sidebar session list panel (SessionListPanel)
 *   - Sidebar skills browser panel (SkillsPanel)
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
import { ICommandPalette, MainAreaWidget, WidgetTracker } from '@jupyterlab/apputils';
import { INotebookTracker, NotebookActions } from '@jupyterlab/notebook';
import { IStatusBar } from '@jupyterlab/statusbar';

import { KernelCommClient } from './WsClient';
import { SessionManager } from './SessionManager';
import { SwarmStateManager } from './SwarmStateManager';
import { ChatPanel } from './ChatPanel';
import { SwarmMapPanel } from './SwarmMapPanel';
import { StatusIndicator } from './StatusIndicator';
import { NotebookContextCollector } from './NotebookContextCollector';
import { SessionListPanel } from './SessionListPanel';
import { SkillsPanel } from './SkillsPanel';

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

  // Optionally execute the inserted cell immediately
  if (data.execute) {
    await NotebookActions.run(notebook, notebookPanel.sessionContext);
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

    // Connect comm when the first notebook kernel becomes available
    tracker.currentChanged.connect(async (_, panel) => {
      if (panel?.sessionContext?.session?.kernel) {
        const kernel = panel.sessionContext.session.kernel;

        // Register the cell-insert comm target on every kernel
        kernel.registerCommTarget('jiuwenswarm_cell_insert', (comm, msg) => {
          comm.onMsg = async (message) => {
            const data = message.content.data as Record<string, any>;
            await _handleCellInsert(data, tracker);
          };
        });

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

    // ── Session list panel ───────────────────────────────────────────────────
    const sessionListPanel = new SessionListPanel(sessionMgr);
    const sessionListTracker = new WidgetTracker<SessionListPanel>({
      namespace: 'jiuwenswarm-sessions',
    });
    app.shell.add(sessionListPanel, 'left', { rank: 501 });
    await sessionListTracker.add(sessionListPanel);

    // ── Skills browser panel ─────────────────────────────────────────────────
    const skillsPanel = new SkillsPanel(client);
    const skillsTracker = new WidgetTracker<SkillsPanel>({
      namespace: 'jiuwenswarm-skills',
    });
    app.shell.add(skillsPanel, 'left', { rank: 502 });
    await skillsTracker.add(skillsPanel);

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
      openSessions: `${PLUGIN_ID}:open-sessions`,
      openSkills: `${PLUGIN_ID}:open-skills`,
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

    app.commands.addCommand(commands.openSkills, {
      label: 'JiuwenSwarm: Open Skills Browser',
      execute: () => {
        app.shell.activateById(SkillsPanel.ID);
      },
    });

    if (palette) {
      const category = 'JiuwenSwarm';
      palette.addItem({ command: commands.openChat, category });
      palette.addItem({ command: commands.openSwarmMap, category });
      palette.addItem({ command: commands.newSession, category });
      palette.addItem({ command: commands.openSessions, category });
      palette.addItem({ command: commands.openSkills, category });
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
      restorer.add(skillsPanel, 'jiuwenswarm-skills');
    }

    console.log('[jiuwenswarm] JupyterLab extension activated');
  },
};

export default extension;
