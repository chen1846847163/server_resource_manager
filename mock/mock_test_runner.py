import random
import time
import json
import logging

logger = logging.getLogger(__name__)

MOCK_TEST_CASES = [
    {"name": "test_network_connectivity", "module": "network", "description": "Test basic network connectivity", "params": {"target": "8.8.8.8", "timeout": 5}},
    {"name": "test_disk_io", "module": "hardware", "description": "Test disk read/write speed", "params": {"path": "/tmp", "size_mb": 100}},
    {"name": "test_cpu_stress", "module": "hardware", "description": "Test CPU under load", "params": {"duration": 10, "threads": 4}},
    {"name": "test_memory_leak", "module": "memory", "description": "Test for memory leaks", "params": {"iterations": 1000}},
    {"name": "test_api_response", "module": "api", "description": "Test API response times", "params": {"url": "http://localhost:8080", "expected_ms": 200}},
    {"name": "test_service_restart", "module": "service", "description": "Test service restart behavior", "params": {"service": "nginx", "max_wait": 30}},
]


def get_mock_test_cases():
    return MOCK_TEST_CASES


def run_mock_test(case_name, server_info, params=None):
    logger.info(f"Running mock test '{case_name}' on server {server_info.get('name', 'unknown')}")
    time.sleep(random.uniform(0.5, 2.0))

    success_rate = random.uniform(0.7, 1.0)
    passed = random.random() < success_rate

    result = {
        "test_case": case_name,
        "server": server_info.get("name", "unknown"),
        "server_host": server_info.get("host", "unknown"),
        "passed": passed,
        "duration_ms": round(random.uniform(100, 5000), 1),
        "error": None if passed else f"Mock error: {random.choice(['Timeout', 'Assertion failed', 'Connection refused', 'Unexpected response'])}",
        "output": f"Mock output for {case_name}" + (f" with params: {params}" if params else ""),
    }
    logger.info(f"Test '{case_name}' finished: {'PASS' if passed else 'FAIL'}")
    return result
