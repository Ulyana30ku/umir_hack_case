"""Answer composition service."""

from typing import Optional, List
from datetime import datetime

from app.schemas.response import FinalAnswer, SourceScore
from app.schemas.query import ParsedUserQuery, ProductTask, NewsTask
from app.schemas.product import ProductCandidate
from app.schemas.news import NewsItem
from app.schemas.trace import AgentRunTrace, AgentTraceStep
from app.services.ranking_service import get_source_scores
from app.core.logging import get_logger

logger = get_logger(__name__)


class AnswerService:
    """Service for composing the final answer."""
    
    def compose_answer(
        self,
        parsed_query: ParsedUserQuery,
        selected_product: Optional[ProductCandidate],
        alternative_products: List[ProductCandidate],
        rejected_products: List[ProductCandidate],
        news: List[NewsItem],
        trace: AgentRunTrace,
    ) -> FinalAnswer:
        """
        Compose the final answer from all components.
        
        Args:
            parsed_query: Original parsed query
            selected_product: Selected product or None
            alternative_products: List of alternative products
            rejected_products: List of rejected products
            news: List of news items
            trace: Execution trace
            
        Returns:
            FinalAnswer with summary and explanation
        """
        logger.info("Composing final answer")
        
        # Generate summary
        summary = self._generate_summary(
            parsed_query,
            selected_product,
            news,
        )
        
        # Generate explanation
        explanation = self._generate_explanation(
            parsed_query.product_task,
            selected_product,
            alternative_products,
            rejected_products,
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            parsed_query,
            selected_product,
            news,
        )
        
        # Collect sources
        sources = self._collect_sources(selected_product, news)
        
        # Get source scores
        source_scores = get_source_scores(sources)
        
        return FinalAnswer(
            summary=summary,
            selected_product=selected_product,
            alternative_products=alternative_products,
            rejected_products=rejected_products,
            news=news,
            sources=sources,
            source_scores=source_scores,
            explanation=explanation,
            confidence=confidence,
            trace=trace,
        )
    
    def _generate_summary(
        self,
        parsed_query: ParsedUserQuery,
        selected_product: Optional[ProductCandidate],
        news: List[NewsItem],
    ) -> str:
        """Generate summary text."""
        parts = []
        
        # Product summary
        if selected_product:
            price_str = f"{selected_product.price:,.0f} {selected_product.currency}" if selected_product.price else "Цена не указана"
            parts.append(
                f"Найден {selected_product.brand} {selected_product.model} "
                f"{selected_product.memory_gb}GB по цене {price_str}."
            )
        elif parsed_query.product_task:
            parts.append("Не удалось найти товар по вашим критериям.")
        
        # News summary
        if news:
            parts.append(f"Подобрано {len(news)} новостей по теме.")
        
        return " ".join(parts) if parts else "Запрос обработан."
    
    def _generate_explanation(
        self,
        task: Optional[ProductTask],
        selected: Optional[ProductCandidate],
        alternatives: List[ProductCandidate],
        rejected: List[ProductCandidate],
    ) -> str:
        """Generate explanation for product selection."""
        if not selected:
            return "Товар не выбран - не найдено соответствующих критериям предложений."
        
        # Build explanation
        explanation_parts = []
        
        # Add matched constraints
        if selected.matched_constraints:
            constraints_str = ", ".join(selected.matched_constraints)
            explanation_parts.append(f"Подтверждены: {constraints_str}.")
        
        # Add selection reason
        explanation_parts.append(
            f"Выбран как лучший кандидат среди товаров с подтвержденными ограничениями."
        )
        
        # Add price info if relevant
        if selected.price:
            explanation_parts.append(f"Цена: {selected.price:,.0f} {selected.currency}.")
        
        # Add alternatives info
        if alternatives:
            explanation_parts.append(
                f"Также найдено {len(alternatives)} альтернативных вариантов."
            )
        
        # Add rejected products info if any
        if rejected:
            rejection_summary = []
            for r in rejected[:3]:  # Show top 3 rejected
                if r.rejection_reason:
                    reason = r.rejection_reason[:50] + "..." if len(r.rejection_reason) > 50 else r.rejection_reason
                    rejection_summary.append(f"- {r.title}: {reason}")
            
            if rejection_summary:
                explanation_parts.append(
                    f"Отклонено {len(rejected)} кандидатов: " + "; ".join(rejection_summary[:2])
                )
        
        return " ".join(explanation_parts)
    
    def _calculate_confidence(
        self,
        parsed_query: ParsedUserQuery,
        selected_product: Optional[ProductCandidate],
        news: List[NewsItem],
    ) -> float:
        """Calculate overall confidence score."""
        # Base confidence from query parsing
        confidence = parsed_query.confidence * 0.3
        
        # Add product confidence if selected
        if selected_product:
            confidence += 0.4 * (selected_product.confidence or 0.5)
            # Bonus for full constraint match
            if len(selected_product.matched_constraints) >= 2:
                confidence += 0.1
        
        # Add news confidence
        if news:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _collect_sources(
        self,
        selected_product: Optional[ProductCandidate],
        news: List[NewsItem],
    ) -> List[str]:
        """Collect source names."""
        sources = set()
        
        if selected_product:
            sources.add(selected_product.source)
        
        for item in news:
            sources.add(item.source)
        
        return sorted(list(sources))


# Singleton instance
_answer_service: Optional[AnswerService] = None


def get_answer_service() -> AnswerService:
    """Get the answer service singleton."""
    global _answer_service
    if _answer_service is None:
        _answer_service = AnswerService()
    return _answer_service


def compose_answer(
    parsed_query: ParsedUserQuery,
    selected_product: Optional[ProductCandidate],
    alternative_products: List[ProductCandidate],
    rejected_products: List[ProductCandidate],
    news: List[NewsItem],
    trace: AgentRunTrace,
) -> FinalAnswer:
    """Compose the final answer."""
    service = get_answer_service()
    return service.compose_answer(
        parsed_query,
        selected_product,
        alternative_products,
        rejected_products,
        news,
        trace,
    )
