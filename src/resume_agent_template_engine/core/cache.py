"""
Caching module for resume template engine.
Provides Redis-based caching for compiled PDFs and LaTeX content.
"""

import hashlib
import json
import logging
import os
from typing import Any, Dict, Optional
from datetime import timedelta

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

logger = logging.getLogger(__name__)


class CacheConfig:
    """Configuration for cache settings."""

    def __init__(self):
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_db = int(os.getenv("REDIS_DB", "0"))
        self.redis_password = os.getenv("REDIS_PASSWORD", None)
        self.redis_ssl = os.getenv("REDIS_SSL", "false").lower() == "true"
        self.cache_enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"
        self.pdf_cache_ttl = int(os.getenv("PDF_CACHE_TTL", str(60 * 60 * 24)))  # 24 hours
        self.latex_cache_ttl = int(os.getenv("LATEX_CACHE_TTL", str(60 * 60 * 12)))  # 12 hours
        self.max_connections = int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))


class DocumentCache:
    """
    Redis-based caching for compiled documents.

    Features:
    - PDF binary caching with TTL
    - LaTeX content caching
    - Cache key generation based on content hash
    - Connection pooling for performance
    - Async/await support
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        """Initialize document cache with configuration."""
        self.config = config or CacheConfig()
        self._pool: Optional[ConnectionPool] = None
        self._redis: Optional[redis.Redis] = None
        self._metrics = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "sets": 0
        }

    async def initialize(self):
        """Initialize Redis connection pool."""
        if not self.config.cache_enabled:
            logger.info("Caching is disabled")
            return

        try:
            # Build connection pool kwargs (ssl only if enabled)
            pool_kwargs = {
                "host": self.config.redis_host,
                "port": self.config.redis_port,
                "db": self.config.redis_db,
                "max_connections": self.config.max_connections,
                "decode_responses": False  # We need binary data for PDFs
            }

            if self.config.redis_password:
                pool_kwargs["password"] = self.config.redis_password

            self._pool = ConnectionPool(**pool_kwargs)
            self._redis = redis.Redis(connection_pool=self._pool)

            # Test connection
            await self._redis.ping()
            logger.info(
                f"Redis cache initialized: {self.config.redis_host}:{self.config.redis_port}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {e}")
            self._redis = None

    async def close(self):
        """Close Redis connection pool."""
        if self._redis:
            await self._redis.close()
            await self._pool.disconnect()
            logger.info("Redis cache connection closed")

    def _generate_cache_key(
        self,
        data: Dict[str, Any],
        template_name: str,
        document_type: str,
        output_format: str,
        spacing: str = "normal",
        prefix: str = "doc"
    ) -> str:
        """
        Generate deterministic cache key from document parameters.

        Args:
            data: Resume/cover letter data
            template_name: Template identifier
            document_type: "resume" or "cover_letter"
            output_format: "pdf", "latex", "docx"
            spacing: Layout spacing mode
            prefix: Cache key prefix

        Returns:
            Cache key string
        """
        # Create deterministic hash of input parameters
        cache_data = {
            "data": data,
            "template": template_name,
            "type": document_type,
            "format": output_format,
            "spacing": spacing,
            "version": "v1"  # Increment to invalidate cache on schema changes
        }

        # Sort keys for deterministic JSON
        json_str = json.dumps(cache_data, sort_keys=True, default=str)
        hash_digest = hashlib.sha256(json_str.encode()).hexdigest()

        return f"{prefix}:{document_type}:{output_format}:{hash_digest[:16]}"

    async def get_pdf(
        self,
        data: Dict[str, Any],
        template_name: str,
        document_type: str,
        spacing: str = "normal"
    ) -> Optional[bytes]:
        """
        Get cached PDF document.

        Returns:
            PDF bytes if cached, None if not found
        """
        if not self._redis or not self.config.cache_enabled:
            return None

        try:
            cache_key = self._generate_cache_key(
                data, template_name, document_type, "pdf", spacing, prefix="pdf"
            )

            pdf_bytes = await self._redis.get(cache_key)

            if pdf_bytes:
                self._metrics["hits"] += 1
                logger.debug(f"Cache HIT: {cache_key}")
                return pdf_bytes
            else:
                self._metrics["misses"] += 1
                logger.debug(f"Cache MISS: {cache_key}")
                return None

        except Exception as e:
            self._metrics["errors"] += 1
            logger.error(f"Cache get error: {e}")
            return None

    async def set_pdf(
        self,
        data: Dict[str, Any],
        template_name: str,
        document_type: str,
        pdf_bytes: bytes,
        spacing: str = "normal"
    ) -> bool:
        """
        Cache compiled PDF document.

        Returns:
            True if cached successfully, False otherwise
        """
        if not self._redis or not self.config.cache_enabled:
            return False

        try:
            cache_key = self._generate_cache_key(
                data, template_name, document_type, "pdf", spacing, prefix="pdf"
            )

            await self._redis.setex(
                cache_key,
                timedelta(seconds=self.config.pdf_cache_ttl),
                pdf_bytes
            )

            self._metrics["sets"] += 1
            logger.debug(f"Cache SET: {cache_key} ({len(pdf_bytes)} bytes)")
            return True

        except Exception as e:
            self._metrics["errors"] += 1
            logger.error(f"Cache set error: {e}")
            return False

    async def get_latex(
        self,
        data: Dict[str, Any],
        template_name: str,
        document_type: str,
        spacing: str = "normal"
    ) -> Optional[str]:
        """
        Get cached LaTeX content.

        Returns:
            LaTeX string if cached, None if not found
        """
        if not self._redis or not self.config.cache_enabled:
            return None

        try:
            cache_key = self._generate_cache_key(
                data, template_name, document_type, "latex", spacing, prefix="latex"
            )

            latex_bytes = await self._redis.get(cache_key)

            if latex_bytes:
                self._metrics["hits"] += 1
                logger.debug(f"Cache HIT: {cache_key}")
                return latex_bytes.decode('utf-8')
            else:
                self._metrics["misses"] += 1
                logger.debug(f"Cache MISS: {cache_key}")
                return None

        except Exception as e:
            self._metrics["errors"] += 1
            logger.error(f"Cache get error: {e}")
            return None

    async def set_latex(
        self,
        data: Dict[str, Any],
        template_name: str,
        document_type: str,
        latex_content: str,
        spacing: str = "normal"
    ) -> bool:
        """
        Cache generated LaTeX content.

        Returns:
            True if cached successfully, False otherwise
        """
        if not self._redis or not self.config.cache_enabled:
            return False

        try:
            cache_key = self._generate_cache_key(
                data, template_name, document_type, "latex", spacing, prefix="latex"
            )

            await self._redis.setex(
                cache_key,
                timedelta(seconds=self.config.latex_cache_ttl),
                latex_content.encode('utf-8')
            )

            self._metrics["sets"] += 1
            logger.debug(f"Cache SET: {cache_key} ({len(latex_content)} chars)")
            return True

        except Exception as e:
            self._metrics["errors"] += 1
            logger.error(f"Cache set error: {e}")
            return False

    async def invalidate_document(
        self,
        data: Dict[str, Any],
        template_name: str,
        document_type: str,
        spacing: str = "normal"
    ) -> int:
        """
        Invalidate all cached versions of a document.

        Returns:
            Number of keys deleted
        """
        if not self._redis or not self.config.cache_enabled:
            return 0

        try:
            keys_to_delete = []

            for output_format in ["pdf", "latex", "docx"]:
                cache_key = self._generate_cache_key(
                    data, template_name, document_type, output_format, spacing,
                    prefix=output_format
                )
                keys_to_delete.append(cache_key)

            deleted = await self._redis.delete(*keys_to_delete)
            logger.info(f"Invalidated {deleted} cache entries")
            return deleted

        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return 0

    async def clear_all(self) -> bool:
        """
        Clear all cached documents (use with caution).

        Returns:
            True if successful, False otherwise
        """
        if not self._redis or not self.config.cache_enabled:
            return False

        try:
            await self._redis.flushdb()
            logger.warning("All cache entries cleared")
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get cache performance metrics.

        Returns:
            Dictionary with hits, misses, hit rate, errors
        """
        total_requests = self._metrics["hits"] + self._metrics["misses"]
        hit_rate = (
            self._metrics["hits"] / total_requests * 100
            if total_requests > 0
            else 0
        )

        return {
            "hits": self._metrics["hits"],
            "misses": self._metrics["misses"],
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "errors": self._metrics["errors"],
            "sets": self._metrics["sets"],
            "enabled": self.config.cache_enabled,
            "connected": self._redis is not None
        }

    def reset_metrics(self):
        """Reset metrics counters."""
        self._metrics = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "sets": 0
        }


# Global cache instance
_cache_instance: Optional[DocumentCache] = None


async def get_cache() -> DocumentCache:
    """
    Get or create global cache instance.

    Returns:
        DocumentCache instance
    """
    global _cache_instance

    if _cache_instance is None:
        _cache_instance = DocumentCache()
        await _cache_instance.initialize()

    return _cache_instance


async def close_cache():
    """Close global cache instance."""
    global _cache_instance

    if _cache_instance:
        await _cache_instance.close()
        _cache_instance = None
