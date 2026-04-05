function SummaryCard({ summary }) {
  return (
    <>
      <div className="card-kicker">Итог</div>
      {summary ? <p className="summary-text">{summary}</p> : <div className="empty-state-soft">Summary не вернулся.</div>}
    </>
  );
}

export default SummaryCard;
