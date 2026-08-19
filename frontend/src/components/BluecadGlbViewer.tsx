import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

const BLUECAD_SEMANTIC_KEY = /^bluecad-part-sha256-[0-9a-f]{64}$/;

export type GeometryInspectionMesh = Readonly<{
  sessionKey: string;
  meshKey: string;
  semanticKey: string | null;
  displayName: string;
  materialNames: readonly string[];
  triangleCount: number | null;
  worldBounds: Readonly<{
    min: readonly [number, number, number];
    max: readonly [number, number, number];
  }> | null;
}>;

export type GeometryInspectionSnapshot = Readonly<{
  sessionKey: string | null;
  status: "idle" | "loading" | "ready" | "error";
  meshes: readonly GeometryInspectionMesh[];
  selected: GeometryInspectionMesh | null;
}>;

export type GeometryInspectionCommand = Readonly<{
  sessionKey: string;
  meshKey: string | null;
  nonce: number;
}>;

type BluecadGlbViewerProps = {
  artifactUrl: string;
  inspectionCommand?: GeometryInspectionCommand | null;
  onInspectionChange?(snapshot: GeometryInspectionSnapshot): void;
};

type SessionSelection = (meshKey: string | null) => void;

function disposeMaterial(material: THREE.Material) {
  for (const value of Object.values(material)) {
    if (value instanceof THREE.Texture) value.dispose();
  }
  material.dispose();
}

function disposeOwnedScene(root: THREE.Object3D) {
  root.traverse((object) => {
    if (!(object instanceof THREE.Mesh)) return;
    object.geometry?.dispose();
    const materials = Array.isArray(object.material) ? object.material : [object.material];
    for (const material of materials) disposeMaterial(material);
  });
}

function triangleCount(geometry: THREE.BufferGeometry): number | null {
  const count = geometry.index?.count ?? geometry.getAttribute("position")?.count;
  return typeof count === "number" && Number.isFinite(count) ? Math.floor(count / 3) : null;
}

function worldBounds(mesh: THREE.Mesh): GeometryInspectionMesh["worldBounds"] {
  const geometry = mesh.geometry;
  if (!geometry.boundingBox) geometry.computeBoundingBox();
  if (!geometry.boundingBox) return null;
  const box = geometry.boundingBox.clone().applyMatrix4(mesh.matrixWorld);
  return {
    min: [box.min.x, box.min.y, box.min.z],
    max: [box.max.x, box.max.y, box.max.z]
  };
}

function semanticKeyCandidate(mesh: THREE.Mesh): string | null {
  const name = mesh.name.trim();
  return BLUECAD_SEMANTIC_KEY.test(name) ? name : null;
}

function meshFact(mesh: THREE.Mesh, ordinal: number, sessionKey: string): GeometryInspectionMesh {
  const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
  return {
    sessionKey,
    meshKey: `mesh-${ordinal}`,
    semanticKey: semanticKeyCandidate(mesh),
    displayName: mesh.name.trim() || `Mesh ${ordinal}`,
    materialNames: materials.map((material) => material.name.trim()).filter(Boolean),
    triangleCount: triangleCount(mesh.geometry),
    worldBounds: worldBounds(mesh)
  };
}

