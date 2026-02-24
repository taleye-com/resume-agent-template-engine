"""
Load Test for Resume Agent Template Engine
Tests how many requests the API can handle with 1 CPU and 2GB memory.

Usage:
    python tests/load/test_load_performance.py

Requirements:
    pip install httpx aiohttp rich
"""

import asyncio
import time
import statistics
from dataclasses import dataclass, field
from typing import Optional
import httpx
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

console = Console()

# Sample resume data for testing
SAMPLE_RESUME_DATA = {
    "document_type": "resume",
    "template": "classic",
    "format": "pdf",
    "spacing_mode": "compact",
    "data": {
        "personalInfo": {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1 (555) 123-4567",
            "location": "San Francisco, CA",
            "linkedin": "https://linkedin.com/in/johndoe",
            "github": "https://github.com/johndoe"
        },
        "professionalSummary": "Experienced software engineer with 8+ years of expertise in full-stack development, cloud architecture, and team leadership. Proven track record of delivering scalable solutions.",
        "experience": [
            {
                "position": "Senior Software Engineer",
                "company": "Tech Corp",
                "location": "San Francisco, CA",
                "startDate": "2020-01",
                "endDate": "Present",
                "description": "Lead development of cloud-native applications",
                "achievements": [
                    "Reduced system latency by 40%",
                    "Led team of 5 engineers",
                    "Implemented CI/CD pipeline"
                ]
            },
            {
                "position": "Software Engineer",
                "company": "StartupXYZ",
                "location": "New York, NY",
                "startDate": "2017-06",
                "endDate": "2019-12",
                "description": "Full-stack development",
                "achievements": [
                    "Built RESTful APIs serving 1M+ requests/day",
                    "Designed database schema for 100K+ users"
                ]
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Science in Computer Science",
                "institution": "MIT",
                "graduationDate": "2017-05",
                "gpa": "3.8/4.0"
            }
        ],
        "skills": {
            "technical": ["Python", "JavaScript", "TypeScript", "React", "Node.js", "AWS", "Docker", "Kubernetes"],
            "soft": ["Leadership", "Communication", "Problem Solving"]
        }
    }
}


@dataclass
class LoadTestResult:
    """Results from a single request"""
    success: bool
    response_time_ms: float
    status_code: int
    error: Optional[str] = None


