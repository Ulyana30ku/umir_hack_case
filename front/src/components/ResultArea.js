import { useEffect, useRef, useState } from 'react';
import ParsedQueryCard from './ParsedQueryCard.js';
import ProductCard from './ProductCard.js';
import NewsList from './NewsList.js';
import SummaryCard from './SummaryCard.js';
import DecorativeSlot from './DecorativeSlot.js';

function ResultArea({ data, loading, hasSearched }) {
  const bottomOrnamentRef = useRef(null);
  const [isBottomOrnamentVisible, setIsBottomOrnamentVisible] = useState(false);

  useEffect(() => {
    if (!bottomOrnamentRef.current) {
      return undefined;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsBottomOrnamentVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.2 },
    );

    observer.observe(bottomOrnamentRef.current);

    return () => observer.disconnect();
  }, []);

  return (
    <section className="result-shell">
      <div className="result-header">
        <div>
          <h2 className="section-title">Результаты</h2>
        </div>
      </div>

      {loading ? (
        <div className="result-grid result-grid-loading" aria-live="polite">
          <div className="skeleton-card skeleton-compact" />
          <div className="skeleton-card skeleton-featured" />
          <div className="skeleton-card skeleton-rail" />
        </div>
      ) : data ? (
        <>
          <div className="result-grid">
            <article className="result-panel parsed-panel">
              <ParsedQueryCard parsedQuery={data.parsed_query} />
            </article>

            <article className="result-panel product-panel">
              <ProductCard product={data.best_product} />
            </article>

            <article className="result-panel summary-panel">
              <SummaryCard summary={data.summary} />
            </article>

            <article className="result-panel news-panel">
              <NewsList news={data.news} />
            </article>
          </div>
        </>
      ) : hasSearched ? (
        <div className="empty-state-soft">Пока нет результатов. Отправьте запрос, чтобы увидеть ответ здесь.</div>
      ) : (
        <div className="empty-results">
          <div className="empty-results-copy">
            <h3>Результаты появятся здесь</h3>
            <p>
              Введите запрос и отправьте его, чтобы увидеть разобранный intent, лучший товар, новости и summary.
            </p>
          </div>
        </div>
      )}

      <div
        ref={bottomOrnamentRef}
        className={`result-ornaments-bottom ${isBottomOrnamentVisible ? 'is-visible' : ''}`.trim()}
        aria-hidden="true"
      >
        <DecorativeSlot src="/decor-2.png" label="/decor-2.png" caption="Декоративное изображение блока результатов" className="result-orb-bottom" />
      </div>
    </section>
  );
}

export default ResultArea;