function BluecadGlbViewer({ artifactUrl, inspectionCommand = null, onInspectionChange }: BluecadGlbViewerProps) {
  const mountRef = useRef<HTMLDivElement | null>(null);
  const [message, setMessage] = useState("Loading GLB artifact…");
  const generationRef = useRef(0);
  const inspectionChangeRef = useRef(onInspectionChange);
  const selectCurrentMeshRef = useRef<SessionSelection | null>(null);
  const sessionKeyRef = useRef<string | null>(null);
  inspectionChangeRef.current = onInspectionChange;

  useEffect(() => {
    if (!inspectionCommand) return;
    if (inspectionCommand.sessionKey !== sessionKeyRef.current) return;
    selectCurrentMeshRef.current?.(inspectionCommand.meshKey);
  }, [inspectionCommand]);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return undefined;
    const generation = ++generationRef.current;
    const publish = (snapshot: GeometryInspectionSnapshot) => {
      if (generationRef.current === generation) inspectionChangeRef.current?.(snapshot);
    };
    const clearInspection = (status: GeometryInspectionSnapshot["status"]) => {
      sessionKeyRef.current = null;
      selectCurrentMeshRef.current = null;
      publish({ sessionKey: null, status, meshes: [], selected: null });
    };

    setMessage("Loading GLB artifact…");
    clearInspection("loading");

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true });
    } catch (error) {
      console.error(error);
      setMessage("Unable to start the 3D viewer in this browser.");
      clearInspection("error");
      return undefined;
    }

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf8fafc);
    const camera = new THREE.PerspectiveCamera(45, mount.clientWidth / Math.max(mount.clientHeight, 1), 0.1, 10000);
    camera.position.set(160, 120, 160);

    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(mount.clientWidth, mount.clientHeight);
    renderer.domElement.setAttribute("role", "img");
    renderer.domElement.setAttribute("aria-label", "Interactive 3D preview and geometry inspection of generated BLUECAD geometry");
    mount.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;

    scene.add(new THREE.HemisphereLight(0xffffff, 0x64748b, 2.2));
    const directional = new THREE.DirectionalLight(0xffffff, 2.4);
    directional.position.set(80, 120, 90);
    scene.add(directional);
    const grid = new THREE.GridHelper(220, 22, 0x94a3b8, 0xe2e8f0);
    scene.add(grid);

    let disposed = false;
    let loadedScene: THREE.Object3D | null = null;
    let meshFacts: GeometryInspectionMesh[] = [];
    const meshByKey = new Map<string, THREE.Mesh>();
    const keyByMesh = new Map<THREE.Mesh, string>();
    const factByKey = new Map<string, GeometryInspectionMesh>();
    let selectedFact: GeometryInspectionMesh | null = null;
    let currentSessionKey: string | null = null;

    const emitReady = () => {
      if (!currentSessionKey || disposed) return;
      publish({ sessionKey: currentSessionKey, status: "ready", meshes: meshFacts, selected: selectedFact });
    };
    const selectMesh: SessionSelection = (meshKey) => {
      if (!currentSessionKey || disposed) return;
      selectedFact = meshKey ? factByKey.get(meshKey) ?? null : null;
      emitReady();
    };

    const loader = new GLTFLoader();
    loader.load(
      artifactUrl,
      (gltf: { scene: THREE.Object3D }) => {
        if (disposed) {
          disposeOwnedScene(gltf.scene);
          return;
        }
        if (generationRef.current !== generation) {
          disposeOwnedScene(gltf.scene);
          return;
        }
        loadedScene = gltf.scene;
        scene.add(gltf.scene);
        gltf.scene.updateMatrixWorld(true);

        currentSessionKey = `viewer-session-${generation}`;
        sessionKeyRef.current = currentSessionKey;
        meshFacts = [];
        meshByKey.clear();
        keyByMesh.clear();
        factByKey.clear();
        let ordinal = 0;
        gltf.scene.traverse((object) => {
          if (!(object instanceof THREE.Mesh)) return;
          ordinal += 1;
          const fact = meshFact(object, ordinal, currentSessionKey!);
          meshFacts.push(fact);
          meshByKey.set(fact.meshKey, object);
          keyByMesh.set(object, fact.meshKey);
          factByKey.set(fact.meshKey, fact);
        });
        selectedFact = null;
        selectCurrentMeshRef.current = selectMesh;

        const box = new THREE.Box3().setFromObject(gltf.scene);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        const maxDim = Math.max(size.x, size.y, size.z, 1);
        controls.target.copy(center);
        camera.position.copy(center).add(new THREE.Vector3(maxDim * 1.5, maxDim, maxDim * 1.5));
        camera.near = Math.max(maxDim / 1000, 0.01);
        camera.far = maxDim * 100;
        camera.updateProjectionMatrix();
        controls.update();
        setMessage("Orbit, pan, zoom, or click a mesh to inspect visible geometry.");
        emitReady();
      },
      undefined,
      (error: unknown) => {
        if (disposed) return;
        if (generationRef.current !== generation) return;
        console.error(error);
        setMessage("Unable to load this GLB artifact.");
        clearInspection("error");
      }
    );

    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    let pointerDown: { pointerId: number; x: number; y: number } | null = null;
    const onPointerDown = (event: PointerEvent) => {
      if (event.button !== 0) return;
      pointerDown = { pointerId: event.pointerId, x: event.clientX, y: event.clientY };
    };
    const onPointerUp = (event: PointerEvent) => {
      const start = pointerDown;
      pointerDown = null;
      if (!start || start.pointerId !== event.pointerId || event.button !== 0 || !currentSessionKey) return;
      if (Math.hypot(event.clientX - start.x, event.clientY - start.y) > 4) return;
      const rect = renderer.domElement.getBoundingClientRect();
      if (rect.width <= 0 || rect.height <= 0) return;
      pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(pointer, camera);
      const hit = raycaster.intersectObjects(Array.from(meshByKey.values()), false)[0]?.object;
      if (!(hit instanceof THREE.Mesh)) {
        selectMesh(null);
        return;
      }
      selectMesh(keyByMesh.get(hit) ?? null);
    };
    const onPointerCancel = () => { pointerDown = null; };
    renderer.domElement.addEventListener("pointerdown", onPointerDown);
    renderer.domElement.addEventListener("pointerup", onPointerUp);
    renderer.domElement.addEventListener("pointercancel", onPointerCancel);

    const resize = () => {
      camera.aspect = mount.clientWidth / Math.max(mount.clientHeight, 1);
      camera.updateProjectionMatrix();
      renderer.setSize(mount.clientWidth, mount.clientHeight);
    };
    const resizeObserver = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(resize);
    resizeObserver?.observe(mount);
    window.addEventListener("resize", resize);

    let animationFrame = 0;
    const animate = () => {
      if (disposed) return;
      controls.update();
      renderer.render(scene, camera);
      animationFrame = window.requestAnimationFrame(animate);
    };
    animate();

    return () => {
      disposed = true;
      if (generationRef.current === generation) {
        sessionKeyRef.current = null;
        selectCurrentMeshRef.current = null;
        inspectionChangeRef.current?.({ sessionKey: null, status: "idle", meshes: [], selected: null });
      }
      window.cancelAnimationFrame(animationFrame);
      resizeObserver?.disconnect();
      window.removeEventListener("resize", resize);
      renderer.domElement.removeEventListener("pointerdown", onPointerDown);
      renderer.domElement.removeEventListener("pointerup", onPointerUp);
      renderer.domElement.removeEventListener("pointercancel", onPointerCancel);
      meshByKey.clear();
      keyByMesh.clear();
      factByKey.clear();
      meshFacts = [];
      selectedFact = null;
      if (loadedScene) {
        scene.remove(loadedScene);
        disposeOwnedScene(loadedScene);
        loadedScene = null;
      }
      scene.remove(grid);
      grid.geometry.dispose();
      const gridMaterials = Array.isArray(grid.material) ? grid.material : [grid.material];
      for (const material of gridMaterials) material.dispose();
      controls.dispose();
      renderer.dispose();
      if (renderer.domElement.parentNode === mount) mount.removeChild(renderer.domElement);
    };
  }, [artifactUrl]);

  return (
    <div className="bluecad-viewer-shell">
      <div ref={mountRef} className="bluecad-viewer" />
      <p className="panel-subtitle" aria-live="polite">{message}</p>
    </div>
  );
}

export default BluecadGlbViewer;
