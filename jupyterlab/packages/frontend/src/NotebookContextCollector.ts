/**
 * Collects notebook context from the active notebook for the agent.
 *
 * Analagous to ContextCollector.ts in the IDE plugin (which reads the active
 * editor file).  Here we collect:
 *   - The active notebook path
 *   - The most recently executed cells (inputs + outputs, truncated)
 *
 * This TypeScript side provides a lightweight summary; deeper variable
 * inspection is handled by context.py in the Python kernel.
 */

import { INotebookTracker, NotebookPanel } from '@jupyterlab/notebook';

export interface NotebookContext {
  notebookPath: string | null;
  recentCells: CellSummary[];
}

export interface CellSummary {
  cellType: 'code' | 'markdown';
  source: string;
  outputPreview?: string;
}

const MAX_CELLS = 5;
const MAX_CHARS = 600;

export class NotebookContextCollector {
  constructor(private readonly _tracker: INotebookTracker) {}

  collect(): NotebookContext {
    const panel: NotebookPanel | null = this._tracker.currentWidget;

    if (!panel) {
      return { notebookPath: null, recentCells: [] };
    }

    const notebookPath = panel.context.path;
    const cells = panel.content.model?.cells;
    if (!cells) {
      return { notebookPath, recentCells: [] };
    }

    const summaries: CellSummary[] = [];
    const count = cells.length;

    for (let i = Math.max(0, count - MAX_CELLS); i < count; i++) {
      const cell = cells.get(i);
      if (!cell) continue;

      const type = cell.type === 'code' ? 'code' : 'markdown';
      let source = cell.sharedModel.getSource();
      if (source.length > MAX_CHARS) {
        source = source.slice(0, MAX_CHARS) + '\n…';
      }

      let outputPreview: string | undefined;
      if (type === 'code' && 'outputs' in cell) {
        // @ts-ignore – outputs exists on CodeCellModel
        const outputs = (cell as any).outputs?.toJSON?.() ?? [];
        const text = outputs
          .map((o: any) => {
            if (o.output_type === 'stream') return (o.text ?? []).join('');
            if (o.output_type === 'execute_result' || o.output_type === 'display_data') {
              return (o.data?.['text/plain'] ?? '');
            }
            return '';
          })
          .filter(Boolean)
          .join('\n');
        if (text) {
          outputPreview = text.length > MAX_CHARS ? text.slice(0, MAX_CHARS) + '…' : text;
        }
      }

      summaries.push({ cellType: type, source, outputPreview });
    }

    return { notebookPath, recentCells: summaries };
  }

  formatAsString(): string {
    const ctx = this.collect();
    if (!ctx.notebookPath && ctx.recentCells.length === 0) return '';

    const parts: string[] = [];
    if (ctx.notebookPath) {
      parts.push(`Active notebook: ${ctx.notebookPath}`);
    }
    for (const cell of ctx.recentCells) {
      const header = cell.cellType === 'code' ? '```python' : '```markdown';
      parts.push(`${header}\n${cell.source}\n\`\`\``);
      if (cell.outputPreview) {
        parts.push(`Output:\n${cell.outputPreview}`);
      }
    }
    return parts.join('\n\n');
  }
}
