import DecorativeSlot from './DecorativeSlot.js';

function HeroArea({ title, subtitle }) {
  return (
    <section className="hero-area">
      <div className="hero-copy-panel">
        <h1 className="hero-title">{title}</h1>
        <p className="hero-subtitle">{subtitle}</p>
      </div>

      <div className="hero-ornaments" aria-hidden="true">
        <DecorativeSlot src="/decor-2.png" label="/decor-2.png" className="hero-center-orb hero-orb-large" />
      </div>
    </section>
  );
}

export default HeroArea;
