# Performance Benchmarking Script

import time
import statistics
import requests
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict


class PerformanceBenchmark:
    """Performance testing for Bug-Risk-NLP API"""
    
    def __init__(self, api_base: str = "http://localhost:8000"):
        self.api_base = api_base
        self.results: List[Dict] = []
    
    def benchmark_endpoint(self, name: str, method: str, url: str, 
                          iterations: int = 100, **kwargs) -> Dict:
        """Benchmark a single endpoint"""
        print(f"Benchmarking {name}...")
        times = []
        errors = 0
        
        for i in range(iterations):
            start = time.time()
            try:
                if method == "GET":
                    response = requests.get(url, **kwargs)
                elif method == "POST":
                    response = requests.post(url, **kwargs)
                
                response.raise_for_status()
                duration = (time.time() - start) * 1000  # ms
                times.append(duration)
            except Exception as e:
                errors += 1
                times.append(0)
        
        # Calculate statistics
        valid_times = [t for t in times if t > 0]
        
        result = {
            "name": name,
            "iterations": iterations,
            "errors": errors,
            "avg_ms": statistics.mean(valid_times) if valid_times else 0,
            "median_ms": statistics.median(valid_times) if valid_times else 0,
            "min_ms": min(valid_times) if valid_times else 0,
            "max_ms": max(valid_times) if valid_times else 0,
            "p95_ms": statistics.quantiles(valid_times, n=20)[18] if valid_times else 0,
            "p99_ms": statistics.quantiles(valid_times, n=100)[98] if valid_times else 0,
        }
        
        self.results.append(result)
        return result
    
    def benchmark_concurrent(self, name: str, method: str, url: str,
                            concurrent_users: int = 10, requests_per_user: int = 10,
                            **kwargs) -> Dict:
        """Benchmark with concurrent users"""
        print(f"Benchmarking {name} with {concurrent_users} concurrent users...")
        
        def make_request():
            start = time.time()
            try:
                if method == "GET":
                    response = requests.get(url, **kwargs)
                else:
                    response = requests.post(url, **kwargs)
                response.raise_for_status()
                return (time.time() - start) * 1000
            except:
                return 0
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            times = list(executor.map(
                lambda _: make_request(),
                range(concurrent_users * requests_per_user)
            ))
        
        total_time = time.time() - start_time
        valid_times = [t for t in times if t > 0]
        
        result = {
            "name": name,
            "concurrent_users": concurrent_users,
            "total_requests": concurrent_users * requests_per_user,
            "successful": len(valid_times),
            "failed": len(times) - len(valid_times),
            "total_time_s": total_time,
            "requests_per_sec": len(valid_times) / total_time if total_time > 0 else 0,
            "avg_response_ms": statistics.mean(valid_times) if valid_times else 0,
            "p95_ms": statistics.quantiles(valid_times, n=20)[18] if valid_times else 0,
        }
        
        self.results.append(result)
        return result
    
    def print_results(self):
        """Print benchmark results"""
        print("\n=== Performance Benchmark Results ===\n")
        
        for result in self.results:
            print(f"{result['name']}:")
            if 'concurrent_users' in result:
                print(f"  Concurrent Users: {result['concurrent_users']}")
                print(f"  Total Requests: {result['total_requests']}")
                print(f"  Successful: {result['successful']}")
                print(f"  Failed: {result['failed']}")
                print(f"  Requests/sec: {result['requests_per_sec']:.2f}")
                print(f"  Avg Response: {result['avg_response_ms']:.2f}ms")
                print(f"  P95 Response: {result['p95_ms']:.2f}ms")
            else:
                print(f"  Iterations: {result['iterations']}")
                print(f"  Errors: {result['errors']}")
                print(f"  Avg: {result['avg_ms']:.2f}ms")
                print(f"  Median: {result['median_ms']:.2f}ms")
                print(f"  Min: {result['min_ms']:.2f}ms")
                print(f"  Max: {result['max_ms']:.2f}ms")
                print(f"  P95: {result['p95_ms']:.2f}ms")
                print(f"  P99: {result['p99_ms']:.2f}ms")
            print()
    
    def run_all_benchmarks(self):
        """Run all performance benchmarks"""
        # 1. Health check
        self.benchmark_endpoint(
            "Health Check",
            "GET",
            f"{self.api_base}/health",
            iterations=1000
        )
        
        # 2. Search endpoint
        self.benchmark_endpoint(
            "Search API",
            "POST",
            f"{self.api_base}/search/test_project",
            iterations=100,
            json={"query": "test", "filters": {}}
        )
        
        # 3. Security scan
        self.benchmark_endpoint(
            "Security Score",
            "GET",
            f"{self.api_base}/security/test_project/score",
            iterations=100
        )
        
        # 4. Analytics
        self.benchmark_endpoint(
            "Analytics",
            "GET",
            f"{self.api_base}/analytics/test_project/productivity",
            iterations=50
        )
        
        # 5. Concurrent load test
        self.benchmark_concurrent(
            "Concurrent Search",
            "POST",
            f"{self.api_base}/search/test_project",
            concurrent_users=20,
            requests_per_user=10,
            json={"query": "test", "filters": {}}
        )
        
        # 6. Concurrent analytics
        self.benchmark_concurrent(
            "Concurrent Analytics",
            "GET",
            f"{self.api_base}/analytics/test_project/productivity",
            concurrent_users=10,
            requests_per_user=10
        )
        
        self.print_results()
        
        # Performance goals
        print("=== Performance Goals ===")
        search_result = next(r for r in self.results if r['name'] == 'Search API')
        print(f"Search P95 < 500ms: {'✓' if search_result['p95_ms'] < 500 else '✗'}")
        
        concurrent_result = next(r for r in self.results if r['name'] == 'Concurrent Search')
        print(f"Concurrent throughput > 50 req/s: {'✓' if concurrent_result['requests_per_sec'] > 50 else '✗'}")
        
        health_result = next(r for r in self.results if r['name'] == 'Health Check')
        print(f"Health check P99 < 50ms: {'✓' if health_result['p99_ms'] < 50 else '✗'}")


if __name__ == "__main__":
    benchmark = PerformanceBenchmark("http://localhost:8000")
    benchmark.run_all_benchmarks()
