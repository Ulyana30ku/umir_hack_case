"""Safety Layer - Security guardrails for browser automation."""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from app.mcp.models import SafetyConfig, ExecutionContext
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SafetyResult:
    """Result of safety check."""
    allowed: bool
    reason: Optional[str] = None


class SafetyLayer:
    """
    Security guardrails for browser automation.
    
    Implements:
    - Domain allowlist
    - Action denylist
    - Step limits
    - Dangerous action detection
    """
    
    def __init__(self, config: SafetyConfig):
        """
        Initialize safety layer.
        
        Args:
            config: Safety configuration
        """
        self.config = config
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Compile regex patterns for URL checking."""
        # Compile domain patterns
        self._domain_patterns = []
        for domain in self.config.domain_allowlist:
            # Escape dots and convert * to regex
            pattern = domain.replace(".", r"\.").replace("*", ".*")
            self._domain_patterns.append(re.compile(pattern))
    
    async def check(
        self,
        tool_name: str,
        input_data: Dict[str, Any],
        context: ExecutionContext,
    ) -> SafetyResult:
        """
        Check if action is allowed.
        
        Args:
            tool_name: Name of tool to execute
            input_data: Input data for tool
            context: Execution context
            
        Returns:
            SafetyResult with allowed status and reason
        """
        # 1. Check tool in denylist
        if tool_name in self.config.action_denylist:
            return SafetyResult(
                allowed=False,
                reason=f"Tool '{tool_name}' is blocked for security"
            )
        
        # 2. Check URL in allowlist (for navigation tools)
        if "url" in input_data:
            url = input_data["url"]
            if not self._is_url_allowed(url):
                return SafetyResult(
                    allowed=False,
                    reason=f"URL '{url}' not in domain allowlist"
                )
        
        # 3. Check step limit
        if context.step_count >= self.config.max_steps_per_run:
            return SafetyResult(
                allowed=False,
                reason=f"Maximum steps ({self.config.max_steps_per_run}) exceeded"
            )
        
        # 4. Check dangerous actions in input
        dangerous_check = self._check_dangerous_input(tool_name, input_data)
        if not dangerous_check.allowed:
            return dangerous_check
        
        # 5. Check for suspicious patterns
        suspicious = self._check_suspicious_patterns(tool_name, input_data)
        if not suspicious.allowed:
            return suspicious
        
        return SafetyResult(allowed=True)
    
    def _is_url_allowed(self, url: str) -> bool:
        """
        Check URL against allowlist.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL is allowed
        """
        # Empty allowlist = allow all
        if not self.config.domain_allowlist:
            return True
        
        # Check each domain pattern
        for pattern in self._domain_patterns:
            if pattern.search(url):
                return True
        
        return False
    
    def _check_dangerous_input(
        self,
        tool_name: str,
        input_data: Dict[str, Any],
    ) -> SafetyResult:
        """Check for dangerous input patterns."""
        dangerous_keys = [
            "eval",
            "exec", 
            "__import__",
            "innerHTML",
            "outerHTML",
        ]
        
        # Check for JavaScript execution attempts
        if tool_name in ["browser.type", "browser.click"]:
            # Check if input contains suspicious patterns
            for key, value in input_data.items():
                if isinstance(value, str):
                    for danger in dangerous_keys:
                        if danger in value.lower():
                            return SafetyResult(
                                allowed=False,
                                reason=f"Potentially dangerous input detected: {danger}"
                            )
        
        return SafetyResult(allowed=True)
    
    def _check_suspicious_patterns(
        self,
        tool_name: str,
        input_data: Dict[str, Any],
    ) -> SafetyResult:
        """Check for suspicious patterns."""
        # Check for file download attempts
        if tool_name == "browser.download":
            return SafetyResult(
                allowed=False,
                reason="File downloads are disabled for security"
            )
        
        # Check for attempts to access local files
        if "url" in input_data:
            url = input_data["url"]
            if url.startswith("file://"):
                return SafetyResult(
                    allowed=False,
                    reason="Local file access is disabled"
                )
        
        # Check for attempts to access system URLs
        if "url" in input_data:
            url = input_data["url"]
            system_urls = ["chrome://", "about:", "edge://"]
            if any(url.startswith(s) for s in system_urls):
                return SafetyResult(
                    allowed=False,
                    reason="System URLs are blocked"
                )
        
        return SafetyResult(allowed=True)
    
    def is_domain_allowed(self, domain: str) -> bool:
        """Check if domain is in allowlist."""
        return self._is_url_allowed(domain)
    
    def get_allowed_domains(self) -> List[str]:
        """Get list of allowed domains."""
        return self.config.domain_allowlist.copy()


class DomainAllowlist:
    """Domain allowlist manager."""
    
    def __init__(self, domains: Optional[List[str]] = None):
        """
        Initialize allowlist.
        
        Args:
            domains: List of allowed domains (None = allow all)
        """
        self.domains = domains or []
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Compile domain patterns."""
        self._patterns = []
        for domain in self.domains:
            pattern = domain.replace(".", r"\.").replace("*", ".*")
            self._patterns.append(re.compile(pattern))
    
    def is_allowed(self, url: str) -> bool:
        """Check if URL is allowed."""
        if not self.domains:
            return True
        
        for pattern in self._patterns:
            if pattern.search(url):
                return True
        
        return False
    
    def add_domain(self, domain: str) -> None:
        """Add domain to allowlist."""
        if domain not in self.domains:
            self.domains.append(domain)
            self._compile_patterns()
    
    def remove_domain(self, domain: str) -> bool:
        """Remove domain from allowlist."""
        if domain in self.domains:
            self.domains.remove(domain)
            self._compile_patterns()
            return True
        return False
