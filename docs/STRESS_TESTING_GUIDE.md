# Stress Testing Configuration Guide

This guide explains how to use the comprehensive stress testing system for the resume-agent-template-engine, including enterprise-level testing with up to 10,000+ concurrent requests.

## Overview

The stress testing system provides configurable stress levels and categories designed for different environments and use cases:

- **Development**: Light testing for local development
- **Staging**: Medium testing for validation environments
- **Production**: Heavy testing for production validation
- **Enterprise**: High-scale testing for enterprise applications
- **Extreme**: Breaking point testing with 10,000+ concurrent requests

## Quick Start

### Basic Usage

```bash
# Run with default (medium) stress level
python run_stress_tests.py

# Run enterprise-level stress tests (1,000 concurrent requests)
python run_stress_tests.py --stress-level enterprise

# Run extreme stress tests (10,000 concurrent requests)
python run_stress_tests.py --stress-level extreme

# Run specific test category
python run_stress_tests.py --category production

# Run specific tests only
python run_stress_tests.py --tests high_volume,memory_stress
```

### Enterprise Testing

```bash
# Enterprise application validation (99% success rate, <1s response time)
python run_stress_tests.py --stress-level enterprise --export-metrics

# Breaking point analysis (find system limits)
python run_stress_tests.py --stress-level extreme --category breaking_point
```

## Stress Levels

### Light (Development)
- **Concurrent Requests**: 10-15
- **Success Rate**: ≥90%
- **Response Time**: <3.0s
- **Use Case**: Local development, debugging
- **Duration**: Short (10 seconds)

### Medium (Staging)
- **Concurrent Requests**: 50-75
- **Success Rate**: ≥95%
- **Response Time**: <2.0s
- **Use Case**: Staging environment validation
- **Duration**: Medium (30 seconds)

### Heavy (Production)
- **Concurrent Requests**: 200-300
- **Success Rate**: ≥98%
- **Response Time**: <1.5s
- **Use Case**: Production readiness testing
- **Duration**: Long (60 seconds)

### Enterprise (High-Scale)
- **Concurrent Requests**: 1,000-1,500
- **Success Rate**: ≥99%
- **Response Time**: <1.0s
- **Use Case**: Enterprise application validation
- **Duration**: Extended (120 seconds)
- **Special Features**: Handles enterprise-scale loads

### Extreme (Breaking Point)
- **Concurrent Requests**: 10,000-15,000
- **Success Rate**: ≥95% (degradation expected)
- **Response Time**: <2.0s
- **Use Case**: Finding system limits, capacity planning
- **Duration**: Long (300 seconds)
- **Warning**: High resource usage

## Test Categories

### Development
- **Stress Levels**: Light only
- **Required Tests**: Basic functionality
- **Skip Slow Tests**: Yes
- **Use Case**: Daily development

### Staging
- **Stress Levels**: Light, Medium
- **Required Tests**: Comprehensive validation
- **Skip Slow Tests**: No
- **Use Case**: Pre-production testing

### Production
- **Stress Levels**: Medium, Heavy
- **Required Tests**: Full production validation
- **Skip Slow Tests**: No
- **Use Case**: Production deployment validation

### Enterprise
- **Stress Levels**: Heavy, Enterprise
- **Required Tests**: All tests including recovery
- **Skip Slow Tests**: No
- **Use Case**: Enterprise deployment validation

### Breaking Point
- **Stress Levels**: Extreme only
- **Required Tests**: Core stress tests
- **Skip Slow Tests**: No
- **Use Case**: Capacity planning and limit testing

## Configuration File

The system uses `config/stress_test_config.yaml` to define all parameters:

```yaml
stress_levels:
  enterprise:
    concurrent_requests:
      high_volume_test: 1000      # 1K concurrent requests
      sustained_load_test: 200    # 200 sustained requests
      scaling_test_levels: [50, 100, 250, 500, 1000]
    
    performance_requirements:
      success_rate_threshold: 0.99     # 99% success rate
      avg_response_time_threshold: 1.0 # <1 second response
      throughput_threshold: 100.0      # 100+ req/s throughput
    
    test_duration:
      sustained_load_duration: 120     # 2 minutes
      recovery_wait_time: 5           # 5 seconds recovery
```

## Environment Detection

The system automatically detects and adjusts for different environments:

### CI/CD Environments
- **Auto-Detection**: GitHub Actions, Jenkins, etc.
- **Adjustments**: 50% reduced load, shorter durations
- **Timeout**: 3 minutes maximum

### Local Development
- **Auto-Detection**: Default when no CI detected
- **Adjustments**: 20% reduced load, shorter durations
- **Timeout**: 1 minute maximum

### Performance Testing
- **Manual Override**: Set `STRESS_TEST_ENV=performance_testing`
- **Adjustments**: 200% increased load, longer durations
- **Timeout**: 10 minutes maximum

## Advanced Usage

### Custom Configuration

```bash
# Use custom configuration file
python run_stress_tests.py --config my_custom_config.yaml

# Override environment detection
python run_stress_tests.py --environment performance_testing

# Export detailed metrics
python run_stress_tests.py --stress-level enterprise --export-metrics --detailed-report
```

