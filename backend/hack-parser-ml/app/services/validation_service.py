"""Validation service for product candidates."""

from typing import List, Optional
from app.schemas.product import ProductCandidate
from app.schemas.query import ProductTask
from app.core.logging import get_logger

logger = get_logger(__name__)


# Critical constraints that must be validated
CRITICAL_CONSTRAINTS = [
    "brand",
    "memory_gb",
    "condition",
]


class ValidationService:
    """Service for validating products against constraints."""
    
    def validate_product(
        self,
        candidate: ProductCandidate,
        task: ProductTask,
    ) -> ProductCandidate:
        """
        Validate a single product candidate against task constraints.
        
        Args:
            candidate: Product candidate to validate
            task: Product search task with constraints
            
        Returns:
            Updated candidate with matched/unmet constraints
        """
        candidate.matched_constraints = []
        candidate.unmet_constraints = []
        
        # Check brand
        if task.brand:
            if candidate.brand and task.brand.lower() == candidate.brand.lower():
                candidate.matched_constraints.append("brand")
            else:
                candidate.unmet_constraints.append("brand")
                candidate.rejection_reason = f"Brand mismatch: expected {task.brand}, got {candidate.brand}"
        
        # Check memory
        if task.memory_gb:
            if candidate.memory_gb == task.memory_gb:
                candidate.matched_constraints.append("memory_gb")
            else:
                candidate.unmet_constraints.append("memory_gb")
                candidate.rejection_reason = f"Memory mismatch: expected {task.memory_gb}GB, got {candidate.memory_gb}GB"
        
        # Check condition
        if task.condition:
            if candidate.condition == task.condition:
                candidate.matched_constraints.append("condition")
            else:
                candidate.unmet_constraints.append("condition")
                candidate.rejection_reason = f"Condition mismatch: expected {task.condition}, got {candidate.condition}"
        
        # Check price range
        if task.min_price and candidate.price:
            if candidate.price < task.min_price:
                candidate.unmet_constraints.append("min_price")
                candidate.rejection_reason = f"Price below minimum: {candidate.price} < {task.min_price}"
            else:
                candidate.matched_constraints.append("min_price")
        
        if task.max_price and candidate.price:
            if candidate.price > task.max_price:
                candidate.unmet_constraints.append("max_price")
                candidate.rejection_reason = f"Price above maximum: {candidate.price} > {task.max_price}"
            else:
                candidate.matched_constraints.append("max_price")
        
        # If no critical constraints were checked, mark as valid
        if not candidate.unmet_constraints:
            candidate.rejection_reason = None
        
        return candidate
    
    def validate_products(
        self,
        candidates: List[ProductCandidate],
        task: ProductTask,
    ) -> List[ProductCandidate]:
        """
        Validate multiple product candidates.
        
        Args:
            candidates: List of product candidates
            task: Product search task with constraints
            
        Returns:
            List of validated candidates
        """
        validated = []
        for candidate in candidates:
            validated_candidate = self.validate_product(candidate, task)
            validated.append(validated_candidate)
        
        logger.info(f"Validated {len(validated)} products")
        return validated
    
    def filter_valid(
        self,
        candidates: List[ProductCandidate],
    ) -> List[ProductCandidate]:
        """
        Filter out invalid (rejected) candidates.
        
        Args:
            candidates: List of validated candidates
            
        Returns:
            List of valid candidates only
        """
        return [c for c in candidates if not c.rejection_reason]
    
    def filter_by_constraints(
        self,
        candidates: List[ProductCandidate],
        required_constraints: List[str],
    ) -> List[ProductCandidate]:
        """
        Filter candidates that have all required constraints matched.
        
        Args:
            candidates: List of validated candidates
            required_constraints: List of constraint names that must be matched
            
        Returns:
            List of candidates with all required constraints
        """
        result = []
        for candidate in candidates:
            if all(c in candidate.matched_constraints for c in required_constraints):
                result.append(candidate)
        return result


# Singleton instance
_validation_service: Optional[ValidationService] = None


def get_validation_service() -> ValidationService:
    """Get the validation service singleton."""
    global _validation_service
    if _validation_service is None:
        _validation_service = ValidationService()
    return _validation_service


def validate_products(
    candidates: List[ProductCandidate],
    task: ProductTask,
) -> List[ProductCandidate]:
    """Validate products against task constraints."""
    service = get_validation_service()
    return service.validate_products(candidates, task)
