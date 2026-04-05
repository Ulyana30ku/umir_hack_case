function ParsedQueryCard({ parsedQuery }) {
  if (!parsedQuery) {
    return <div className="empty-state-soft">Бэкенд не вернул разобранные данные.</div>;
  }

  const fields = [
    ['Product', parsedQuery.product],
    ['Memory', `${parsedQuery.memory_gb} GB`],
    ['Condition', parsedQuery.condition],
    ['Sort by', parsedQuery.sort_by],
    ['News topic', parsedQuery.news_topic],
  ];

  return (
    <>
      <div className="card-kicker">Разобранный запрос</div>
      <dl className="definition-list">
        {fields.map(([label, value]) => (
          <div className="definition-row" key={label}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
    </>
  );
}

export default ParsedQueryCard;
