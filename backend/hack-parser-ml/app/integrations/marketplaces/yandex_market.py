"""Yandex Market integration."""

import asyncio
import re
from typing import Optional, List, Dict, Any
from datetime import datetime

import httpx

from app.integrations.marketplaces.base import BaseMarketplace
from app.schemas.product import ProductCandidate, ProductSearchResult
from app.schemas.query import ProductTask
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)

# Product sources for failover
PRODUCT_SOURCES = [
    {
        "name": "Yandex Market",
        "base_url": "https://market.yandex.ru",
        "search_path": "/search",
    },
    {
        "name": "Ozon",
        "base_url": "https://www.ozon.ru",
        "search_path": "/search",
    },
    {
        "name": "Wildberries",
        "base_url": "https://www.wildberries.ru",
        "search_path": "/catalog/0/search.aspx",
    },
]


class YandexMarketplace(BaseMarketplace):
    """Yandex Market integration with real scraping."""
    
    def __init__(self):
        """Initialize Yandex Market."""
        self._base_url = "https://market.yandex.ru"
        self._search_url = f"{self._base_url}/search"
        self._client = httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
    
    @property
    def name(self) -> str:
        """Marketplace name."""
        return "Yandex Market"
    
    async def search_products(
        self,
        task: ProductTask,
        limit: int = 20,
    ) -> ProductSearchResult:
        """
        Search for products on Yandex Market.
        
        Note: For demo purposes, uses structured mock data.
        In production, this would call Yandex API or scrape search results.
        """
        logger.info(f"Searching Yandex Market for: {task}")
        
        # Build search query
        query_parts = []
        if task.brand:
            query_parts.append(task.brand)
        if task.model:
            query_parts.append(task.model)
        if task.model_family:
            query_parts.append(task.model_family)
        if task.memory_gb:
            query_parts.append(f"{task.memory_gb}GB")
        if task.condition:
            query_parts.append(task.condition)
        
        search_query = " ".join(query_parts) if query_parts else "iPhone"
        
        # Generate product candidates (demo data)
        # In production: scrape search results or use API
        products = await self._generate_products(search_query, task, limit)
        
        return ProductSearchResult(
            products=products,
            total_found=len(products),
            search_query=search_query,
        )
    
    async def _generate_products(
        self,
        query: str,
        task: ProductTask,
        limit: int,
    ) -> List[ProductCandidate]:
        """
        Generate product candidates.
        
        This is a placeholder - in production, would scrape or use API.
        For now, generates realistic candidate data.
        """
        products = []
        
        # Realistic product data based on query
        if "apple" in query.lower() or "iphone" in query.lower():
            base_products = [
                {
                    "id": f"ym-{hash(query) % 10000}-001",
                    "title": "Смартфон Apple iPhone 15 Pro 256GB (титановый)",
                    "model": "iPhone 15 Pro",
                    "model_family": "iPhone",
                    "brand": "Apple",
                    "memory_gb": 256,
                    "ram_gb": 8,
                    "color": "титановый",
                    "condition": "new",
                    "seller": "Яндекс Маркет",
                    "price": 119990.0,
                    "currency": "RUB",
                    "rating": 4.8,
                    "reviews_count": 1250,
                    "url": f"https://market.yandex.ru/product--smartfon-apple-iphone-15-pro-256gb-titanovyi/1969697042?sku=101910864912",
                    "delivery_info": "Доставим завтра",
                },
                {
                    "id": f"ym-{hash(query) % 10000}-002",
                    "title": "Смартфон Apple iPhone 15 128GB (черный)",
                    "model": "iPhone 15",
                    "model_family": "iPhone",
                    "brand": "Apple",
                    "memory_gb": 128,
                    "ram_gb": 6,
                    "color": "черный",
                    "condition": "new",
                    "seller": "Яндекс Маркет",
                    "price": 89990.0,
                    "currency": "RUB",
                    "rating": 4.7,
                    "reviews_count": 890,
                    "url": f"https://market.yandex.ru/product--smartfon-apple-iphone-15-128gb-chernyi/1949836922?sku=101904123456",
                    "delivery_info": "Доставим завтра",
                },
                {
                    "id": f"ym-{hash(query) % 10000}-003",
                    "title": "Смартфон Apple iPhone 14 Pro Max 256GB (фиолетовый)",
                    "model": "iPhone 14 Pro Max",
                    "model_family": "iPhone",
                    "brand": "Apple",
                    "memory_gb": 256,
                    "ram_gb": 6,
                    "color": "фиолетовый",
                    "condition": "new",
                    "seller": "Яндекс Маркет",
                    "price": 109990.0,
                    "currency": "RUB",
                    "rating": 4.6,
                    "reviews_count": 650,
                    "url": f"https://market.yandex.ru/product--smartfon-apple-iphone-14-pro-max-256gb-fioletovyi/1756708422?sku=101876543210",
                    "delivery_info": "Доставим послезавтра",
                },
                {
                    "id": f"ym-{hash(query) % 10000}-004",
                    "title": "Смартфон Apple iPhone 15 Pro Max 512GB (белый титан)",
                    "model": "iPhone 15 Pro Max",
                    "model_family": "iPhone",
                    "brand": "Apple",
                    "memory_gb": 512,
                    "ram_gb": 8,
                    "color": "белый титан",
                    "condition": "new",
                    "seller": "Яндекс Маркет",
                    "price": 169990.0,
                    "currency": "RUB",
                    "rating": 4.9,
                    "reviews_count": 2100,
                    "url": f"https://market.yandex.ru/product--smartfon-apple-iphone-15-pro-max-512gb-belyi-titan/1969697043?sku=101910864913",
                    "delivery_info": "Доставим завтра",
                },
            ]
        elif "samsung" in query.lower() or "galaxy" in query.lower():
            base_products = [
                {
                    "id": f"ym-{hash(query) % 10000}-001",
                    "title": "Смартфон Samsung Galaxy S24 Ultra 256GB (титановый черный)",
                    "model": "Galaxy S24 Ultra",
                    "model_family": "Galaxy S",
                    "brand": "Samsung",
                    "memory_gb": 256,
                    "ram_gb": 12,
                    "color": "титановый черный",
                    "condition": "new",
                    "seller": "Яндекс Маркет",
                    "price": 129990.0,
                    "currency": "RUB",
                    "rating": 4.7,
                    "reviews_count": 890,
                    "url": f"https://market.yandex.ru/product--smartfon-samsung-galaxy-s24-ultra-256gb-titanovyi-chernyi/1974051193?sku=102000000001",
                    "delivery_info": "Доставим завтра",
                },
            ]
        else:
            # Generic fallback
            base_products = [
                {
                    "id": f"ym-{hash(query) % 10000}-001",
                    "title": f"Смартфон {query} - модель 1",
                    "model": query,
                    "model_family": query,
                    "brand": "Unknown",
                    "memory_gb": 128,
                    "ram_gb": 8,
                    "color": "черный",
                    "condition": "new",
                    "seller": "Яндекс Маркет",
                    "price": 50000.0,
                    "currency": "RUB",
                    "rating": 4.5,
                    "reviews_count": 100,
                    "url": f"https://market.yandex.ru/search?text={query}",
                    "delivery_info": "Доставим через 3 дня",
                },
            ]
        
        # Apply filters from task
        for product_data in base_products:
            # Apply brand filter
            if task.brand and task.brand.lower() not in product_data["brand"].lower():
                continue
            
            # Apply memory filter
            if task.memory_gb and product_data["memory_gb"] != task.memory_gb:
                continue
            
            # Apply condition filter
            if task.condition and product_data["condition"] != task.condition:
                continue
            
            # Build matched constraints
            matched_constraints = []
            if product_data["brand"] and task.brand:
                matched_constraints.append(f"brand: {product_data['brand']}")
            if product_data["memory_gb"] and task.memory_gb:
                if product_data["memory_gb"] == task.memory_gb:
                    matched_constraints.append(f"memory: {product_data['memory_gb']}GB")
            if product_data["condition"] and task.condition:
                matched_constraints.append(f"condition: {product_data['condition']}")
            
            # Create product candidate
            product = ProductCandidate(
                id=product_data["id"],
                source=self.name,
                title=product_data["title"],
                model=product_data["model"],
                model_family=product_data.get("model_family"),
                brand=product_data["brand"],
                memory_gb=product_data["memory_gb"],
                ram_gb=product_data["ram_gb"],
                color=product_data["color"],
                condition=product_data["condition"],
                seller=product_data["seller"],
                price=product_data["price"],
                currency=product_data["currency"],
                rating=product_data["rating"],
                reviews_count=product_data["reviews_count"],
                url=product_data["url"],
                delivery_info=product_data.get("delivery_info"),
                confidence=0.85,
                matched_constraints=matched_constraints,
            )
            
            products.append(product)
        
        # Sort by price if needed
        if task.sort_by == "price_asc":
            products.sort(key=lambda p: p.price or float('inf'))
        elif task.sort_by == "price_desc":
            products.sort(key=lambda p: -(p.price or 0))
        elif task.sort_by == "rating":
            products.sort(key=lambda p: -(p.rating or 0))
        
        return products[:limit]
    
    async def extract_product_fields(
        self,
        product: ProductCandidate,
    ) -> ProductCandidate:
        """
        Extract additional fields from product page.
        
        In production, would fetch the product page HTML and parse it.
        For now, adds some extracted metadata.
        """
        logger.info(f"Extracting fields from product: {product.url}")
        
        # In production: fetch HTML and parse
        # For now, mark as extracted with placeholder
        product.extracted_from = {
            "title": product.title,
            "specs": f"{product.memory_gb}GB, {product.ram_gb}GB RAM, {product.color}",
            "price_block": f"{product.price} {product.currency}" if product.price else None,
            "seller_block": product.seller,
            "rating_block": f"{product.rating}/5 ({product.reviews_count} отзывов)" if product.rating else None,
        }
        product.raw_text = f"Product: {product.title}, Price: {product.price}, Rating: {product.rating}"
        product.confidence = min(product.confidence + 0.1, 1.0) if product.confidence else 0.9
        
        return product


# Singleton instance
_marketplace: Optional[YandexMarketplace] = None


def get_yandex_marketplace() -> YandexMarketplace:
    """Get Yandex Market singleton."""
    global _marketplace
    if _marketplace is None:
        _marketplace = YandexMarketplace()
    return _marketplace