### Environment Variables

```bash
# Set stress level via environment
export STRESS_TEST_LEVEL=enterprise
python run_stress_tests.py

# Override environment detection
export STRESS_TEST_ENV=performance_testing
python run_stress_tests.py
```

### Dry Run Testing

```bash
# See what would be executed without running
python run_stress_tests.py --stress-level extreme --dry-run
```

## Test Metrics and Reporting

### Automatic Metrics Export

The system automatically exports detailed metrics in JSON format:

```json
{
  "test_name": "high_volume_concurrent_requests",
  "stress_level": "enterprise",
  "configuration": {
    "concurrent_requests": 1000,
    "success_rate_threshold": 0.99,
    "avg_response_time_threshold": 1.0,
    "throughput_threshold": 100.0
  },
  "results": {
    "total_requests": 1000,
    "successful_requests": 995,
    "success_rate": 0.995,
    "avg_response_time": 0.85,
    "throughput": 125.5
  },
  "assertions": {
    "success_rate_passed": true,
    "avg_response_time_passed": true,
    "throughput_passed": true
  }
}
```

### Performance Benchmarks

The system includes predefined benchmarks for:

- **API Response Times**: Health checks, template listing, document generation
- **Throughput Requirements**: Single request, concurrent 10/20/50/100
- **Resource Usage**: Memory consumption, garbage collection
- **Scalability**: Load scaling behavior, recovery after overload

## Enterprise Use Cases

### High-Traffic Production Systems

```bash
# Validate system can handle 1,000 concurrent users
python run_stress_tests.py --stress-level enterprise

# Expected Results:
# - 99% success rate with 1,000 concurrent requests
# - <1 second average response time
# - 100+ requests/second throughput
# - Proper recovery after overload conditions
```

### Load Testing for Capacity Planning

```bash
# Find system breaking points
python run_stress_tests.py --stress-level extreme --category breaking_point

# Expected Results:
# - Maximum concurrent request handling (up to 10,000)
# - Performance degradation points
# - Resource utilization limits
# - Recovery characteristics
```

### Regression Testing

```bash
# Ensure performance doesn't degrade between releases
python run_stress_tests.py --stress-level heavy --export-metrics

# Compare metrics with baseline:
# - Response time trends
# - Throughput changes
# - Success rate stability
# - Resource usage patterns
```

## Troubleshooting

### Common Issues

#### Test Skipped
```
Skipped: High volume test skipped for local_development environment
```
**Solution**: Use appropriate stress level for environment or override:
```bash
python run_stress_tests.py --environment performance_testing
```

#### Memory Issues (Extreme Tests)
```
Error: System ran out of memory during extreme stress test
```
**Solutions**:
- Increase system memory
- Use lower stress level (enterprise instead of extreme)
- Run tests on dedicated performance testing server

#### Timeout Issues
```
Error: Test exceeded timeout limit
```
**Solutions**:
- Increase timeout in configuration
- Use faster stress level
- Check system performance

### Performance Tuning

If tests fail to meet enterprise requirements:

1. **Optimize Application Code**
   - Profile slow endpoints
   - Optimize database queries
   - Implement caching

2. **Infrastructure Scaling**
   - Increase server resources
   - Add load balancing
   - Optimize database performance

3. **Configuration Tuning**
   - Adjust thresholds in config file
   - Optimize thread pool sizes
   - Tune garbage collection

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Enterprise Stress Tests
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  
jobs:
  stress-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
      
      - name: Run Enterprise Stress Tests
        run: |
          python run_stress_tests.py --stress-level enterprise --quiet
      
      - name: Upload metrics
        uses: actions/upload-artifact@v3
        with:
          name: stress-test-metrics
          path: stress_test_metrics_*.json
```

### Jenkins Pipeline Example

```groovy
pipeline {
    agent any
    
    stages {
        stage('Enterprise Stress Test') {
            steps {
                script {
                    sh 'python run_stress_tests.py --stress-level enterprise'
                }
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'stress_test_metrics_*.json'
        }
    }
}
```

## Best Practices

### Development Workflow

1. **Local Development**: Use light stress tests
2. **Pull Request**: Run medium stress tests
3. **Staging Deployment**: Run heavy stress tests
4. **Production Deployment**: Run enterprise stress tests
5. **Capacity Planning**: Run extreme stress tests periodically

### Monitoring and Alerting

1. **Set up alerts** for stress test failures
2. **Monitor trends** in performance metrics
3. **Establish baselines** for each environment
4. **Review metrics** regularly for degradation

### Resource Management

1. **Run extreme tests** on dedicated hardware
2. **Schedule heavy tests** during off-peak hours
3. **Monitor system resources** during testing
4. **Clean up temporary files** after testing

## Support

For questions or issues with stress testing:

1. Check this documentation first
2. Review the configuration file (`config/stress_test_config.yaml`)
3. Run with `--verbose` flag for detailed output
4. Check exported metrics for detailed analysis
5. Use `--dry-run` to validate configuration without running tests

The stress testing system is designed to scale from simple development validation to enterprise-level production testing with 10,000+ concurrent requests. 