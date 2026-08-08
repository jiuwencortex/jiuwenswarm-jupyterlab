/**
 * SkillsPanel — sidebar panel for browsing available JiuwenSwarm skills.
 *
 * Requests the skill list from the Python kernel on connect and whenever the
 * user presses the refresh button.  Each skill is shown with its name,
 * description, and source file.
 */

import { Widget } from '@lumino/widgets';
import { KernelCommClient } from './WsClient';
import { SkillInfo } from './protocol';

export class SkillsPanel extends Widget {
  static readonly ID = 'jiuwenswarm-skills-panel';
  static readonly TITLE = 'Skills';

  private _client: KernelCommClient;
  private _list: HTMLElement;
  private _skills: SkillInfo[] = [];

  constructor(client: KernelCommClient) {
    super();
    this.id = SkillsPanel.ID;
    this.title.label = SkillsPanel.TITLE;
    this.title.closable = true;
    this.addClass('jiuwenswarm-skills-panel');

    this._client = client;
    this.node.style.cssText =
      'height:100%; overflow-y:auto; padding:8px; font-family:var(--jp-ui-font-family)';

    // ── Header row ──────────────────────────────────────────────────────────
    const header = document.createElement('div');
    header.style.cssText =
      'display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;';

    const titleEl = document.createElement('span');
    titleEl.style.cssText =
      'font-size:12px; font-weight:600; color:var(--jp-ui-font-color0);';
    titleEl.textContent = 'Available Skills';

    const refreshBtn = document.createElement('button');
    refreshBtn.textContent = '↻';
    refreshBtn.title = 'Refresh skill list';
    refreshBtn.style.cssText =
      'font-size:14px; padding:1px 6px; cursor:pointer; border-radius:4px;' +
      ' border:1px solid var(--jp-border-color1); background:transparent;' +
      ' color:var(--jp-ui-font-color1);';
    refreshBtn.addEventListener('click', () => this._requestSkills());

    header.appendChild(titleEl);
    header.appendChild(refreshBtn);
    this.node.appendChild(header);

    // ── Skills list ─────────────────────────────────────────────────────────
    this._list = document.createElement('div');
    this.node.appendChild(this._list);

    // Receive skill list from kernel
    client.onEvent(event => {
      if (event.type === 'skills') {
        this._skills = event.skills;
        this._render();
      }
    });

    // Request on first connection
    client.onEvent(event => {
      if (event.type === 'connected') {
        this._requestSkills();
      }
    });

    this._render();
  }

  private _requestSkills(): void {
    this._client.send({ type: 'get_skills' });
  }

  private _render(): void {
    this._list.innerHTML = '';

    if (this._skills.length === 0) {
      const empty = document.createElement('div');
      empty.style.cssText =
        'font-size:11px; color:var(--jp-ui-font-color2); padding:8px 0;';
      empty.textContent = 'No skills loaded yet. Connect to a kernel first, or click ↻ to refresh.';
      this._list.appendChild(empty);
      return;
    }

    for (const skill of this._skills) {
      this._list.appendChild(this._makeItem(skill));
    }
  }

  private _makeItem(skill: SkillInfo): HTMLElement {
    const item = document.createElement('div');
    item.style.cssText =
      'padding:8px 10px; margin-bottom:6px; border-radius:4px;' +
      ' border:1px solid var(--jp-border-color2); background:var(--jp-layout-color1);';

    const nameEl = document.createElement('div');
    nameEl.style.cssText =
      'font-size:12px; font-weight:600; color:var(--jp-ui-font-color0); margin-bottom:3px;';
    nameEl.textContent = skill.name;

    const descEl = document.createElement('div');
    descEl.style.cssText =
      'font-size:11px; color:var(--jp-ui-font-color1); line-height:1.45;';
    descEl.textContent = skill.description || '(no description)';

    item.appendChild(nameEl);
    item.appendChild(descEl);

    if (skill.source) {
      const sourceEl = document.createElement('div');
      sourceEl.style.cssText =
        'font-size:10px; color:var(--jp-ui-font-color2); margin-top:4px; font-style:italic;';
      sourceEl.textContent = skill.source;
      item.appendChild(sourceEl);
    }

    return item;
  }
}
