"""Tests for agent flow."""

import pytest

from app.schemas.query import ParsedUserQuery, ProductTask, NewsTask
from app.schemas.trace import AgentRunTrace, AgentTraceStep
from app.agents.planner import Planner


class TestAgentFlow:
    """Test cases for agent flow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.planner = Planner()
    
    def test_planner_product_only(self):
        """Test planning for product-only query."""
        query = ParsedUserQuery(
            raw_query="Найди iPhone",
            product_task=ProductTask(brand="Apple"),
            news_task=None,
            confidence=0.8,
        )
        
        plan = self.planner.create_plan(query)
        
        assert plan.run_product_search is True
        assert plan.run_news_search is False
        assert "search_products" in plan.steps
        assert "compose_answer" in plan.steps
    
    def test_planner_news_only(self):
        """Test planning for news-only query."""
        query = ParsedUserQuery(
            raw_query="Найди новости про Apple",
            product_task=None,
            news_task=NewsTask(topic="Apple"),
            confidence=0.8,
        )
        
        plan = self.planner.create_plan(query)
        
        assert plan.run_product_search is False
        assert plan.run_news_search is True
        assert "search_news" in plan.steps
        assert "compose_answer" in plan.steps
    
    def test_planner_combined(self):
        """Test planning for combined query."""
        query = ParsedUserQuery(
            raw_query="Найди iPhone и новости",
            product_task=ProductTask(brand="Apple"),
            news_task=NewsTask(topic="Apple"),
            confidence=0.8,
        )
        
        plan = self.planner.create_plan(query)
        
        assert plan.run_product_search is True
        assert plan.run_news_search is True
        assert "search_products" in plan.steps
        assert "search_news" in plan.steps
    
    def test_trace_add_step(self):
        """Test adding steps to trace."""
        trace = AgentRunTrace(
            run_id="test-001",
            user_query="test query",
        )
        
        step = AgentTraceStep(
            step_name="test_step",
            status="started",
        )
        
        trace.add_step(step)
        
        assert len(trace.steps) == 1
        assert trace.steps[0].step_name == "test_step"
    
    def test_trace_mark_completed(self):
        """Test marking step as completed."""
        trace = AgentRunTrace(
            run_id="test-001",
            user_query="test query",
        )
        
        trace.add_step(AgentTraceStep(
            step_name="test_step",
            status="started",
        ))
        
        trace.mark_completed("test_step", "result")
        
        step = trace.get_step("test_step")
        assert step.status == "completed"
        assert step.output_payload is not None
    
    def test_trace_mark_failed(self):
        """Test marking step as failed."""
        trace = AgentRunTrace(
            run_id="test-001",
            user_query="test query",
        )
        
        trace.add_step(AgentTraceStep(
            step_name="test_step",
            status="started",
        ))
        
        trace.mark_failed("test_step", "error message")
        
        step = trace.get_step("test_step")
        assert step.status == "failed"
        assert step.error_message == "error message"
    
    def test_trace_duration(self):
        """Test calculating step duration."""
        from datetime import datetime
        
        step = AgentTraceStep(
            step_name="test",
            status="started",
            started_at=datetime(2024, 1, 1, 10, 0, 0),
            finished_at=datetime(2024, 1, 1, 10, 0, 10),
        )
        
        assert step.duration_seconds() == 10.0


def test_planner_singleton():
    """Test that planner singleton works."""
    from app.agents.planner import get_planner
    
    planner1 = get_planner()
    planner2 = get_planner()
    
    assert planner1 is planner2
