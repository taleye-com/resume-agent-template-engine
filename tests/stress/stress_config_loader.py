"""Configuration loader for stress testing parameters."""

import os
import yaml
import json
from typing import Dict, Any, Optional, List
from pathlib import Path


class StressTestConfig:
    """Configuration manager for stress testing parameters."""

    def __init__(
        self, config_path: Optional[str] = None, stress_level: Optional[str] = None
    ):
        """
        Initialize the stress test configuration.

        Args:
            config_path: Path to the configuration file
            stress_level: Override stress level (light, medium, heavy, enterprise, extreme)
        """
        self.config_path = config_path or self._find_config_file()
        self.config = self._load_config()
        self.stress_level = stress_level or self._get_default_stress_level()
        self.environment = self._detect_environment()

        # Apply environment overrides
        self._apply_environment_overrides()

    def _find_config_file(self) -> str:
        """Find the stress test configuration file."""
        # Try multiple possible locations
        possible_paths = [
            "config/stress_test_config.yaml",
            "tests/stress/stress_test_config.yaml",
            "../config/stress_test_config.yaml",
            "../../config/stress_test_config.yaml",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # If not found, use the default location
        return "config/stress_test_config.yaml"

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, "r") as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            print(
                f"Warning: Config file {self.config_path} not found. Using default configuration."
            )
            return self._get_default_config()
        except Exception as e:
            print(f"Error loading config: {e}. Using default configuration.")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if file is not found."""
        return {
            "global_settings": {
                "default_stress_level": "medium",
                "timeout_seconds": 300,
                "cleanup_temp_files": True,
                "enable_detailed_logging": True,
            },
            "stress_levels": {
                "medium": {
                    "concurrent_requests": {
                        "high_volume_test": 50,
                        "sustained_load_test": 20,
                        "race_condition_test": 20,
                        "resource_contention_test": 50,
                        "scaling_test_levels": [5, 10, 15, 20, 25],
                        "overload_test": 75,
                    },
                    "performance_requirements": {
                        "success_rate_threshold": 0.95,
                        "avg_response_time_threshold": 2.0,
                        "max_response_time_threshold": 5.0,
                        "throughput_threshold": 10.0,
                        "memory_increase_threshold": 75,
                        "recovery_degradation_threshold": 10.0,
                    },
                    "test_duration": {
                        "sustained_load_duration": 30,
                        "overload_duration": 10,
                        "recovery_wait_time": 2,
                    },
                    "payload_size": {
                        "large_payload_entries": 100,
                        "large_payload_size_mb": 5.0,
                    },
                }
            },
        }

    def _get_default_stress_level(self) -> str:
        """Get the default stress level from configuration."""
        return self.config.get("global_settings", {}).get(
            "default_stress_level", "medium"
        )

    def _detect_environment(self) -> str:
        """Detect the current environment."""
        # Check environment variables
        if os.getenv("CI") or os.getenv("GITHUB_ACTIONS") or os.getenv("JENKINS_URL"):
            return "ci_cd"
        elif os.getenv("STRESS_TEST_ENV"):
            return os.getenv("STRESS_TEST_ENV")
        elif os.getenv("ENVIRONMENT"):
            env = os.getenv("ENVIRONMENT").lower()
            if env in ["dev", "development"]:
                return "local_development"
            elif env in ["prod", "production"]:
                return "production"
            elif env in ["stage", "staging"]:
                return "staging"

        # Default to local development
        return "local_development"

    def _apply_environment_overrides(self):
        """Apply environment-specific overrides to the configuration."""
        overrides = self.config.get("environment_overrides", {}).get(
            self.environment, {}
        )

        if overrides:
            print(f"Applying environment overrides for: {self.environment}")

            # Apply multipliers to concurrent requests
            if "concurrent_requests_multiplier" in overrides:
                multiplier = overrides["concurrent_requests_multiplier"]
                stress_config = self.config["stress_levels"][self.stress_level]

                for key, value in stress_config["concurrent_requests"].items():
                    if isinstance(value, (int, float)):
                        stress_config["concurrent_requests"][key] = max(
                            1, int(value * multiplier)
                        )
                    elif isinstance(value, list):
                        stress_config["concurrent_requests"][key] = [
                            max(1, int(v * multiplier)) for v in value
                        ]

            # Apply multipliers to durations
            if "duration_multiplier" in overrides:
                multiplier = overrides["duration_multiplier"]
                stress_config = self.config["stress_levels"][self.stress_level]

                for key, value in stress_config["test_duration"].items():
                    stress_config["test_duration"][key] = max(
                        1, int(value * multiplier)
                    )

            # Apply timeout override
            if "timeout_seconds" in overrides:
                self.config["global_settings"]["timeout_seconds"] = overrides[
                    "timeout_seconds"
                ]

    def get_stress_level_config(self, level: Optional[str] = None) -> Dict[str, Any]:
        """Get configuration for a specific stress level."""
        level = level or self.stress_level
        return self.config.get("stress_levels", {}).get(level, {})

    def get_concurrent_requests(
        self, test_name: str, level: Optional[str] = None
    ) -> int:
        """Get concurrent request count for a specific test."""
        config = self.get_stress_level_config(level)
        return config.get("concurrent_requests", {}).get(test_name, 10)

    def get_performance_requirement(
        self, requirement: str, level: Optional[str] = None
    ) -> float:
        """Get performance requirement value."""
        config = self.get_stress_level_config(level)
        return config.get("performance_requirements", {}).get(requirement, 0.95)

    def get_test_duration(self, duration_type: str, level: Optional[str] = None) -> int:
        """Get test duration for a specific type."""
        config = self.get_stress_level_config(level)
        return config.get("test_duration", {}).get(duration_type, 30)

    def get_payload_size_config(self, level: Optional[str] = None) -> Dict[str, Any]:
        """Get payload size configuration."""
        config = self.get_stress_level_config(level)
        return config.get(
            "payload_size", {"large_payload_entries": 100, "large_payload_size_mb": 5.0}
        )

    def get_scaling_test_levels(self, level: Optional[str] = None) -> List[int]:
        """Get scaling test levels."""
        config = self.get_stress_level_config(level)
        return config.get("concurrent_requests", {}).get(
            "scaling_test_levels", [5, 10, 15, 20, 25]
        )

    def should_skip_test(self, test_name: str, category: str = "staging") -> bool:
        """Check if a test should be skipped based on category configuration."""
        category_config = self.config.get("test_categories", {}).get(category, {})

        # Check if stress level is allowed for this category
        allowed_levels = category_config.get("stress_levels", [])
        if allowed_levels and self.stress_level not in allowed_levels:
            return True

        # Check if test is in required or optional tests
        required_tests = category_config.get("required_tests", [])
        optional_tests = category_config.get("optional_tests", [])

        # If test is not in required or optional, skip it
        if test_name not in required_tests and test_name not in optional_tests:
            return True

        # Check if slow tests should be skipped
        if category_config.get("skip_slow_tests", False):
            slow_tests = [
                "sustained_load",
                "recovery_after_overload",
                "scaling_behavior",
            ]
            if test_name in slow_tests:
                return True

        return False

    def get_benchmark_requirement(self, benchmark_type: str, metric: str) -> float:
        """Get benchmark requirement value."""
        benchmarks = self.config.get("benchmarks", {})
        return benchmarks.get(benchmark_type, {}).get(metric, 1.0)

    def is_detailed_logging_enabled(self) -> bool:
        """Check if detailed logging is enabled."""
        return self.config.get("global_settings", {}).get(
            "enable_detailed_logging", True
        )

    def should_cleanup_temp_files(self) -> bool:
        """Check if temporary files should be cleaned up."""
        return self.config.get("global_settings", {}).get("cleanup_temp_files", True)

    def get_timeout_seconds(self) -> int:
        """Get the global timeout in seconds."""
        return self.config.get("global_settings", {}).get("timeout_seconds", 300)

    def export_metrics_enabled(self) -> bool:
        """Check if metrics export is enabled."""
        return self.config.get("reporting", {}).get("export_metrics_to_file", True)

    def get_metrics_file_format(self) -> str:
        """Get the metrics file format."""
        return self.config.get("reporting", {}).get("metrics_file_format", "json")

    def print_configuration_summary(self):
        """Print a summary of the current configuration."""
        print(f"\n=== Stress Test Configuration Summary ===")
        print(f"Stress Level: {self.stress_level}")
        print(f"Environment: {self.environment}")
        print(f"Config File: {self.config_path}")

        config = self.get_stress_level_config()
        if config:
            print(f"Description: {config.get('description', 'N/A')}")
            print(
                f"High Volume Test: {self.get_concurrent_requests('high_volume_test')} concurrent requests"
            )
            print(
                f"Success Rate Threshold: {self.get_performance_requirement('success_rate_threshold'):.1%}"
            )
            print(
                f"Avg Response Time Threshold: {self.get_performance_requirement('avg_response_time_threshold'):.1f}s"
            )
            print(
                f"Throughput Threshold: {self.get_performance_requirement('throughput_threshold'):.1f} req/s"
            )

        print("=" * 45)


def get_stress_config(
    stress_level: Optional[str] = None, config_path: Optional[str] = None
) -> StressTestConfig:
    """
    Factory function to get a configured StressTestConfig instance.

    Args:
        stress_level: Override stress level
        config_path: Path to config file

    Returns:
        Configured StressTestConfig instance
    """
    # Check for environment variable override
    if not stress_level:
        stress_level = os.getenv("STRESS_TEST_LEVEL")

    return StressTestConfig(config_path=config_path, stress_level=stress_level)


def export_test_metrics(
    metrics: Dict[str, Any], config: StressTestConfig, test_name: str
):
    """Export test metrics to file if enabled."""
    if not config.export_metrics_enabled():
        return

    timestamp = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"stress_test_metrics_{test_name}_{config.stress_level}_{timestamp}"

    format_type = config.get_metrics_file_format()

    if format_type == "json":
        filename += ".json"
        with open(filename, "w") as f:
            json.dump(metrics, f, indent=2)
    elif format_type == "yaml":
        filename += ".yaml"
        with open(filename, "w") as f:
            yaml.dump(metrics, f, default_flow_style=False)

    print(f"Metrics exported to: {filename}")
