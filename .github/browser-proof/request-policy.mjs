const SAFE_BROWSER_METHODS = new Set(['GET', 'HEAD', 'OPTIONS']);
const READ_ONLY_SAME_ORIGIN_POST_PATHS = new Set(['/ai/context/packs/preview']);

export function isMutatingSameOriginRequest(method, path, readOnlySameOriginPostPaths = READ_ONLY_SAME_ORIGIN_POST_PATHS) {
  if (typeof method !== 'string' || typeof path !== 'string' || !(readOnlySameOriginPostPaths instanceof Set)) return true;
  const normalizedMethod = method.toUpperCase();
  if (SAFE_BROWSER_METHODS.has(normalizedMethod)) return false;
  if (normalizedMethod === 'POST' && readOnlySameOriginPostPaths.has(path)) return false;
  return true;
}
