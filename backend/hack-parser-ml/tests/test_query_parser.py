"""Tests for query parser."""

import pytest

from app.services.query_parser import QueryParser
from app.schemas.query import ParsedUserQuery, ProductTask, NewsTask


class TestQueryParser:
    """Test cases for QueryParser."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = QueryParser()
    
    def test_parse_product_only_query(self):
        """Test parsing a product-only query."""
        query = "Найди самый дешевый новый iPhone 256 ГБ"
        
        result = self.parser.parse(query)
        
        assert isinstance(result, ParsedUserQuery)
        assert result.raw_query == query
        assert result.product_task is not None
        assert result.news_task is None
    
    def test_parse_news_only_query(self):
        """Test parsing a news-only query."""
        query = "Найди новости про Apple за последнюю неделю"
        
        result = self.parser.parse(query)
        
        assert result.product_task is None
        assert result.news_task is not None
    
    def test_parse_combined_query(self):
        """Test parsing a combined product and news query."""
        query = "Найди самый дешевый новый iPhone 256 ГБ и новости про Apple за неделю"
        
        result = self.parser.parse(query)
        
        assert result.product_task is not None
        assert result.news_task is not None
    
    def test_extract_brand_apple(self):
        """Test extracting Apple brand."""
        query = "найди iPhone"
        
        result = self.parser.parse(query)
        
        assert result.product_task.brand == "Apple"
    
    def test_extract_brand_samsung(self):
        """Test extracting Samsung brand."""
        query = "найди Samsung Galaxy"
        
        result = self.parser.parse(query)
        
        assert result.product_task.brand == "Samsung"
    
    def test_extract_memory(self):
        """Test extracting memory size."""
        query = "найди iPhone 256 ГБ"
        
        result = self.parser.parse(query)
        
        assert result.product_task.memory_gb == 256
    
    def test_extract_condition_new(self):
        """Test extracting condition 'new'."""
        query = "найди новый iPhone"
        
        result = self.parser.parse(query)
        
        assert result.product_task.condition == "new"
    
    def test_extract_price_range(self):
        """Test extracting price range."""
        query = "найди iPhone до 100000 рублей"
        
        result = self.parser.parse(query)
        
        assert result.product_task.max_price == 100000.0
    
    def test_extract_sort_order(self):
        """Test extracting sort order."""
        query = "найди самый дешевый iPhone"
        
        result = self.parser.parse(query)
        
        assert result.product_task.sort_by == "price_asc"
    
    def test_confidence_calculation(self):
        """Test confidence calculation."""
        query = "найди новый Apple iPhone 256 ГБ"
        
        result = self.parser.parse(query)
        
        # Should have high confidence with brand, memory, condition
        assert result.confidence > 0.5
    
    def test_detect_ambiguities(self):
        """Test detecting ambiguities."""
        query = "найди iPhone"
        
        result = self.parser.parse(query)
        
        # Should have ambiguities for missing constraints
        assert len(result.ambiguities) > 0


def test_query_parser_singleton():
    """Test that query parser singleton works."""
    from app.services.query_parser import get_query_parser
    
    parser1 = get_query_parser()
    parser2 = get_query_parser()
    
    assert parser1 is parser2
