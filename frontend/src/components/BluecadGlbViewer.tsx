import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

type BluecadGlbViewerProps = {
  artifactUrl: string;
};

function BluecadGlbViewer({ artifactUrl }: BluecadGlbViewerProps) {
  const mountRef = useRef<HTMLDivElement | null>(null);
  const [message, setMessage] = useState("Loading GLB artifact…");

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return undefined;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf8fafc);
    const camera = new THREE.PerspectiveCamera(45, mount.clientWidth / Math.max(mount.clientHeight, 1), 0.1, 10000);
    camera.position.set(160, 120, 160);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(mount.clientWidth, mount.clientHeight);
    mount.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;

    scene.add(new THREE.HemisphereLight(0xffffff, 0x64748b, 2.2));
    const directional = new THREE.DirectionalLight(0xffffff, 2.4);
    directional.position.set(80, 120, 90);
    scene.add(directional);
    scene.add(new THREE.GridHelper(220, 22, 0x94a3b8, 0xe2e8f0));

    let disposed = false;
    const loader = new GLTFLoader();
    loader.load(
      artifactUrl,
      (gltf: { scene: THREE.Object3D }) => {
        if (disposed) return;
        scene.add(gltf.scene);
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
        setMessage("Orbit, pan, and zoom to inspect the generated geometry.");
      },
      undefined,
      (error: unknown) => {
        console.error(error);
        setMessage("Unable to load this GLB artifact.");
      }
    );

    const resize = () => {
      camera.aspect = mount.clientWidth / Math.max(mount.clientHeight, 1);
      camera.updateProjectionMatrix();
      renderer.setSize(mount.clientWidth, mount.clientHeight);
    };
    window.addEventListener("resize", resize);

    const animate = () => {
      if (disposed) return;
      controls.update();
      renderer.render(scene, camera);
      window.requestAnimationFrame(animate);
    };
    animate();

    return () => {
      disposed = true;
      window.removeEventListener("resize", resize);
      controls.dispose();
      renderer.dispose();
      mount.removeChild(renderer.domElement);
    };
  }, [artifactUrl]);

  return (
    <div className="bluecad-viewer-shell">
      <div ref={mountRef} className="bluecad-viewer" />
      <p className="panel-subtitle">{message}</p>
    </div>
  );
}

export default BluecadGlbViewer;
