import { useEffect, useRef } from 'react';
import './SplashCursor.css';

const DEFAULT_COLORS = [
  '255, 209, 220',
  '203, 220, 255',
  '206, 244, 223',
  '255, 229, 204',
  '233, 221, 255',
];

function SplashCursor({
  DENSITY_DISSIPATION = 3.5,
  SPLAT_RADIUS = 0.2,
  SPLAT_FORCE = 6000,
  COLOR_UPDATE_SPEED = 10,
}) {
  const canvasRef = useRef(null);
  const particlesRef = useRef([]);
  const animationFrameRef = useRef(0);
  const colorIndexRef = useRef(0);
  const colorTickRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) {
      return undefined;
    }

    const context = canvas.getContext('2d');
    if (!context) {
      return undefined;
    }

    const resizeCanvas = () => {
      const ratio = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.floor(window.innerWidth * ratio);
      canvas.height = Math.floor(window.innerHeight * ratio);
      canvas.style.width = `${window.innerWidth}px`;
      canvas.style.height = `${window.innerHeight}px`;
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
    };

    const spawnSplash = (x, y) => {
      const count = Math.max(3, Math.min(10, Math.round(SPLAT_FORCE / 1200)));
      const radiusBase = Math.max(22, Math.min(70, SPLAT_RADIUS * 240));
      const color = DEFAULT_COLORS[colorIndexRef.current % DEFAULT_COLORS.length];

      for (let index = 0; index < count; index += 1) {
        const angle = (Math.PI * 2 * index) / count + Math.random() * 0.45;
        const velocity = 0.6 + Math.random() * 1.4;

        particlesRef.current.push({
          x,
          y,
          vx: Math.cos(angle) * velocity,
          vy: Math.sin(angle) * velocity,
          radius: radiusBase * (0.6 + Math.random() * 0.75),
          life: 1,
          decay: 0.008 * DENSITY_DISSIPATION + Math.random() * 0.008,
          color,
        });
      }
    };

    const handlePointerMove = (event) => {
      colorTickRef.current += 1;
      if (colorTickRef.current % Math.max(2, Math.round(14 - COLOR_UPDATE_SPEED)) === 0) {
        colorIndexRef.current += 1;
      }

      spawnSplash(event.clientX, event.clientY);

      if (particlesRef.current.length > 220) {
        particlesRef.current.splice(0, particlesRef.current.length - 220);
      }
    };

    const draw = () => {
      context.clearRect(0, 0, window.innerWidth, window.innerHeight);

      particlesRef.current = particlesRef.current.filter((particle) => particle.life > 0.02);

      particlesRef.current.forEach((particle) => {
        particle.x += particle.vx;
        particle.y += particle.vy;
        particle.vx *= 0.982;
        particle.vy *= 0.982;
        particle.life -= particle.decay;

        const gradient = context.createRadialGradient(
          particle.x,
          particle.y,
          0,
          particle.x,
          particle.y,
          particle.radius,
        );

        gradient.addColorStop(0, `rgba(${particle.color}, ${0.18 * particle.life})`);
        gradient.addColorStop(1, `rgba(${particle.color}, 0)`);

        context.fillStyle = gradient;
        context.beginPath();
        context.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
        context.fill();
      });

      animationFrameRef.current = window.requestAnimationFrame(draw);
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    window.addEventListener('pointermove', handlePointerMove, { passive: true });
    animationFrameRef.current = window.requestAnimationFrame(draw);

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      window.removeEventListener('pointermove', handlePointerMove);
      if (animationFrameRef.current) {
        window.cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [COLOR_UPDATE_SPEED, DENSITY_DISSIPATION, SPLAT_FORCE, SPLAT_RADIUS]);

  return (
    <div className="splash-cursor-layer" aria-hidden="true">
      <canvas ref={canvasRef} className="splash-cursor-canvas" />
    </div>
  );
}

export default SplashCursor;
