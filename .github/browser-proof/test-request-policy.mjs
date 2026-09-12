import assert from 'node:assert/strict';
import { isMutatingSameOriginRequest } from './request-policy.mjs';

for (const method of ['GET', 'HEAD', 'OPTIONS']) {
  assert.equal(isMutatingSameOriginRequest(method, '/any/path'), false, `${method} must remain read-only`);
}
assert.equal(isMutatingSameOriginRequest('POST', '/ai/context/packs/preview'), false, 'context preview POST is read-only');
assert.equal(isMutatingSameOriginRequest('post', '/ai/context/packs/preview'), false, 'method classification is case-normalized');
assert.equal(isMutatingSameOriginRequest('POST', '/ai/context/packs/preview/extra'), true, 'read-only POST classification is exact-path only');
assert.equal(isMutatingSameOriginRequest('POST', '/api/write'), true, 'unclassified POST remains mutating');
assert.equal(isMutatingSameOriginRequest('PUT', '/ai/context/packs/preview'), true, 'only POST may use the read-only endpoint classification');
assert.equal(isMutatingSameOriginRequest('DELETE', '/ai/context/packs/preview'), true, 'destructive methods remain mutating');
assert.equal(isMutatingSameOriginRequest(null, '/ai/context/packs/preview'), true, 'malformed methods fail closed');
assert.equal(isMutatingSameOriginRequest('POST', null), true, 'malformed paths fail closed');
console.log('browser-proof request policy PASS');
