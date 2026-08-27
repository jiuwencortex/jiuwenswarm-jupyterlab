/**
 * Swarm state model — mirrors SwarmState.ts in the IDE plugin.
 * Maintained by SwarmStateManager, consumed by SwarmMapPanel.
 */

import { SwarmSnapshot, SwarmLane, SwarmTask } from './protocol';

export interface SwarmState {
  snapshot: SwarmSnapshot | null;
  lastUpdated: number;
}

export const EMPTY_STATE: SwarmState = {
  snapshot: null,
  lastUpdated: 0,
};

export function applySnapshot(current: SwarmState, snapshot: SwarmSnapshot): SwarmState {
  return {
    snapshot,
    lastUpdated: Date.now(),
  };
}

export function isTeamActive(state: SwarmState): boolean {
  if (!state.snapshot) return false;
  return state.snapshot.lanes.some(l => l.status === 'ACTIVE');
}

export function workerLanes(state: SwarmState): SwarmLane[] {
  if (!state.snapshot) return [];
  return state.snapshot.lanes.filter(l => !l.memberName.startsWith('Orchestrator'));
}

export function pendingTasks(state: SwarmState): SwarmTask[] {
  if (!state.snapshot?.tasks) return [];
  return state.snapshot.tasks.filter(t => t.status === 'pending' || t.status === 'in_progress');
}
