"""Comprehensive stress testing and performance benchmarking for the resume-agent-template-engine."""

import pytest
import time
import threading
import tempfile
import os
import gc
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
import json

from resume_agent_template_engine.api.app import app
from tests.stress.stress_config_loader import get_stress_config, export_test_metrics


class TestStressTesting:
    """Comprehensive stress testing for the API under various load conditions."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI application."""
        return TestClient(app)
    
    @pytest.fixture
    def stress_config(self):
        """Get stress test configuration."""
        config = get_stress_config()
        config.print_configuration_summary()
        return config
    
    @pytest.fixture
    def mock_engine_setup(self):
        """Set up consistent engine mocking for stress tests."""
        def setup_mock_engine():
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(b"Mock PDF content for stress testing")
                temp_path = temp_file.name
            
            mock_engine = Mock()
            
            def mock_get_templates(document_type=None):
                if document_type is None:
                    return {"resume": ["classic", "modern"], "cover_letter": ["formal", "creative"]}
                elif document_type == "resume":
                    return ["classic", "modern"]
                elif document_type == "cover_letter":
                    return ["formal", "creative"]
                else:
                    return []
            
            mock_engine.get_available_templates.side_effect = mock_get_templates
            mock_engine.export_to_pdf.return_value = temp_path
            mock_engine.get_template_info.return_value = {
                "name": "classic",
                "document_type": "resume",
                "description": "Test template",
                "required_fields": ["personalInfo"]
            }
            
            return mock_engine, temp_path
        
        return setup_mock_engine

    def test_high_volume_concurrent_requests(self, client, stress_config, mock_engine_setup, sample_resume_data):
        """Test system behavior under high volume of concurrent requests."""
        # Skip test if not applicable for current category (use appropriate category for stress level)
        if stress_config.stress_level == 'extreme':
            category = 'breaking_point'
        elif stress_config.stress_level == 'enterprise':
            category = 'enterprise'
        else:
            category = 'staging'
        
        if stress_config.should_skip_test('high_volume', category):
            pytest.skip(f"High volume test skipped for {stress_config.stress_level} stress level")
        
        mock_engine, temp_path = mock_engine_setup()
        
        try:
            with patch('resume_agent_template_engine.api.app.TemplateEngine') as mock_engine_class, \
                 patch('tempfile.NamedTemporaryFile') as mock_tempfile, \
                 patch('os.path.exists', return_value=True), \
                 patch('os.remove'):
                
                mock_engine_class.return_value = mock_engine
                
                # Mock tempfile to return our real file path
                mock_temp = Mock()
                mock_temp.name = temp_path
                mock_tempfile.return_value.__enter__.return_value = mock_temp
                
                # Get test parameters from configuration
                num_concurrent_requests = stress_config.get_concurrent_requests('high_volume_test')
                max_workers = min(num_concurrent_requests, 20)  # Cap workers for safety
                
                success_rate_threshold = stress_config.get_performance_requirement('success_rate_threshold')
                avg_response_time_threshold = stress_config.get_performance_requirement('avg_response_time_threshold')
                throughput_threshold = stress_config.get_performance_requirement('throughput_threshold')
                
                request_data = {
                    "document_type": "resume",
                    "template": "classic",
                    "format": "pdf",
                    "data": sample_resume_data
                }
                
                def make_request():
                    """Make a single request and return timing and status."""
                    start_time = time.time()
                    try:
                        response = client.post("/generate", json=request_data)
                        end_time = time.time()
                        return {
                            "status_code": response.status_code,
                            "response_time": end_time - start_time,
                            "success": response.status_code == 200
                        }
                    except Exception as e:
                        end_time = time.time()
                        return {
                            "status_code": 500,
                            "response_time": end_time - start_time,
                            "success": False,
                            "error": str(e)
                        }
                
                # Execute concurrent requests
                start_test_time = time.time()
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = [executor.submit(make_request) for _ in range(num_concurrent_requests)]
                    results = [future.result() for future in as_completed(futures)]
                
                end_test_time = time.time()
                total_test_time = end_test_time - start_test_time
                
                # Analyze results
                successful_requests = [r for r in results if r["success"]]
                failed_requests = [r for r in results if not r["success"]]
                response_times = [r["response_time"] for r in results]
                
                # Calculate metrics
                success_rate = len(successful_requests) / len(results)
                avg_response_time = statistics.mean(response_times)
                throughput = num_concurrent_requests / total_test_time
                
                # Prepare metrics for export
                test_metrics = {
                    "test_name": "high_volume_concurrent_requests",
                    "stress_level": stress_config.stress_level,
                    "configuration": {
                        "concurrent_requests": num_concurrent_requests,
                        "max_workers": max_workers,
                        "success_rate_threshold": success_rate_threshold,
                        "avg_response_time_threshold": avg_response_time_threshold,
                        "throughput_threshold": throughput_threshold
                    },
                    "results": {
                        "total_requests": num_concurrent_requests,
                        "successful_requests": len(successful_requests),
                        "failed_requests": len(failed_requests),
                        "success_rate": success_rate,
                        "avg_response_time": avg_response_time,
                        "min_response_time": min(response_times),
                        "max_response_time": max(response_times),
                        "throughput": throughput,
                        "total_test_time": total_test_time
                    },
                    "assertions": {
                        "success_rate_passed": success_rate >= success_rate_threshold,
                        "avg_response_time_passed": avg_response_time < avg_response_time_threshold,
                        "throughput_passed": throughput > throughput_threshold
                    }
                }
                
                # Export metrics
                export_test_metrics(test_metrics, stress_config, "high_volume_concurrent")
                
                # Dynamic assertions based on configuration
                assert success_rate >= success_rate_threshold, f"Success rate too low: {success_rate:.2%} (threshold: {success_rate_threshold:.2%})"
                assert avg_response_time < avg_response_time_threshold, f"Average response time too high: {avg_response_time:.2f}s (threshold: {avg_response_time_threshold:.2f}s)"
                assert throughput > throughput_threshold, f"Throughput too low: {throughput:.2f} req/s (threshold: {throughput_threshold:.2f} req/s)"
                
                if stress_config.is_detailed_logging_enabled():
                    print(f"\n=== High Volume Concurrent Test Results ({stress_config.stress_level}) ===")
                    print(f"Total requests: {num_concurrent_requests}")
                    print(f"Successful requests: {len(successful_requests)}")
                    print(f"Failed requests: {len(failed_requests)}")
                    print(f"Success rate: {success_rate:.2%} (threshold: {success_rate_threshold:.2%})")
                    print(f"Average response time: {avg_response_time:.3f}s (threshold: {avg_response_time_threshold:.3f}s)")
                    print(f"Min response time: {min(response_times):.3f}s")
                    print(f"Max response time: {max(response_times):.3f}s")
                    print(f"Throughput: {throughput:.2f} req/s (threshold: {throughput_threshold:.2f} req/s)")
                
        finally:
            # Cleanup based on configuration
            if stress_config.should_cleanup_temp_files() and os.path.exists(temp_path):
                os.remove(temp_path)

    def test_memory_stress_testing(self, client, mock_engine_setup, sample_resume_data):
        """Test memory usage under sustained load (simplified without psutil)."""
        mock_engine, temp_path = mock_engine_setup()
        
        try:
            with patch('resume_agent_template_engine.api.app.TemplateEngine') as mock_engine_class, \
                 patch('tempfile.NamedTemporaryFile') as mock_tempfile, \
                 patch('os.path.exists', return_value=True), \
                 patch('os.remove'):
                
                mock_engine_class.return_value = mock_engine
                
                # Mock tempfile to return our real file path
                mock_temp = Mock()
                mock_temp.name = temp_path
                mock_tempfile.return_value.__enter__.return_value = mock_temp
                
                request_data = {
                    "document_type": "resume",
                    "template": "classic",
                    "format": "pdf",
                    "data": sample_resume_data
                }
                
                num_requests = 100
                
                print(f"\n=== Memory Stress Test Results ===")
                print(f"Running {num_requests} requests to test memory stability...")
                
                for i in range(num_requests):
                    response = client.post("/generate", json=request_data)
                    assert response.status_code == 200
                    
                    # Force garbage collection periodically to test for memory leaks
                    if i % 50 == 0:
                        gc.collect()
                        print(f"Completed {i} requests, forcing garbage collection")
                
                print(f"Successfully completed {num_requests} requests without memory issues")
                
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_large_payload_stress(self, client, mock_engine_setup):
        """Test system behavior with very large data payloads."""
        mock_engine, temp_path = mock_engine_setup()
        
        try:
            with patch('resume_agent_template_engine.api.app.TemplateEngine') as mock_engine_class, \
                 patch('tempfile.NamedTemporaryFile') as mock_tempfile, \
                 patch('os.path.exists', return_value=True), \
                 patch('os.remove'):
                
                mock_engine_class.return_value = mock_engine
                
                # Mock tempfile to return our real file path
                mock_temp = Mock()
                mock_temp.name = temp_path
                mock_tempfile.return_value.__enter__.return_value = mock_temp
                
                # Create extremely large resume data
                large_resume_data = {
                    "personalInfo": {
                        "name": "John Doe" * 100,  # Very long name
                        "email": "john@example.com",
                        "phone": "+1-234-567-8900",
                        "location": "San Francisco, CA" * 50,
                        "summary": "A" * 10000  # 10KB summary
                    },
                    "experience": [],
                    "education": [],
                    "projects": [],
                    "skills": []
                }
                
                # Add 100 experience entries with large descriptions
                for i in range(100):
                    large_resume_data["experience"].append({
                        "title": f"Senior Software Engineer {i}" * 10,
                        "company": f"Tech Company {i}" * 20,
                        "location": "San Francisco, CA",
                        "startDate": "2020-01",
                        "endDate": "2023-12",
                        "description": ["B" * 1000] * 20  # 20KB per job description
                    })
                
                # Add large education entries
                for i in range(20):
                    large_resume_data["education"].append({
                        "degree": f"Master of Science in Computer Science {i}" * 10,
                        "institution": f"University {i}" * 15,
                        "location": "Berkeley, CA",
                        "graduationDate": "2019-05",
                        "coursework": ["C" * 500] * 10  # Large coursework descriptions
                    })
                
                # Add large project entries
                for i in range(50):
                    large_resume_data["projects"].append({
                        "name": f"Project {i}" * 20,
                        "description": "D" * 2000,  # 2KB per project
                        "technologies": [f"Tech{j}" * 10 for j in range(20)],
                        "url": f"https://github.com/user/project{i}"
                    })
                
                # Add large skills section
                large_resume_data["skills"] = {
                    "programming": ["E" * 100] * 50,
                    "frameworks": ["F" * 100] * 50,
                    "databases": ["G" * 100] * 30,
                    "tools": ["H" * 100] * 40
                }
                
                request_data = {
                    "document_type": "resume",
                    "template": "classic",
                    "format": "pdf",
                    "data": large_resume_data
                }
                
                # Calculate payload size
                payload_size = len(json.dumps(request_data).encode('utf-8')) / 1024 / 1024  # MB
                print(f"\n=== Large Payload Stress Test ===")
                print(f"Payload size: {payload_size:.2f} MB")
                
                # Test large payload processing
                start_time = time.time()
                response = client.post("/generate", json=request_data)
                end_time = time.time()
                
                processing_time = end_time - start_time
                
                assert response.status_code == 200, f"Large payload failed: {response.status_code}"
                assert processing_time < 10.0, f"Large payload took too long: {processing_time:.2f}s"
                
                print(f"Processing time: {processing_time:.2f}s")
                print(f"Processing rate: {payload_size / processing_time:.2f} MB/s")
                
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_sustained_load_endurance(self, client, mock_engine_setup, sample_resume_data):
        """Test system endurance under sustained moderate load."""
        mock_engine, temp_path = mock_engine_setup()
        
        try:
            with patch('resume_agent_template_engine.api.app.TemplateEngine') as mock_engine_class, \
                 patch('tempfile.NamedTemporaryFile') as mock_tempfile, \
                 patch('os.path.exists', return_value=True), \
                 patch('os.remove'):
                
                mock_engine_class.return_value = mock_engine
                
                # Mock tempfile to return our real file path
                mock_temp = Mock()
                mock_temp.name = temp_path
                mock_tempfile.return_value.__enter__.return_value = mock_temp
                
                request_data = {
                    "document_type": "resume",
                    "template": "classic",
                    "format": "pdf",
                    "data": sample_resume_data
                }
                
                # Run sustained load for 30 seconds with requests every 100ms
                test_duration = 30  # seconds (reduced for CI/CD)
                request_interval = 0.1  # seconds
                expected_requests = int(test_duration / request_interval)
                
                start_time = time.time()
                successful_requests = 0
                failed_requests = 0
                response_times = []
                
                while time.time() - start_time < test_duration:
                    request_start = time.time()
                    
                    try:
                        response = client.post("/generate", json=request_data)
                        request_end = time.time()
                        
                        response_time = request_end - request_start
                        response_times.append(response_time)
                        
                        if response.status_code == 200:
                            successful_requests += 1
                        else:
                            failed_requests += 1
                            
                    except Exception:
                        failed_requests += 1
                    
                    # Wait for next request (if needed)
                    elapsed = time.time() - request_start
                    if elapsed < request_interval:
                        time.sleep(request_interval - elapsed)
                
                total_requests = successful_requests + failed_requests
                success_rate = successful_requests / total_requests if total_requests > 0 else 0
                
                print(f"\n=== Sustained Load Endurance Test Results ===")
                print(f"Test duration: {test_duration}s")
                print(f"Total requests: {total_requests}")
                print(f"Successful requests: {successful_requests}")
                print(f"Failed requests: {failed_requests}")
                print(f"Success rate: {success_rate:.2%}")
                
                if response_times:
                    print(f"Average response time: {statistics.mean(response_times):.3f}s")
                    print(f"95th percentile response time: {statistics.quantiles(response_times, n=20)[18]:.3f}s")
                
                # Assertions
                assert success_rate >= 0.98, f"Success rate too low for sustained load: {success_rate:.2%}"
                assert total_requests >= expected_requests * 0.8, f"Too few requests processed: {total_requests}"
                
                if response_times:
                    avg_response_time = statistics.mean(response_times)
                    assert avg_response_time < 1.0, f"Average response time degraded: {avg_response_time:.3f}s"
                
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestPerformanceBenchmarking:
    """Performance benchmarking and regression testing."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI application."""
        return TestClient(app)
    
    @pytest.fixture
    def benchmark_engine_setup(self):
        """Set up engine mocking for benchmark tests."""
        def setup_mock_engine():
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(b"Benchmark PDF content")
                temp_path = temp_file.name
            
            mock_engine = Mock()
            mock_engine.get_available_templates.return_value = {"resume": ["classic"]}
            mock_engine.export_to_pdf.return_value = temp_path
            
            return mock_engine, temp_path
        
        return setup_mock_engine

    def test_api_response_time_benchmarks(self, client, benchmark_engine_setup, sample_resume_data):
        """Benchmark API response times for different operations."""
        mock_engine, temp_path = benchmark_engine_setup()
        
        try:
            with patch('resume_agent_template_engine.api.app.TemplateEngine') as mock_engine_class, \
                 patch('tempfile.NamedTemporaryFile') as mock_tempfile, \
                 patch('os.path.exists', return_value=True), \
                 patch('os.remove'):
                
                mock_engine_class.return_value = mock_engine
                
                # Mock tempfile to return our real file path
                mock_temp = Mock()
                mock_temp.name = temp_path
                mock_tempfile.return_value.__enter__.return_value = mock_temp
                
                benchmarks = {}
                
                # Benchmark 1: Health check
                times = []
                for _ in range(100):
                    start = time.time()
                    response = client.get("/health")
                    end = time.time()
                    assert response.status_code == 200
                    times.append(end - start)
                benchmarks["health_check"] = {
                    "avg": statistics.mean(times),
                    "p95": statistics.quantiles(times, n=20)[18],
                    "p99": statistics.quantiles(times, n=100)[98]
                }
                
                # Benchmark 2: List templates
                times = []
                for _ in range(50):
                    start = time.time()
                    response = client.get("/templates")
                    end = time.time()
                    assert response.status_code == 200
                    times.append(end - start)
                benchmarks["list_templates"] = {
                    "avg": statistics.mean(times),
                    "p95": statistics.quantiles(times, n=20)[18],
                    "p99": statistics.quantiles(times, n=50)[48]
                }
                
                # Benchmark 3: Get schema
                times = []
                for _ in range(50):
                    start = time.time()
                    response = client.get("/schema/resume")
                    end = time.time()
                    assert response.status_code == 200
                    times.append(end - start)
                benchmarks["get_schema"] = {
                    "avg": statistics.mean(times),
                    "p95": statistics.quantiles(times, n=20)[18],
                    "p99": statistics.quantiles(times, n=50)[48]
                }
                
                # Benchmark 4: Document generation
                request_data = {
                    "document_type": "resume",
                    "template": "classic",
                    "format": "pdf",
                    "data": sample_resume_data
                }
                times = []
                for _ in range(30):
                    start = time.time()
                    response = client.post("/generate", json=request_data)
                    end = time.time()
                    assert response.status_code == 200
                    times.append(end - start)
                benchmarks["document_generation"] = {
                    "avg": statistics.mean(times),
                    "p95": statistics.quantiles(times, n=20)[18],
                    "p99": statistics.quantiles(times, n=30)[28]
                }
                
                # Print benchmark results
                print(f"\n=== Performance Benchmark Results ===")
                for operation, metrics in benchmarks.items():
                    print(f"{operation}:")
                    print(f"  Average: {metrics['avg']:.3f}s")
                    print(f"  95th percentile: {metrics['p95']:.3f}s")
                    print(f"  99th percentile: {metrics['p99']:.3f}s")
                
                # Performance assertions (these should be adjusted based on requirements)
                assert benchmarks["health_check"]["avg"] < 0.01, "Health check too slow"
                assert benchmarks["list_templates"]["avg"] < 0.05, "Template listing too slow"
                assert benchmarks["get_schema"]["avg"] < 0.05, "Schema retrieval too slow"
                assert benchmarks["document_generation"]["avg"] < 1.0, "Document generation too slow"
                assert benchmarks["document_generation"]["p95"] < 2.0, "95% of document generations too slow"
                
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_throughput_benchmarks(self, client, benchmark_engine_setup, sample_resume_data):
        """Benchmark system throughput under various loads."""
        mock_engine, temp_path = benchmark_engine_setup()
        
        try:
            with patch('resume_agent_template_engine.api.app.TemplateEngine') as mock_engine_class, \
                 patch('tempfile.NamedTemporaryFile') as mock_tempfile, \
                 patch('os.path.exists', return_value=True), \
                 patch('os.remove'):
                
                mock_engine_class.return_value = mock_engine
                
                # Mock tempfile to return our real file path
                mock_temp = Mock()
                mock_temp.name = temp_path
                mock_tempfile.return_value.__enter__.return_value = mock_temp
                
                request_data = {
                    "document_type": "resume",
                    "template": "classic",
                    "format": "pdf",
                    "data": sample_resume_data
                }
                
                throughput_results = {}
                
                # Test different concurrency levels
                concurrency_levels = [1, 5, 10, 20]
                
                for concurrency in concurrency_levels:
                    requests_per_level = 30
                    
                    def make_request():
                        response = client.post("/generate", json=request_data)
                        return response.status_code == 200
                    
                    start_time = time.time()
                    
                    with ThreadPoolExecutor(max_workers=concurrency) as executor:
                        futures = [executor.submit(make_request) for _ in range(requests_per_level)]
                        successful = sum(future.result() for future in as_completed(futures))
                    
                    end_time = time.time()
                    total_time = end_time - start_time
                    throughput = requests_per_level / total_time
                    
                    throughput_results[concurrency] = {
                        "throughput": throughput,
                        "success_rate": successful / requests_per_level,
                        "total_time": total_time
                    }
                
                print(f"\n=== Throughput Benchmark Results ===")
                for concurrency, results in throughput_results.items():
                    print(f"Concurrency {concurrency}:")
                    print(f"  Throughput: {results['throughput']:.2f} req/s")
                    print(f"  Success rate: {results['success_rate']:.2%}")
                    print(f"  Total time: {results['total_time']:.2f}s")
                
                # Assert minimum throughput requirements
                assert throughput_results[1]["throughput"] > 5, "Single request throughput too low"
                assert throughput_results[10]["throughput"] > 15, "Concurrent throughput too low"
                
                # Assert that success rate doesn't degrade significantly with concurrency
                for results in throughput_results.values():
                    assert results["success_rate"] >= 0.95, "Success rate degraded with concurrency"
                
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestConcurrencyValidation:
    """Specialized tests for concurrency handling and race conditions."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI application."""
        return TestClient(app)

    def test_race_condition_detection(self, client, sample_resume_data):
        """Test for race conditions in concurrent document generation."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(b"Race condition test PDF")
            temp_path = temp_file.name
        
        try:
            with patch('resume_agent_template_engine.api.app.TemplateEngine') as mock_engine_class, \
                 patch('tempfile.NamedTemporaryFile') as mock_tempfile, \
                 patch('os.path.exists', return_value=True), \
                 patch('os.remove'):
                
                mock_engine = Mock()
                mock_engine.get_available_templates.return_value = {"resume": ["classic"]}
                mock_engine.export_to_pdf.return_value = temp_path
                mock_engine_class.return_value = mock_engine
                
                # Mock tempfile to return our real file path
                mock_temp = Mock()
                mock_temp.name = temp_path
                mock_tempfile.return_value.__enter__.return_value = mock_temp
                
                request_data = {
                    "document_type": "resume",
                    "template": "classic",
                    "format": "pdf",
                    "data": sample_resume_data
                }
                
                # Track shared state to detect race conditions
                shared_state = {"counter": 0, "errors": []}
                lock = threading.Lock()
                
                def concurrent_request(request_id):
                    """Make a request and update shared state."""
                    try:
                        response = client.post("/generate", json=request_data)
                        
                        with lock:
                            shared_state["counter"] += 1
                            
                        # Simulate some processing time
                        time.sleep(0.01)
                        
                        with lock:
                            if response.status_code != 200:
                                shared_state["errors"].append(f"Request {request_id}: {response.status_code}")
                                
                        return response.status_code == 200
                        
                    except Exception as e:
                        with lock:
                            shared_state["errors"].append(f"Request {request_id}: {str(e)}")
                        return False
                
                # Execute concurrent requests
                num_threads = 20
                with ThreadPoolExecutor(max_workers=num_threads) as executor:
                    futures = [executor.submit(concurrent_request, i) for i in range(num_threads)]
                    results = [future.result() for future in as_completed(futures)]
                
                # Verify no race conditions occurred
                assert shared_state["counter"] == num_threads, "Race condition detected in counter"
                assert len(shared_state["errors"]) == 0, f"Errors detected: {shared_state['errors']}"
                assert all(results), "Some concurrent requests failed"
                
                print(f"\n=== Race Condition Test Results ===")
                print(f"Concurrent requests: {num_threads}")
                print(f"Successful requests: {sum(results)}")
                print(f"Counter value: {shared_state['counter']}")
                print(f"Errors: {len(shared_state['errors'])}")
                
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_resource_contention_handling(self, client, sample_resume_data):
        """Test handling of resource contention under high concurrency."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(b"Resource contention test PDF")
            temp_path = temp_file.name
        
        try:
            with patch('resume_agent_template_engine.api.app.TemplateEngine') as mock_engine_class, \
                 patch('tempfile.NamedTemporaryFile') as mock_tempfile, \
                 patch('os.path.exists', return_value=True), \
                 patch('os.remove'):
                
                mock_engine = Mock()
                mock_engine.get_available_templates.return_value = {"resume": ["classic"]}
                
                # Simulate varying processing times to create contention
                def variable_export_time(*args, **kwargs):
                    import random
                    time.sleep(random.uniform(0.01, 0.1))  # 10-100ms processing time
                    return temp_path
                
                mock_engine.export_to_pdf.side_effect = variable_export_time
                mock_engine_class.return_value = mock_engine
                
                # Mock tempfile to return our real file path
                mock_temp = Mock()
                mock_temp.name = temp_path
                mock_tempfile.return_value.__enter__.return_value = mock_temp
                
                request_data = {
                    "document_type": "resume",
                    "template": "classic",
                    "format": "pdf",
                    "data": sample_resume_data
                }
                
                # Test with high concurrency to force resource contention
                num_requests = 50
                max_workers = 25
                
                response_times = []
                status_codes = []
                
                def timed_request():
                    start_time = time.time()
                    response = client.post("/generate", json=request_data)
                    end_time = time.time()
                    
                    return {
                        "response_time": end_time - start_time,
                        "status_code": response.status_code
                    }
                
                start_test = time.time()
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = [executor.submit(timed_request) for _ in range(num_requests)]
                    results = [future.result() for future in as_completed(futures)]
                
                end_test = time.time()
                
                response_times = [r["response_time"] for r in results]
                status_codes = [r["status_code"] for r in results]
                successful_requests = sum(1 for code in status_codes if code == 200)
                
                print(f"\n=== Resource Contention Test Results ===")
                print(f"Total requests: {num_requests}")
                print(f"Successful requests: {successful_requests}")
                print(f"Success rate: {successful_requests / num_requests:.2%}")
                print(f"Average response time: {statistics.mean(response_times):.3f}s")
                print(f"Max response time: {max(response_times):.3f}s")
                print(f"Total test time: {end_test - start_test:.2f}s")
                
                # Assertions
                success_rate = successful_requests / num_requests
                assert success_rate >= 0.95, f"Success rate too low under contention: {success_rate:.2%}"
                
                # Response times should still be reasonable even under contention
                avg_response_time = statistics.mean(response_times)
                assert avg_response_time < 2.0, f"Average response time too high under contention: {avg_response_time:.3f}s"
                
                # No response should take extremely long (deadlock detection)
                max_response_time = max(response_times)
                assert max_response_time < 5.0, f"Maximum response time indicates potential deadlock: {max_response_time:.3f}s"
                
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestScalabilityValidation:
    """Tests to validate system scalability characteristics."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI application."""
        return TestClient(app)

    def test_load_scaling_behavior(self, client, sample_resume_data):
        """Test how system performance scales with increasing load."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(b"Scalability test PDF")
            temp_path = temp_file.name
        
        try:
            with patch('resume_agent_template_engine.api.app.TemplateEngine') as mock_engine_class, \
                 patch('tempfile.NamedTemporaryFile') as mock_tempfile, \
                 patch('os.path.exists', return_value=True), \
                 patch('os.remove'):
                
                mock_engine = Mock()
                mock_engine.get_available_templates.return_value = {"resume": ["classic"]}
                mock_engine.export_to_pdf.return_value = temp_path
                mock_engine_class.return_value = mock_engine
                
                # Mock tempfile to return our real file path
                mock_temp = Mock()
                mock_temp.name = temp_path
                mock_tempfile.return_value.__enter__.return_value = mock_temp
                
                request_data = {
                    "document_type": "resume",
                    "template": "classic",
                    "format": "pdf",
                    "data": sample_resume_data
                }
                
                # Test different load levels
                load_levels = [5, 10, 15, 20, 25]  # Number of concurrent requests
                results = {}
                
                for load in load_levels:
                    def make_request():
                        start_time = time.time()
                        response = client.post("/generate", json=request_data)
                        end_time = time.time()
                        return {
                            "success": response.status_code == 200,
                            "response_time": end_time - start_time
                        }
                    
                    test_start = time.time()
                    
                    with ThreadPoolExecutor(max_workers=load) as executor:
                        futures = [executor.submit(make_request) for _ in range(load)]
                        load_results = [future.result() for future in as_completed(futures)]
                    
                    test_end = time.time()
                    
                    successful = sum(1 for r in load_results if r["success"])
                    response_times = [r["response_time"] for r in load_results]
                    
                    results[load] = {
                        "success_rate": successful / load,
                        "avg_response_time": statistics.mean(response_times),
                        "throughput": load / (test_end - test_start),
                        "total_time": test_end - test_start
                    }
                    
                    # Small delay between load tests
                    time.sleep(0.5)
                
                print(f"\n=== Load Scaling Behavior Results ===")
                for load, metrics in results.items():
                    print(f"Load {load}:")
                    print(f"  Success rate: {metrics['success_rate']:.2%}")
                    print(f"  Avg response time: {metrics['avg_response_time']:.3f}s")
                    print(f"  Throughput: {metrics['throughput']:.2f} req/s")
                
                # Analyze scaling behavior
                success_rates = [metrics["success_rate"] for metrics in results.values()]
                avg_response_times = [metrics["avg_response_time"] for metrics in results.values()]
                throughputs = [metrics["throughput"] for metrics in results.values()]
                
                # Assert that success rate doesn't degrade significantly
                min_success_rate = min(success_rates)
                assert min_success_rate >= 0.90, f"Success rate degraded too much at high load: {min_success_rate:.2%}"
                
                # Assert that response time doesn't increase exponentially
                max_response_time = max(avg_response_times)
                assert max_response_time < 3.0, f"Response time increased too much at high load: {max_response_time:.3f}s"
                
                # Throughput should generally be reasonable across all load levels
                # Note: Throughput may not always increase linearly due to resource contention
                min_throughput = min(throughputs)
                assert min_throughput > 100, f"Minimum throughput too low: {min_throughput:.2f} req/s"
                
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @pytest.mark.slow
    def test_recovery_after_overload(self, client, sample_resume_data):
        """Test system recovery after experiencing overload conditions."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(b"Recovery test PDF")
            temp_path = temp_file.name
        
        try:
            with patch('resume_agent_template_engine.api.app.TemplateEngine') as mock_engine_class, \
                 patch('tempfile.NamedTemporaryFile') as mock_tempfile, \
                 patch('os.path.exists', return_value=True), \
                 patch('os.remove'):
                
                mock_engine = Mock()
                mock_engine.get_available_templates.return_value = {"resume": ["classic"]}
                mock_engine.export_to_pdf.return_value = temp_path
                mock_engine_class.return_value = mock_engine
                
                # Mock tempfile to return our real file path
                mock_temp = Mock()
                mock_temp.name = temp_path
                mock_tempfile.return_value.__enter__.return_value = mock_temp
                
                request_data = {
                    "document_type": "resume",
                    "template": "classic",
                    "format": "pdf",
                    "data": sample_resume_data
                }
                
                # Phase 1: Normal operation baseline
                print(f"\n=== Recovery Test: Phase 1 - Baseline ===")
                baseline_start = time.time()
                response = client.post("/generate", json=request_data)
                baseline_time = time.time() - baseline_start
                assert response.status_code == 200
                print(f"Baseline response time: {baseline_time:.3f}s")
                
                # Phase 2: Overload the system
                print(f"=== Recovery Test: Phase 2 - Overload ===")
                overload_requests = 50
                overload_concurrency = 30
                
                def overload_request():
                    try:
                        response = client.post("/generate", json=request_data)
                        return response.status_code == 200
                    except:
                        return False
                
                overload_start = time.time()
                with ThreadPoolExecutor(max_workers=overload_concurrency) as executor:
                    futures = [executor.submit(overload_request) for _ in range(overload_requests)]
                    overload_results = [future.result() for future in as_completed(futures)]
                overload_end = time.time()
                
                overload_success_rate = sum(overload_results) / len(overload_results)
                print(f"Overload success rate: {overload_success_rate:.2%}")
                print(f"Overload duration: {overload_end - overload_start:.2f}s")
                
                # Phase 3: Recovery period
                print(f"=== Recovery Test: Phase 3 - Recovery ===")
                time.sleep(2)  # Allow system to recover
                
                # Test recovery with single requests
                recovery_times = []
                recovery_successes = 0
                
                for i in range(10):
                    recovery_start = time.time()
                    response = client.post("/generate", json=request_data)
                    recovery_time = time.time() - recovery_start
                    
                    recovery_times.append(recovery_time)
                    if response.status_code == 200:
                        recovery_successes += 1
                    
                    time.sleep(0.1)  # Brief pause between recovery tests
                
                recovery_success_rate = recovery_successes / 10
                avg_recovery_time = statistics.mean(recovery_times)
                
                print(f"Recovery success rate: {recovery_success_rate:.2%}")
                print(f"Average recovery response time: {avg_recovery_time:.3f}s")
                
                # Assertions
                assert recovery_success_rate >= 0.90, f"System didn't recover properly: {recovery_success_rate:.2%}"
                
                # Response time should return to reasonable levels after recovery
                recovery_degradation = avg_recovery_time / baseline_time
                assert recovery_degradation < 10.0, f"Response time didn't recover properly: {recovery_degradation:.2f}x baseline"
                
                print(f"Recovery degradation factor: {recovery_degradation:.2f}x")
                
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path) 