"""
Prometheus Metrics for Application Monitoring
"""

from typing import Dict, Callable
from functools import wraps
import time


class PrometheusMetrics:
    """
    Prometheus-style metrics collector
    """
    
    def __init__(self):
        self.counters: Dict[str, int] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, list] = {}
    
    def increment_counter(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        """Increment a counter metric"""
        key = self._make_key(name, labels)
        self.counters[key] = self.counters.get(key, 0) + value
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric"""
        key = self._make_key(name, labels)
        self.gauges[key] = value
    
    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Add observation to histogram"""
        key = self._make_key(name, labels)
        if key not in self.histograms:
            self.histograms[key] = []
        self.histograms[key].append(value)
    
    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Create metric key with labels"""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def get_metrics_text(self) -> str:
        """Generate Prometheus text format"""
        lines = []
        
        # Counters
        for key, value in self.counters.items():
            lines.append(f"{key} {value}")
        
        # Gauges
        for key, value in self.gauges.items():
            lines.append(f"{key} {value}")
        
        # Histograms (simplified - just count and sum)
        for key, values in self.histograms.items():
            lines.append(f"{key}_count {len(values)}")
            lines.append(f"{key}_sum {sum(values)}")
        
        return "\n".join(lines)


# Global metrics instance
metrics = PrometheusMetrics()


def track_request_duration(endpoint: str):
    """
    Decorator to track request duration
    
    Args:
        endpoint: Endpoint name for labeling
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                status = "success"
                return result
            except Exception as e:
                status = "error"
                raise e
            finally:
                duration = (time.time() - start_time) * 1000  # ms
                metrics.observe_histogram(
                    "http_request_duration_ms",
                    duration,
                    labels={"endpoint": endpoint, "status": status}
                )
                metrics.increment_counter(
                    "http_requests_total",
                    labels={"endpoint": endpoint, "status": status}
                )
        return wrapper
    return decorator


def track_scan_metrics(project_id: str, file_count: int, risk_score: float, duration_ms: float):
    """
    Track code scan metrics
    
    Args:
        project_id: Project identifier
        file_count: Number of files scanned
        risk_score: Overall risk score
        duration_ms: Scan duration in milliseconds
    """
    metrics.increment_counter("scans_total", labels={"project_id": project_id})
    metrics.set_gauge("scan_file_count", file_count, labels={"project_id": project_id})
    metrics.set_gauge("scan_risk_score", risk_score, labels={"project_id": project_id})
    metrics.observe_histogram("scan_duration_ms", duration_ms, labels={"project_id": project_id})


def track_ml_inference(model_name: str, duration_ms: float, success: bool):
    """
    Track ML model inference metrics
    
    Args:
        model_name: Name of ML model
        duration_ms: Inference duration in milliseconds
        success: Whether inference succeeded
    """
    status = "success" if success else "error"
    metrics.increment_counter("ml_inferences_total", labels={"model": model_name, "status": status})
    metrics.observe_histogram("ml_inference_duration_ms", duration_ms, labels={"model": model_name})


def track_cache_hit(cache_key: str, hit: bool):
    """
    Track cache hit/miss metrics
    
    Args:
        cache_key: Cache key prefix
        hit: Whether cache hit occurred
    """
    status = "hit" if hit else "miss"
    metrics.increment_counter("cache_operations_total", labels={"key_prefix": cache_key, "status": status})


def track_database_query(operation: str, duration_ms: float):
    """
    Track database query metrics
    
    Args:
        operation: Database operation (find, insert, update, delete)
        duration_ms: Query duration in milliseconds
    """
    metrics.increment_counter("db_queries_total", labels={"operation": operation})
    metrics.observe_histogram("db_query_duration_ms", duration_ms, labels={"operation": operation})
