const SCENE_BINDING_VERSION = "bluecad_scene_binding_v0_1";
const SCENE_BINDING_ARTIFACT = "model.glb";
const SEMANTIC_KEY = /^bluecad-part-sha256-[0-9a-f]{64}$/;
const SHA256 = /^[0-9a-f]{64}$/;

export type ResolvedScenePart = Readonly<{
  semanticKey: string;
  partId: string;
  partKind: string | null;
}>;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function artifactDigest(manifest: Record<string, unknown>): string | null {
  const artifacts = manifest.artifacts;
  if (!isRecord(artifacts)) return null;
  const glb = artifacts[SCENE_BINDING_ARTIFACT];
  if (!isRecord(glb) || typeof glb.sha256 !== "string" || !SHA256.test(glb.sha256)) return null;
  return glb.sha256;
}

/**
 * Resolve one exporter-owned GLTF semantic key against the exact current manifest.
 *
 * This is deliberately fail-closed. Renderer order, display names, materials,
 * bounds and other inspection facts are never accepted as engineering identity.
 */
export function resolveScenePart(
  manifestValue: unknown,
  semanticKey: string | null,
  currentGlbSha256: string
): ResolvedScenePart | null {
  if (!semanticKey || !SEMANTIC_KEY.test(semanticKey) || !SHA256.test(currentGlbSha256)) return null;
  if (!isRecord(manifestValue)) return null;

  const binding = manifestValue.scene_binding;
  const parts = manifestValue.parts;
  if (!isRecord(binding) || !isRecord(parts)) return null;
  if (binding.version !== SCENE_BINDING_VERSION || binding.artifact !== SCENE_BINDING_ARTIFACT) return null;
  if (artifactDigest(manifestValue) !== currentGlbSha256) return null;

  const objects = binding.objects;
  if (!isRecord(objects)) return null;
  const target = objects[semanticKey];
  if (!isRecord(target) || Object.keys(target).length !== 1 || typeof target.part_id !== "string") return null;

  const part = parts[target.part_id];
  if (!isRecord(part)) return null;
  const partKind = typeof part.kind === "string" ? part.kind : null;
  return { semanticKey, partId: target.part_id, partKind };
}
