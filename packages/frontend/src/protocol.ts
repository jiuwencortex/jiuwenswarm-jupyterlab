/**
 * Protocol types shared between the TypeScript frontend and the Python kernel.
 *
 * Messages flow over two channels:
 *   - Kernel → frontend:  comm messages from Python JupyterSwarm
 *   - Frontend → kernel:  comm messages routed to JupyterSwarm.run()
 *
 * The underlying streaming event schema (chat.delta, chat.final, tool.call,
 * tool.result, team.*) is the same as in the IDE plugin; only the transport
 * layer changes (Jupyter comm instead of WebSocket).
 */

// ── Outbound (frontend → kernel) ─────────────────────────────────────────────

export interface SendMessagePayload {
  type: 'send_message';
  query: string;
  mode: AgentMode;
  session_id: string;
  inject_context: boolean;
}

export interface CancelPayload {
  type: 'cancel';
  session_id: string;
}

export interface GetSessionsPayload {
  type: 'get_sessions';
}

export interface GetSkillsPayload {
  type: 'get_skills';
}

export type KernelBoundMessage =
  | SendMessagePayload
  | CancelPayload
  | GetSessionsPayload
  | GetSkillsPayload;

// ── Inbound (kernel → frontend) ───────────────────────────────────────────────

export interface ConnectedEvent {
  type: 'connected';
  server_version: string;
  available_modes: AgentMode[];
}

export interface ChatDeltaEvent {
  type: 'chat.delta';
  session_id: string;
  delta: string;
  turn_id: string;
}

export interface ChatFinalEvent {
  type: 'chat.final';
  session_id: string;
  text: string;
  turn_id: string;
  usage?: {
    input_tokens: number;
    output_tokens: number;
    cost_usd?: number;
  };
}

export interface ChatErrorEvent {
  type: 'chat.error';
  session_id: string;
  error: string;
  turn_id: string;
}

export interface ToolCallEvent {
  type: 'tool.call';
  session_id: string;
  turn_id: string;
  tool_id: string;
  name: string;
  args: Record<string, unknown>;
}

export interface ToolResultEvent {
  type: 'tool.result';
  session_id: string;
  turn_id: string;
  tool_id: string;
  name: string;
  result: string;
  is_error: boolean;
}

export interface SwarmSnapshotEvent {
  type: 'swarm_snapshot';
  snapshot: SwarmSnapshot;
}

export interface SessionListEvent {
  type: 'sessions';
  sessions: SessionInfo[];
}

export interface SkillListEvent {
  type: 'skills';
  skills: SkillInfo[];
}

export type KernelEvent =
  | ConnectedEvent
  | ChatDeltaEvent
  | ChatFinalEvent
  | ChatErrorEvent
  | ToolCallEvent
  | ToolResultEvent
  | SwarmSnapshotEvent
  | SessionListEvent
  | SkillListEvent;

// ── Domain types ─────────────────────────────────────────────────────────────

export type AgentMode = 'agent' | 'code' | 'team' | 'code.team';

export interface SessionInfo {
  session_id: string;
  title: string;
  created_at: string;
  mode: AgentMode;
  kernel_id?: string; // optional — absent means active kernel at receive time
}

/** Frontend-only: tracks a connected kernel with a human-readable label. */
export interface KernelInfo {
  id: string;    // kernel.id from JupyterLab
  label: string; // notebook filename, e.g. "analysis.ipynb"
}

export interface SkillInfo {
  name: string;
  description: string;
  source: string;
}

export interface SwarmSnapshot {
  lanes: SwarmLane[];
  tasks?: SwarmTask[];
}

export interface SwarmLane {
  memberName: string;
  role: string;
  status: 'ACTIVE' | 'IDLE' | 'SHUTDOWN';
  currentTask?: string;
  startedAt?: number;
}

export interface SwarmTask {
  id: string;
  title: string;
  assignee?: string;
  status: 'pending' | 'in_progress' | 'done' | 'failed';
}
