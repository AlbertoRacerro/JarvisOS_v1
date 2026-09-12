const SAFE_BROWSER_METHODS = new Set(['GET', 'HEAD', 'OPTIONS']);
const READ_ONLY_POST_PATHS = new Set(['/ai/context/packs/preview']);

export function isMutatingSameOriginRequest(method, path) {
  if (typeof method !== 'string' || typeof path !== 'string') return true;
  const normalizedMethod = method.toUpperCase();
  if (SAFE_BROWSER_METHODS.has(normalizedMethod)) return false;
  if (normalizedMethod === 'POST' && READ_ONLY_POST_PATHS.has(path)) return false;
  return true;
}
