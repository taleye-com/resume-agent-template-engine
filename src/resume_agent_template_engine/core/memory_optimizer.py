import gc
import sys
import threading
import time
import weakref
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
import logging
from dataclasses import dataclass
from collections import defaultdict, OrderedDict
import psutil
import os

logger = logging.getLogger(__name__)


@dataclass
class MemoryStats:
    """Memory statistics"""

    total_memory: int
    available_memory: int
    used_memory: int
    memory_percent: float
    process_memory: int
    cache_size: int


class LRUCache:
    """Simple LRU cache implementation for DRY principles"""

    def __init__(self, max_size: int = 1000):
        """Initialize LRU cache"""
        self.max_size = max_size
        self.cache = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> Any:
        """Get item from cache"""
        with self._lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                return self.cache[key]
        return None

    def put(self, key: str, value: Any) -> None:
        """Put item in cache"""
        with self._lock:
            if key in self.cache:
                # Update existing item
                self.cache[key] = value
                self.cache.move_to_end(key)
            else:
                # Add new item
                self.cache[key] = value
                if len(self.cache) > self.max_size:
                    # Remove least recently used
                    self.cache.popitem(last=False)

    def clear(self) -> None:
        """Clear cache"""
        with self._lock:
            self.cache.clear()

    def size(self) -> int:
        """Get cache size"""
        return len(self.cache)


class MemoryPool:
    """Memory pool for reusing objects"""

    def __init__(self):
        """Initialize memory pool"""
        self.pools: Dict[type, List[Any]] = defaultdict(list)
        self._lock = threading.Lock()
        self.max_pool_size = 100

    def get_object(self, obj_type: type, *args, **kwargs) -> Any:
        """Get object from pool or create new"""
        with self._lock:
            pool = self.pools[obj_type]
            if pool:
                obj = pool.pop()
                # Reset object if it has a reset method
                if hasattr(obj, "reset"):
                    obj.reset(*args, **kwargs)
                return obj

        # Create new object
        return obj_type(*args, **kwargs)

    def return_object(self, obj: Any) -> None:
        """Return object to pool"""
        obj_type = type(obj)
        with self._lock:
            pool = self.pools[obj_type]
            if len(pool) < self.max_pool_size:
                pool.append(obj)

    def clear_pools(self) -> None:
        """Clear all pools"""
        with self._lock:
            for pool in self.pools.values():
                pool.clear()


class WeakReferenceManager:
    """Manages weak references to avoid memory leaks"""

    def __init__(self):
        """Initialize weak reference manager"""
        self.references: Dict[str, weakref.ref] = {}
        self._lock = threading.Lock()

    def add_reference(self, key: str, obj: Any) -> None:
        """Add weak reference"""

        def cleanup_callback(ref):
            with self._lock:
                if key in self.references and self.references[key] is ref:
                    del self.references[key]

        with self._lock:
            self.references[key] = weakref.ref(obj, cleanup_callback)

    def get_reference(self, key: str) -> Optional[Any]:
        """Get object from weak reference"""
        with self._lock:
            ref = self.references.get(key)
            if ref:
                obj = ref()
                if obj is None:
                    # Object was garbage collected
                    del self.references[key]
                return obj
        return None

    def cleanup_dead_references(self) -> int:
        """Clean up dead references"""
        dead_keys = []
        with self._lock:
            for key, ref in self.references.items():
                if ref() is None:
                    dead_keys.append(key)

            for key in dead_keys:
                del self.references[key]

        return len(dead_keys)


