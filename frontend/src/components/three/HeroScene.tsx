import { useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { MeshDistortMaterial, Float, Stars } from '@react-three/drei'
import type { Mesh } from 'three'

function FloatingSphere() {
  const meshRef = useRef<Mesh>(null)

  useFrame(({ clock }) => {
    if (meshRef.current) {
      meshRef.current.rotation.x = clock.getElapsedTime() * 0.15
      meshRef.current.rotation.y = clock.getElapsedTime() * 0.2
    }
  })

  return (
    <Float speed={2} rotationIntensity={0.4} floatIntensity={0.8}>
      <mesh ref={meshRef} scale={2.2}>
        <icosahedronGeometry args={[1, 4]} />
        <MeshDistortMaterial
          color="#7c3aed"
          attach="material"
          distort={0.35}
          speed={2}
          roughness={0.1}
          metalness={0.8}
          wireframe={false}
        />
      </mesh>
    </Float>
  )
}

function WireFrame() {
  const meshRef = useRef<Mesh>(null)
  useFrame(({ clock }) => {
    if (meshRef.current) {
      meshRef.current.rotation.x = clock.getElapsedTime() * -0.08
      meshRef.current.rotation.y = clock.getElapsedTime() * 0.12
    }
  })
  return (
    <mesh ref={meshRef} scale={3.4}>
      <icosahedronGeometry args={[1, 1]} />
      <meshBasicMaterial color="#a78bfa" wireframe opacity={0.12} transparent />
    </mesh>
  )
}

function Ring() {
  const meshRef = useRef<Mesh>(null)
  useFrame(({ clock }) => {
    if (meshRef.current) {
      meshRef.current.rotation.x = Math.PI / 2 + clock.getElapsedTime() * 0.05
      meshRef.current.rotation.z = clock.getElapsedTime() * 0.1
    }
  })
  return (
    <mesh ref={meshRef}>
      <torusGeometry args={[3.2, 0.015, 8, 80]} />
      <meshBasicMaterial color="#e879f9" opacity={0.3} transparent />
    </mesh>
  )
}

export default function HeroScene() {
  return (
    <div className="w-full h-full">
      <Canvas
        camera={{ position: [0, 0, 7], fov: 50 }}
        dpr={[1, 2]}
        gl={{ antialias: true, alpha: true }}
      >
        <ambientLight intensity={0.3} />
        <pointLight position={[5, 5, 5]} color="#7c3aed" intensity={4} />
        <pointLight position={[-5, -3, -5]} color="#e879f9" intensity={2} />
        <pointLight position={[0, 5, -5]} color="#a78bfa" intensity={1.5} />
        <Stars radius={80} depth={50} count={800} factor={3} fade speed={0.6} />
        <FloatingSphere />
        <WireFrame />
        <Ring />
      </Canvas>
    </div>
  )
}
