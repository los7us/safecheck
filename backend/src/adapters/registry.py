"""
Adapter Registry

Central registry for all platform adapters. This enables:
1. Automatic adapter selection based on URL
2. Dynamic adapter loading
3. Adapter health monitoring
"""

from typing import Dict, Optional
from src.adapters.base_adapter import PlatformAdapter
from src.core.schemas import PlatformName


class AdapterRegistry:
    """Registry for platform adapters"""
    
    def __init__(self):
        self._adapters: Dict[PlatformName, PlatformAdapter] = {}
    
    def register(self, adapter: PlatformAdapter) -> None:
        """
        Register a platform adapter.
        
        Args:
            adapter: Initialized adapter instance
        """
        platform = adapter.platform_name
        self._adapters[platform] = adapter
        print(f"Registered adapter for {platform.value}")
    
    def get_adapter_for_url(self, url: str) -> Optional[PlatformAdapter]:
        """
        Find the appropriate adapter for a given URL.
        
        Args:
            url: URL to match
        
        Returns:
            Matching adapter or None
        """
        for adapter in self._adapters.values():
            if adapter.can_handle(url):
                return adapter
        return None
    
    def get_adapter(self, platform: PlatformName) -> Optional[PlatformAdapter]:
        """
        Get adapter by platform name.
        
        Args:
            platform: Platform name
        
        Returns:
            Adapter or None
        """
        return self._adapters.get(platform)
    
    def list_platforms(self) -> list[PlatformName]:
        """Return list of supported platforms"""
        return list(self._adapters.keys())
    
    async def health_check_all(self) -> Dict[PlatformName, bool]:
        """
        Check health of all registered adapters.
        
        Returns:
            Dict mapping platform to health status
        """
        results = {}
        for platform, adapter in self._adapters.items():
            try:
                results[platform] = await adapter.health_check()
            except Exception:
                results[platform] = False
        return results


# Global registry instance
adapter_registry = AdapterRegistry()