class MemoryMonitor:
    """Monitors memory usage and triggers cleanup"""

    def __init__(self, threshold_percent: float = 80.0):
        """Initialize memory monitor"""
        self.threshold_percent = threshold_percent
        self.running = False
        self.monitor_thread = None
        self.cleanup_callbacks: List[callable] = []
        self._lock = threading.Lock()

    def start_monitoring(self, interval: float = 30.0) -> None:
        """Start memory monitoring"""
        if self.running:
            return

        self.running = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, args=(interval,), daemon=True
        )
        self.monitor_thread.start()
        logger.info("Memory monitoring started")

    def stop_monitoring(self) -> None:
        """Stop memory monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Memory monitoring stopped")

    def add_cleanup_callback(self, callback: callable) -> None:
        """Add cleanup callback"""
        with self._lock:
            self.cleanup_callbacks.append(callback)

    def _monitor_loop(self, interval: float) -> None:
        """Memory monitoring loop"""
        while self.running:
            try:
                stats = self.get_memory_stats()

                if stats.memory_percent > self.threshold_percent:
                    logger.warning(f"Memory usage high: {stats.memory_percent:.1f}%")
                    self._trigger_cleanup()

                time.sleep(interval)

            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")
                time.sleep(interval)

    def _trigger_cleanup(self) -> None:
        """Trigger cleanup callbacks"""
        with self._lock:
            for callback in self.cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Cleanup callback error: {e}")

        # Force garbage collection
        gc.collect()

    def get_memory_stats(self) -> MemoryStats:
        """Get current memory statistics"""
        process = psutil.Process()
        memory_info = psutil.virtual_memory()

        return MemoryStats(
            total_memory=memory_info.total,
            available_memory=memory_info.available,
            used_memory=memory_info.used,
            memory_percent=memory_info.percent,
            process_memory=process.memory_info().rss,
            cache_size=0,  # Will be filled by cache systems
        )


class TemplateCache:
    """Optimized cache for compiled templates"""

    def __init__(self, max_size: int = 50, max_memory_mb: int = 100):
        """Initialize template cache"""
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache = LRUCache(max_size)
        self.memory_usage = 0
        self._lock = threading.Lock()

    def get_template(self, template_key: str) -> Optional[Any]:
        """Get cached template"""
        return self.cache.get(template_key)

    def cache_template(self, template_key: str, template_obj: Any) -> None:
        """Cache compiled template"""
        # Estimate memory usage
        obj_size = sys.getsizeof(template_obj)

        with self._lock:
            # Check if we need to make space
            if self.memory_usage + obj_size > self.max_memory_bytes:
                self._cleanup_memory()

            self.cache.put(template_key, template_obj)
            self.memory_usage += obj_size

    def _cleanup_memory(self) -> None:
        """Clean up memory by removing old items"""
        # Remove items until under memory limit
        target_memory = self.max_memory_bytes * 0.7  # Clean to 70% of limit

        while self.memory_usage > target_memory and self.cache.size() > 0:
            # Remove least recently used item
            with self.cache._lock:
                if self.cache.cache:
                    key, obj = self.cache.cache.popitem(last=False)
                    self.memory_usage -= sys.getsizeof(obj)

    def clear(self) -> None:
        """Clear cache"""
        with self._lock:
            self.cache.clear()
            self.memory_usage = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cached_templates": self.cache.size(),
            "memory_usage_mb": round(self.memory_usage / (1024 * 1024), 2),
            "memory_limit_mb": round(self.max_memory_bytes / (1024 * 1024), 2),
            "cache_hit_rate": 0.0,  # Would need hit/miss tracking
        }


class MemoryOptimizer:
    """Central memory optimization system"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize memory optimizer"""
        config = config or {}

        self.monitor = MemoryMonitor(
            threshold_percent=config.get("memory_threshold", 80.0)
        )
        self.template_cache = TemplateCache(
            max_size=config.get("template_cache_size", 50),
            max_memory_mb=config.get("template_cache_memory", 100),
        )
        self.memory_pool = MemoryPool()
        self.weak_refs = WeakReferenceManager()

        # Register cleanup callbacks
        self.monitor.add_cleanup_callback(self._cleanup_caches)
        self.monitor.add_cleanup_callback(self._cleanup_pools)
        self.monitor.add_cleanup_callback(self._cleanup_weak_refs)

        # Start monitoring
        if config.get("auto_monitor", True):
            self.monitor.start_monitoring(interval=config.get("monitor_interval", 30.0))

    def _cleanup_caches(self) -> None:
        """Clean up caches"""
        # Clear half of template cache
        with self.template_cache._lock:
            current_size = self.template_cache.cache.size()
            target_size = current_size // 2

            while self.template_cache.cache.size() > target_size:
                with self.template_cache.cache._lock:
                    if self.template_cache.cache.cache:
                        key, obj = self.template_cache.cache.cache.popitem(last=False)
                        self.template_cache.memory_usage -= sys.getsizeof(obj)

        logger.info("Cleaned template cache")

    def _cleanup_pools(self) -> None:
        """Clean up memory pools"""
        self.memory_pool.clear_pools()
        logger.info("Cleaned memory pools")

    def _cleanup_weak_refs(self) -> None:
        """Clean up weak references"""
        cleaned = self.weak_refs.cleanup_dead_references()
        logger.info(f"Cleaned {cleaned} dead weak references")

    def optimize_for_build(self, template_count: int) -> None:
        """Optimize memory for build process"""
        # Adjust cache sizes based on expected load
        if template_count > 10:
            # Large build, reduce cache sizes
            self.template_cache.max_size = min(20, template_count)
        else:
            # Small build, can use more cache
            self.template_cache.max_size = 50

        # Force cleanup before build
        self._cleanup_caches()
        gc.collect()

    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        memory_stats = self.monitor.get_memory_stats()
        cache_stats = self.template_cache.get_stats()

        return {
            "memory": {
                "total_mb": round(memory_stats.total_memory / (1024**2), 2),
                "available_mb": round(memory_stats.available_memory / (1024**2), 2),
                "process_mb": round(memory_stats.process_memory / (1024**2), 2),
                "percent_used": memory_stats.memory_percent,
            },
            "template_cache": cache_stats,
            "memory_pools": {
                "pool_types": len(self.memory_pool.pools),
                "total_objects": sum(
                    len(pool) for pool in self.memory_pool.pools.values()
                ),
            },
            "weak_references": len(self.weak_refs.references),
        }

    def shutdown(self) -> None:
        """Shutdown memory optimizer"""
        self.monitor.stop_monitoring()
        self.template_cache.clear()
        self.memory_pool.clear_pools()
        logger.info("Memory optimizer shutdown complete")