@dataclass
class LoadTestStats:
    """Aggregated statistics from load test"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    response_times: list = field(default_factory=list)
    start_time: float = 0
    end_time: float = 0
    errors: dict = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float:
        return self.end_time - self.start_time

    @property
    def requests_per_second(self) -> float:
        if self.duration_seconds > 0:
            return self.successful_requests / self.duration_seconds
        return 0

    @property
    def avg_response_time(self) -> float:
        if self.response_times:
            return statistics.mean(self.response_times)
        return 0

    @property
    def min_response_time(self) -> float:
        if self.response_times:
            return min(self.response_times)
        return 0

    @property
    def max_response_time(self) -> float:
        if self.response_times:
            return max(self.response_times)
        return 0

    @property
    def p50_response_time(self) -> float:
        if self.response_times:
            return statistics.median(self.response_times)
        return 0

    @property
    def p95_response_time(self) -> float:
        if len(self.response_times) >= 2:
            sorted_times = sorted(self.response_times)
            idx = int(len(sorted_times) * 0.95)
            return sorted_times[idx]
        return self.max_response_time

    @property
    def p99_response_time(self) -> float:
        if len(self.response_times) >= 2:
            sorted_times = sorted(self.response_times)
            idx = int(len(sorted_times) * 0.99)
            return sorted_times[idx]
        return self.max_response_time

    @property
    def success_rate(self) -> float:
        if self.total_requests > 0:
            return (self.successful_requests / self.total_requests) * 100
        return 0


class LoadTester:
    """Load tester for Resume Agent Template Engine"""

    def __init__(
        self,
        base_url: str = "http://localhost:8501",
        timeout: float = 120.0
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.stats = LoadTestStats()

    async def make_request(
        self,
        client: httpx.AsyncClient,
        endpoint: str = "/generate",
        method: str = "POST",
        data: dict = None
    ) -> LoadTestResult:
        """Make a single request and return result"""
        start = time.perf_counter()
        try:
            if method == "POST":
                response = await client.post(
                    f"{self.base_url}{endpoint}",
                    json=data or SAMPLE_RESUME_DATA,
                    timeout=self.timeout
                )
            else:
                response = await client.get(
                    f"{self.base_url}{endpoint}",
                    timeout=self.timeout
                )

            elapsed_ms = (time.perf_counter() - start) * 1000

            return LoadTestResult(
                success=response.status_code == 200,
                response_time_ms=elapsed_ms,
                status_code=response.status_code,
                error=None if response.status_code == 200 else response.text[:200]
            )

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            return LoadTestResult(
                success=False,
                response_time_ms=elapsed_ms,
                status_code=0,
                error=str(e)[:200]
            )

    async def run_concurrent_requests(
        self,
        num_requests: int,
        concurrency: int,
        endpoint: str = "/generate"
    ) -> LoadTestStats:
        """Run load test with specified concurrency"""
        self.stats = LoadTestStats()
        self.stats.start_time = time.perf_counter()

        semaphore = asyncio.Semaphore(concurrency)
        completed = 0

        async def bounded_request(client: httpx.AsyncClient):
            nonlocal completed
            async with semaphore:
                result = await self.make_request(client, endpoint)
                self.stats.total_requests += 1
                if result.success:
                    self.stats.successful_requests += 1
                    self.stats.response_times.append(result.response_time_ms)
                else:
                    self.stats.failed_requests += 1
                    error_key = result.error[:50] if result.error else "Unknown"
                    self.stats.errors[error_key] = self.stats.errors.get(error_key, 0) + 1
                completed += 1
                return result

        async with httpx.AsyncClient() as client:
            # First, verify the server is up
            try:
                health_response = await client.get(f"{self.base_url}/health", timeout=10)
                if health_response.status_code != 200:
                    console.print(f"[red]Server health check failed: {health_response.status_code}[/red]")
                    return self.stats
            except Exception as e:
                console.print(f"[red]Cannot connect to server: {e}[/red]")
                return self.stats

            console.print(f"[green]Server is healthy. Starting load test...[/green]")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:
                task = progress.add_task(
                    f"[cyan]Running {num_requests} requests (concurrency: {concurrency})",
                    total=num_requests
                )

                tasks = []
                for _ in range(num_requests):
                    tasks.append(bounded_request(client))

                # Process results as they complete
                for coro in asyncio.as_completed(tasks):
                    await coro
                    progress.update(task, completed=completed)

        self.stats.end_time = time.perf_counter()
        return self.stats

    async def run_health_check_test(
        self,
        num_requests: int = 1000,
        concurrency: int = 100
    ) -> LoadTestStats:
        """Quick test using health endpoint"""
        self.stats = LoadTestStats()
        self.stats.start_time = time.perf_counter()

        semaphore = asyncio.Semaphore(concurrency)
        completed = 0

        async def bounded_request(client: httpx.AsyncClient):
            nonlocal completed
            async with semaphore:
                start = time.perf_counter()
                try:
                    response = await client.get(
                        f"{self.base_url}/health",
                        timeout=self.timeout
                    )
                    elapsed_ms = (time.perf_counter() - start) * 1000
                    self.stats.total_requests += 1
                    if response.status_code == 200:
                        self.stats.successful_requests += 1
                        self.stats.response_times.append(elapsed_ms)
                    else:
                        self.stats.failed_requests += 1
                except Exception as e:
                    elapsed_ms = (time.perf_counter() - start) * 1000
                    self.stats.total_requests += 1
                    self.stats.failed_requests += 1
                    error_key = str(e)[:50]
                    self.stats.errors[error_key] = self.stats.errors.get(error_key, 0) + 1
                completed += 1

        async with httpx.AsyncClient() as client:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:
                task = progress.add_task(
                    f"[cyan]Running {num_requests} health check requests (concurrency: {concurrency})",
                    total=num_requests
                )

                tasks = []
                for _ in range(num_requests):
                    tasks.append(bounded_request(client))

                for coro in asyncio.as_completed(tasks):
                    await coro
                    progress.update(task, completed=completed)

        self.stats.end_time = time.perf_counter()
        return self.stats

    async def run_generate_test(
        self,
        num_requests: int = 50,
        concurrency: int = 5
    ) -> LoadTestStats:
        """Load test on PDF generation endpoint"""
        return await self.run_concurrent_requests(
            num_requests, concurrency, endpoint="/generate"
        )

    def print_results(self, title: str = "Load Test Results"):
        """Print formatted results"""
        console.print()
        console.print(f"[bold blue]{'='*60}[/bold blue]")
        console.print(f"[bold blue]{title:^60}[/bold blue]")
        console.print(f"[bold blue]{'='*60}[/bold blue]")

        # Summary table
        table = Table(title="Summary", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")

        table.add_row("Total Requests", str(self.stats.total_requests))
        table.add_row("Successful", f"{self.stats.successful_requests} ({self.stats.success_rate:.1f}%)")
        table.add_row("Failed", str(self.stats.failed_requests))
        table.add_row("Duration", f"{self.stats.duration_seconds:.2f}s")
        table.add_row("Requests/Second", f"{self.stats.requests_per_second:.2f}")

        console.print(table)

        # Response time table
        if self.stats.response_times:
            rt_table = Table(title="Response Times (ms)", show_header=True, header_style="bold magenta")
            rt_table.add_column("Percentile", style="cyan")
            rt_table.add_column("Time (ms)", style="green", justify="right")

            rt_table.add_row("Min", f"{self.stats.min_response_time:.2f}")
            rt_table.add_row("Avg", f"{self.stats.avg_response_time:.2f}")
            rt_table.add_row("P50 (Median)", f"{self.stats.p50_response_time:.2f}")
            rt_table.add_row("P95", f"{self.stats.p95_response_time:.2f}")
            rt_table.add_row("P99", f"{self.stats.p99_response_time:.2f}")
            rt_table.add_row("Max", f"{self.stats.max_response_time:.2f}")

            console.print(rt_table)

        # Errors table
        if self.stats.errors:
            err_table = Table(title="Errors", show_header=True, header_style="bold red")
            err_table.add_column("Error", style="red")
            err_table.add_column("Count", style="yellow", justify="right")

            for error, count in sorted(self.stats.errors.items(), key=lambda x: x[1], reverse=True)[:10]:
                err_table.add_row(error[:60], str(count))

            console.print(err_table)

        console.print()


async def run_full_load_test():
    """Run comprehensive load test"""
    tester = LoadTester()

    console.print("\n[bold yellow]Resume Agent Template Engine - Load Test[/bold yellow]")
    console.print("[dim]Testing with 1 CPU and 2GB memory configuration[/dim]\n")

    # Test 1: Health endpoint (baseline)
    console.print("[bold cyan]Test 1: Health Endpoint Baseline[/bold cyan]")
    await tester.run_health_check_test(num_requests=500, concurrency=50)
    tester.print_results("Health Endpoint Performance")

    # Test 2: PDF Generation - Light load
    console.print("\n[bold cyan]Test 2: PDF Generation - Light Load (5 concurrent)[/bold cyan]")
    await tester.run_generate_test(num_requests=20, concurrency=5)
    tester.print_results("PDF Generation - Light Load")

    # Test 3: PDF Generation - Medium load
    console.print("\n[bold cyan]Test 3: PDF Generation - Medium Load (10 concurrent)[/bold cyan]")
    await tester.run_generate_test(num_requests=30, concurrency=10)
    tester.print_results("PDF Generation - Medium Load")

    # Test 4: PDF Generation - Heavy load
    console.print("\n[bold cyan]Test 4: PDF Generation - Heavy Load (20 concurrent)[/bold cyan]")
    await tester.run_generate_test(num_requests=40, concurrency=20)
    tester.print_results("PDF Generation - Heavy Load")

    # Final summary
    console.print("\n[bold green]=" * 60)
    console.print("[bold green]LOAD TEST COMPLETE[/bold green]")
    console.print("[bold green]=" * 60)
    console.print("\n[dim]Note: PDF generation includes LaTeX compilation which is CPU-intensive.[/dim]")
    console.print("[dim]For 1 CPU / 2GB memory, expect ~2-5 requests/second for PDF generation.[/dim]\n")


if __name__ == "__main__":
    asyncio.run(run_full_load_test())
