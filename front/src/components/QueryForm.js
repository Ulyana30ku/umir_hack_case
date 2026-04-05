function QueryForm({ value, onChange, onSubmit, onUseSample, sampleQueries, loading }) {
  return (
    <section className="query-shell">
      <form className="query-form" onSubmit={onSubmit}>
        <h2 className="section-title section-title-center">Поиск</h2>

        <div className="search-shell">
          <span className="search-icon" aria-hidden="true">⌕</span>
          <textarea
            className="query-textarea"
            value={value}
            onChange={(event) => onChange(event.target.value)}
            placeholder="Найди самый дешевый новый iPhone с 256 ГБ памяти и новости про Apple"
            rows={3}
          />
        </div>

        <div className="sample-chip-row" aria-label="Примеры запросов">
          {sampleQueries.map((sampleQuery, index) => (
            <button
              key={`${sampleQuery}-${index}`}
              type="button"
              className="sample-chip"
              onClick={() => onUseSample(sampleQuery)}
            >
              {sampleQuery}
            </button>
          ))}
        </div>

        <div className="query-actions">
          <button className="submit-button" type="submit" disabled={loading}>
            {loading ? 'Идёт поиск...' : 'Найти товары и новости'}
          </button>
        </div>
      </form>
    </section>
  );
}

export default QueryForm;