class StreamingDataProcessor:
    """Process large datasets in streaming fashion"""

    def __init__(self, chunk_size: int = 1000):
        """Initialize streaming processor"""
        self.chunk_size = chunk_size

    def process_batch_data(
        self, data_list: List[Dict[str, Any]], processor_func: callable
    ) -> List[Any]:
        """Process data in batches to avoid memory spikes"""
        results = []

        for i in range(0, len(data_list), self.chunk_size):
            chunk = data_list[i : i + self.chunk_size]

            # Process chunk
            chunk_results = []
            for item in chunk:
                try:
                    result = processor_func(item)
                    chunk_results.append(result)
                except Exception as e:
                    logger.warning(f"Failed to process item: {e}")

            results.extend(chunk_results)

            # Force garbage collection after each chunk
            gc.collect()

        return results

    def process_large_file(
        self, file_path: str, processor_func: callable, chunk_size: int = None
    ) -> None:
        """Process large files line by line"""
        chunk_size = chunk_size or self.chunk_size

        with open(file_path, "r", encoding="utf-8") as f:
            chunk = []

            for line in f:
                chunk.append(line.strip())

                if len(chunk) >= chunk_size:
                    try:
                        processor_func(chunk)
                    except Exception as e:
                        logger.error(f"Failed to process chunk: {e}")

                    chunk.clear()
                    gc.collect()

            # Process remaining items
            if chunk:
                try:
                    processor_func(chunk)
                except Exception as e:
                    logger.error(f"Failed to process final chunk: {e}")


def memory_efficient_decorator(func):
    """Decorator for memory-efficient function execution"""

    def wrapper(*args, **kwargs):
        # Force garbage collection before execution
        gc.collect()

        try:
            result = func(*args, **kwargs)
            return result
        finally:
            # Force garbage collection after execution
            gc.collect()

    return wrapper
