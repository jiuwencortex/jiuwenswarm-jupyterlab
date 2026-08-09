/**
 * SessionListPanel — sidebar panel for browsing and switching sessions.
 *
 * Shows all active JiuwenSwarm sessions, highlights the current one, and
 * allows the user to switch sessions by clicking.  A "+ New" button creates
 * a fresh session.
 *
 * Multi-kernel support: when more than one notebook kernel is connected the
 * list is rendered in groups, each prefixed by a kernel/notebook header.
 * Single-kernel stays flat (no visual regression).
 */

import { Widget } from '@lumino/widgets';
import { SessionManager } from './SessionManager';
import { SessionInfo } from './protocol';

export class SessionListPanel extends Widget {
  static readonly ID = 'jiuwenswarm-session-list';
  static readonly TITLE = 'Sessions';

  private _sessionMgr: SessionManager;
  private _list: HTMLElement;
  private _filter: string = '';

  constructor(sessionMgr: SessionManager) {
    super();
    this.id = SessionListPanel.ID;
    this.title.label = SessionListPanel.TITLE;
    this.title.closable = true;
    this.addClass('jiuwenswarm-session-list-panel');

    this._sessionMgr = sessionMgr;
    this.node.style.cssText =
      'height:100%; overflow-y:auto; padding:8px; font-family:var(--jp-ui-font-family)';

    // ── Header row ──────────────────────────────────────────────────────────
    const header = document.createElement('div');
    header.style.cssText =
      'display:flex; align-items:center; justify-content:space-between; margin-bottom:6px;';

    const titleEl = document.createElement('span');
    titleEl.style.cssText =
      'font-size:12px; font-weight:600; color:var(--jp-ui-font-color0);';
    titleEl.textContent = 'Sessions';

    const newBtn = document.createElement('button');
    newBtn.textContent = '+ New';
    newBtn.title = 'Start a new session';
    newBtn.style.cssText =
      'font-size:11px; padding:2px 8px; cursor:pointer; border-radius:4px;' +
      ' border:1px solid var(--jp-border-color1); background:transparent;' +
      ' color:var(--jp-ui-font-color1);';
    newBtn.addEventListener('click', () => sessionMgr.createSession());

    header.appendChild(titleEl);
    header.appendChild(newBtn);
    this.node.appendChild(header);

    // ── Filter input ─────────────────────────────────────────────────────────
    const filterInput = document.createElement('input');
    filterInput.type = 'text';
    filterInput.placeholder = 'Filter sessions…';
    filterInput.style.cssText =
      'width:100%; box-sizing:border-box; font-size:11px; padding:3px 6px;' +
      ' margin-bottom:6px; border-radius:4px;' +
      ' border:1px solid var(--jp-border-color1);' +
      ' background:var(--jp-layout-color1); color:var(--jp-ui-font-color1); outline:none;';
    filterInput.addEventListener('input', () => {
      this._filter = filterInput.value.toLowerCase();
      this._render();
    });
    this.node.appendChild(filterInput);

    // ── Session list ────────────────────────────────────────────────────────
    this._list = document.createElement('div');
    this.node.appendChild(this._list);

    // Re-render on any session change
    sessionMgr.onChange(() => this._render());
    this._render();
  }

  private _matches(session: SessionInfo): boolean {
    if (!this._filter) return true;
    const title = (session.title || session.session_id).toLowerCase();
    return title.includes(this._filter);
  }

  private _render(): void {
    this._list.innerHTML = '';
    const kernels = this._sessionMgr.allKernels();

    if (kernels.length > 1) {
      // ── Grouped view: one section per kernel ───────────────────────────
      let totalVisible = 0;
      for (const kernel of kernels) {
        const sessions = this._sessionMgr.getKernelSessions(kernel.id)
          .filter(s => this._matches(s));
        totalVisible += sessions.length;
        this._list.appendChild(this._makeKernelHeader(kernel.label));
        if (sessions.length === 0) {
          this._list.appendChild(this._makeEmptyNote());
        } else {
          const activeId = this._sessionMgr.activeSessionId;
          for (const session of sessions) {
            this._list.appendChild(
              this._makeItem(session, session.session_id === activeId)
            );
          }
        }
      }
      if (totalVisible === 0) {
        this._list.appendChild(this._makeEmptyNote());
      }
      return;
    }

    // ── Flat view: single kernel or no kernels yet ─────────────────────
    const sessions = this._sessionMgr.sessions.filter(s => this._matches(s));
    const activeId = this._sessionMgr.activeSessionId;

    if (sessions.length === 0) {
      this._list.appendChild(this._makeEmptyNote());
      return;
    }

    for (const session of sessions) {
      this._list.appendChild(
        this._makeItem(session, session.session_id === activeId)
      );
    }
  }

  private _makeKernelHeader(label: string): HTMLElement {
    const el = document.createElement('div');
    el.style.cssText =
      'font-size:10px; font-weight:600; color:var(--jp-ui-font-color2);' +
      ' text-transform:uppercase; letter-spacing:0.05em;' +
      ' padding:6px 0 2px; margin-top:4px; border-top:1px solid var(--jp-border-color2);';
    el.textContent = label;
    return el;
  }

  private _makeEmptyNote(): HTMLElement {
    const empty = document.createElement('div');
    empty.style.cssText =
      'font-size:11px; color:var(--jp-ui-font-color2); padding:8px 0;';
    empty.textContent = 'No sessions yet. Send a message to start one.';
    return empty;
  }

  private _makeItem(session: SessionInfo, isActive: boolean): HTMLElement {
    const item = document.createElement('div');
    item.style.cssText = [
      'padding:8px 10px',
      'margin-bottom:4px',
      'border-radius:4px',
      'cursor:pointer',
      'border:1px solid ' +
        (isActive ? 'var(--jp-brand-color1)' : 'var(--jp-border-color2)'),
      'background:' + (isActive ? 'var(--jp-brand-color3)' : 'transparent'),
      'transition:background 0.1s',
    ].join(';');

    // Top row: title + mode badge
    const topRow = document.createElement('div');
    topRow.style.cssText =
      'display:flex; align-items:center; justify-content:space-between;';

    const titleEl = document.createElement('span');
    titleEl.style.cssText =
      'font-size:12px; color:var(--jp-ui-font-color0);' +
      ' white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:140px;';
    titleEl.textContent = session.title || session.session_id;

    const modeEl = document.createElement('span');
    modeEl.style.cssText =
      'font-size:10px; color:var(--jp-ui-font-color2); flex-shrink:0; margin-left:4px;';
    modeEl.textContent = session.mode;

    topRow.appendChild(titleEl);
    topRow.appendChild(modeEl);
    item.appendChild(topRow);

    // Date row
    if (session.created_at) {
      const dateEl = document.createElement('div');
      dateEl.style.cssText =
        'font-size:10px; color:var(--jp-ui-font-color2); margin-top:2px;';
      try {
        const d = new Date(session.created_at);
        dateEl.textContent =
          d.toLocaleDateString() +
          ' ' +
          d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      } catch {
        dateEl.textContent = session.created_at;
      }
      item.appendChild(dateEl);
    }

    // Click to switch
    item.addEventListener('click', () => {
      this._sessionMgr.activeSessionId = session.session_id;
    });
    item.addEventListener('mouseenter', () => {
      if (session.session_id !== this._sessionMgr.activeSessionId) {
        item.style.background = 'var(--jp-layout-color2)';
      }
    });
    item.addEventListener('mouseleave', () => {
      if (session.session_id !== this._sessionMgr.activeSessionId) {
        item.style.background = 'transparent';
      }
    });

    return item;
  }
}
