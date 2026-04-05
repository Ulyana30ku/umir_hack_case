function ProductCard({ product }) {
  if (!product) {
    return (
      <>
        <div className="card-kicker">Лучший товар</div>
        <div className="empty-state-soft">
          Под запрос не нашлось подходящего товара. Попробуйте другой запрос или ослабьте фильтры.
        </div>
      </>
    );
  }

  const fields = [
    ['Memory', product.memory],
    ['Condition', product.condition],
    ['Seller', product.seller],
    ['Rating', `${product.rating} / 5`],
    ['Reviews', product.reviews_count],
    ['Delivery', product.delivery],
  ];

  return (
    <>
      <div className="card-kicker">Лучший товар</div>
      <h3 className="product-title">{product.title}</h3>
      <p className="product-meta">Лучшее совпадение, выбранное бэкендом.</p>
      <div className="product-price">{product.price.toLocaleString('en-US')} ₽</div>

      <div className="product-details">
        {fields.map(([label, value]) => (
          <div className="product-detail-row" key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>

      <a className="product-link" href={product.url} target="_blank" rel="noreferrer">
        Открыть товар
      </a>
    </>
  );
}

export default ProductCard;
