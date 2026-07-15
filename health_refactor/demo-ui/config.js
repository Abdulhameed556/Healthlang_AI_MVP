/**
 * API base URLs for the demo UI.
 * Same origin — backend serves product + AI routes on one port.
 */
const origin = window.location.origin;
window.DEMO_CONFIG = {
  backendBaseUrl: `${origin}/api/v1`,
  aiBaseUrl: `${origin}/api/v1`,
  evalBaseUrl: `${origin}/ai/api/v1`,
};
