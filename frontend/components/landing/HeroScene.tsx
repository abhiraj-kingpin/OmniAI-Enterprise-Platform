"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

/** Nodes arranged on a sphere, each connected to its nearest few neighbors —
 * a stand-in for "many AI modules, one connected platform" rather than a
 * literal diagram of anything. Plain Three.js (no @react-three/fiber): R3F
 * v8's custom reconciler targets React 18.0-18.2 internals and throws
 * (`ReactCurrentOwner` undefined) against React 18.3 as pinned in this
 * project; R3F v9 needs React 19. A scene this simple doesn't need a
 * declarative renderer anyway — a plain WebGLRenderer in a rAF loop avoids
 * the version coupling entirely. */
export default function HeroScene() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 100);
    camera.position.set(0, 0, 7);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
    renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(renderer.domElement);

    scene.add(new THREE.AmbientLight(0xffffff, 0.6));

    const group = new THREE.Group();
    scene.add(group);

    const NODE_COUNT = 28;
    const nodePositions: THREE.Vector3[] = [];
    const golden = Math.PI * (3 - Math.sqrt(5));
    for (let i = 0; i < NODE_COUNT; i++) {
      const y = 1 - (i / (NODE_COUNT - 1)) * 2;
      const radius = Math.sqrt(1 - y * y);
      const theta = golden * i;
      nodePositions.push(
        new THREE.Vector3(Math.cos(theta) * radius, y, Math.sin(theta) * radius).multiplyScalar(2.2),
      );
    }

    const nodeGeometry = new THREE.SphereGeometry(0.035, 12, 12);
    nodePositions.forEach((pos, i) => {
      const material = new THREE.MeshBasicMaterial({ color: i % 5 === 0 ? 0x60a5fa : 0x93c5fd });
      const mesh = new THREE.Mesh(nodeGeometry, material);
      mesh.position.copy(pos);
      group.add(mesh);
    });

    const edgePoints: THREE.Vector3[] = [];
    nodePositions.forEach((p, i) => {
      const nearest = nodePositions
        .map((q, j) => ({ j, d: i === j ? Infinity : p.distanceTo(q) }))
        .sort((a, b) => a.d - b.d)
        .slice(0, 2);
      for (const { j } of nearest) edgePoints.push(p, nodePositions[j]);
    });
    const edgeGeometry = new THREE.BufferGeometry().setFromPoints(edgePoints);
    const edgeMaterial = new THREE.LineBasicMaterial({ color: 0x3b82f6, transparent: true, opacity: 0.18 });
    group.add(new THREE.LineSegments(edgeGeometry, edgeMaterial));

    const core = new THREE.Mesh(
      new THREE.IcosahedronGeometry(1.15, 1),
      new THREE.MeshBasicMaterial({ color: 0x1d4ed8, wireframe: true, transparent: true, opacity: 0.25 }),
    );
    group.add(core);

    let frameId: number;
    let floatTime = 0;
    const clock = new THREE.Clock();

    function animate() {
      const delta = clock.getDelta();
      floatTime += delta;
      group.rotation.y += delta * 0.08;
      group.position.y = Math.sin(floatTime * 0.6) * 0.15;
      renderer.render(scene, camera);
      frameId = requestAnimationFrame(animate);
    }
    animate();

    function handleResize() {
      if (!container) return;
      camera.aspect = container.clientWidth / container.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(container.clientWidth, container.clientHeight);
    }
    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(frameId);
      window.removeEventListener("resize", handleResize);
      nodeGeometry.dispose();
      edgeGeometry.dispose();
      edgeMaterial.dispose();
      core.geometry.dispose();
      (core.material as THREE.Material).dispose();
      group.traverse((obj) => {
        if (obj instanceof THREE.Mesh) (obj.material as THREE.Material).dispose?.();
      });
      renderer.dispose();
      container.removeChild(renderer.domElement);
    };
  }, []);

  return <div ref={containerRef} className="absolute inset-0" />;
}
