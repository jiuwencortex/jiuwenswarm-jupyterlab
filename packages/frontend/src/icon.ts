import { LabIcon } from '@jupyterlab/ui-components';

/**
 * JiuwenSwarm sidebar icon — a compact blue gradient mark derived from
 * packages/shared-webview/icon.svg.
 */
export const jiuwenIcon = new LabIcon({
  name: 'jiuwenswarm:icon',
  svgstr: `
  <svg viewBox="0 0 28 28" xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="none">
    <defs>
      <linearGradient id="jiuwen_g" x1="0" y1="0" x2="28" y2="28" gradientUnits="userSpaceOnUse">
        <stop stop-color="rgb(68,154,255)" offset="0.005"/>
        <stop stop-color="rgb(20,118,255)" offset="0.502"/>
        <stop stop-color="rgb(53,137,255)" offset="1"/>
      </linearGradient>
    </defs>
    <path fill="url(#jiuwen_g)"
      d="M6.8 5.2 3.2 10.7c-.5.7-.4 1.7.2 2.3l5.2 5.2a2 2 0 0 0 2.7 0l5.7-5.7a2 2 0 0 0 0-2.8L11.9 4.9a2 2 0 0 0-2.7 0l-.5.5 5.2 5.2a1.4 1.4 0 0 1 0 2l-1.6 1.6a1.4 1.4 0 0 1-2 0L7 9.1l-.2.2z"
    />
  </svg>`,
});
