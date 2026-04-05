function ErrorState({ message }) {
  return (
    <section className="error-shell glass-panel" role="alert" aria-live="assertive">
      <div className="card-kicker error-kicker">Ошибка запроса</div>
      <p className="error-text">{message}</p>
    </section>
  );
}

export default ErrorState;
