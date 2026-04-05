function NewsList({ news }) {
  return (
    <>
      <div className="card-kicker">Новости</div>

      {!news || news.length === 0 ? (
        <div className="empty-state-soft">Для этой темы не найдено новостей.</div>
      ) : (
        <div className="news-list">
          {news.map((item) => (
            <article className="news-item" key={`${item.title}-${item.date}`}>
              <h4>{item.title}</h4>
              <p>{item.date}</p>
              <a href={item.url} target="_blank" rel="noreferrer">
                Читать статью
              </a>
            </article>
          ))}
        </div>
      )}
    </>
  );
}

export default NewsList;
