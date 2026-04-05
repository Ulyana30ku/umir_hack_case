const DEFAULT_COLORS = [
  '255, 209, 220',
  '203, 220, 255',
  '206, 244, 223',
  '255, 229, 204',
  '233, 221, 255',
];

function initSplashCursor() {
  const container = document.getElementById('splashLayer');
  if (!container) return;

  const canvas = document.createElement('canvas');
  canvas.className = 'splash-cursor-canvas';
  container.appendChild(canvas);

  const context = canvas.getContext('2d');
  const particles = [];
  let colorIndex = 0;
  let colorTick = 0;

  const resizeCanvas = () => {
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.floor(window.innerWidth * ratio);
    canvas.height = Math.floor(window.innerHeight * ratio);
    canvas.style.width = `${window.innerWidth}px`;
    canvas.style.height = `${window.innerHeight}px`;
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
  };

  const spawnSplash = (x, y) => {
    const count = Math.max(4, Math.min(8, Math.round(6000 / 1200)));
    const radiusBase = Math.max(25, Math.min(50, 0.2 * 240));
    const color = DEFAULT_COLORS[colorIndex % DEFAULT_COLORS.length];

    for (let i = 0; i < count; i++) {
      const angle = (Math.PI * 2 * i) / count + Math.random() * 0.5;
      const velocity = radiusBase + Math.random() * (radiusBase * 0.3);
      particles.push({
        x,
        y,
        vx: Math.cos(angle) * velocity,
        vy: Math.sin(angle) * velocity,
        alpha: 1,
        color,
        size: 5 + Math.random() * 3,
      });
    }

    colorTick++;
    if (colorTick >= 8) {
      colorIndex++;
      colorTick = 0;
    }
  };

  const update = () => {
    for (let i = particles.length - 1; i >= 0; i--) {
      const p = particles[i];
      p.vx *= 0.96;
      p.vy *= 0.96;
      p.vy += 0.12;
      p.x += p.vx;
      p.y += p.vy;
      p.alpha -= 1 / 50;

      if (p.alpha <= 0) {
        particles.splice(i, 1);
      }
    }
  };

  const draw = () => {
    context.clearRect(0, 0, canvas.width, canvas.height);

    for (const p of particles) {
      context.fillStyle = `rgba(${p.color}, ${Math.max(0, p.alpha * 0.8)})`;
      context.beginPath();
      context.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      context.fill();
    }
  };

  const animate = () => {
    update();
    draw();
    requestAnimationFrame(animate);
  };

  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);
  
  document.addEventListener('mousemove', (e) => {
    spawnSplash(e.clientX, e.clientY);
  });

  animate();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initSplashCursor);
} else {
  initSplashCursor();
}
