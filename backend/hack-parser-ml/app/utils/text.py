"""Text utilities for normalization and parsing."""

import re
from typing import Optional


def normalize_text(text: str) -> str:
    """Normalize text by removing extra spaces and converting to lowercase."""
    return re.sub(r'\s+', ' ', text).strip().lower()


def extract_number(text: str) -> Optional[int]:
    """Extract number from text."""
    match = re.search(r'\d+', text)
    if match:
        return int(match.group())
    return None


def normalize_memory(text: str) -> Optional[int]:
    """Normalize memory size to GB."""
    text = text.lower().replace(',', '.').replace(' ', '')
    
    # Match patterns like "256gb", "256 гб", "256gb"
    match = re.search(r'(\d+(?:\.\d+)?)\s*(gb|гб)', text)
    if match:
        value = float(match.group(1))
        return int(value)
    
    # Match patterns like "256 мб" - convert to GB
    match = re.search(r'(\d+)\s*(mb|мб)', text)
    if match:
        value = int(match.group(1))
        return value // 1024
    
    return None


def normalize_condition(text: str) -> Optional[str]:
    """Normalize condition keywords."""
    text = text.lower()
    
    # New condition mappings
    new_keywords = ['новый', 'new', 'не б/у', 'небу', 'brand new', 'новое', 'нов']
    if any(kw in text for kw in new_keywords):
        return 'new'
    
    # Used condition mappings
    used_keywords = ['б/у', 'бу', 'used', 'б/у', '-second-hand', 'бывший в употреблении']
    if any(kw in text for kw in used_keywords):
        return 'used'
    
    # Refurbished condition mappings
    refurbished_keywords = ['refurbished', 'восстановленный', 'реф']
    if any(kw in text for kw in refurbished_keywords):
        return 'refurbished'
    
    return None


def extract_price(text: str) -> Optional[float]:
    """Extract price from text."""
    # Remove currency symbols and normalize
    text = text.replace(' ', '').replace('\xa0', '')
    
    # Match patterns like "1000 руб", "1000р", "1000"
    match = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:руб|р\.?)', text)
    if match:
        value = match.group(1).replace(',', '.')
        return float(value)
    
    # Just number
    match = re.search(r'(\d+(?:[.,]\d+)?)', text)
    if match:
        value = match.group(1).replace(',', '.')
        return float(value)
    
    return None


def extract_sort_order(text: str) -> Optional[str]:
    """Extract sort order from text."""
    text = text.lower()
    
    if 'дешев' in text or 'cheap' in text or 'низк' in text:
        return 'price_asc'
    if 'дорог' in text or 'expensive' in text or 'высок' in text:
        return 'price_desc'
    if 'рейтинг' in text or 'rating' in text:
        return 'rating'
    
    return None


def extract_time_period(text: str) -> Optional[int]:
    """Extract time period in days from text."""
    text = text.lower()
    
    # Week patterns
    if 'недел' in text:
        match = re.search(r'(\d+)\s*недел', text)
        if match:
            return int(match.group(1)) * 7
        return 7
    
    # Month patterns
    if 'месяц' in text:
        match = re.search(r'(\d+)\s*месяц', text)
        if match:
            return int(match.group(1)) * 30
        return 30
    
    # Day patterns
    if 'день' in text or 'дней' in text:
        match = re.search(r'(\d+)\s*ден', text)
        if match:
            return int(match.group(1))
        return 1
    
    return None
