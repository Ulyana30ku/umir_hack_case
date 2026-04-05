import { useState } from 'react';

function DecorativeSlot({ src, label, caption, className = '' }) {
  const [imageFailed, setImageFailed] = useState(false);

  return (
    <div className={`decorative-slot ${className}`.trim()}>
      {!imageFailed && src ? (
        <img
          src={src}
          alt=""
          className="decorative-image"
          loading="lazy"
          onError={() => setImageFailed(true)}
          title={label || caption}
        />
      ) : (
        <div className="decorative-fallback" aria-label={label || caption || 'Decorative placeholder'}>
          <div className="decorative-fallback-title">Изображение</div>
        </div>
      )}
    </div>
  );
}

export default DecorativeSlot;
