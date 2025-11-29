"""
Load testing with Locust for Financial Data Processor.

Usage:
    locust -f locustfile.py --host=http://localhost:8000
    
Then open http://localhost:8089 to configure and start the load test.

Target: 100+ files per day
- Average: ~4 files/hour
- Peak: ~10 files/hour during business hours
"""
import random
import time
from locust import HttpUser, task, between, events
from pathlib import Path
import csv
import io


class FinancialProcessorUser(HttpUser):
    """Simulates a user of the Financial Data Processor."""
    
    # Wait between 30-60 seconds between tasks (simulating real usage)
    wait_time = between(30, 60)
    
    def on_start(self):
        """Called when a user starts."""
        self.sources = ["bankofamerica", "chase", "restaurantdepot", "sysco", "gg", "ar"]
        self.file_counter = 0
    
    @task(5)
    def view_dashboard(self):
        """View the dashboard page."""
        self.client.get("/")
    
    @task(3)
    def view_source_page(self):
        """View a specific source page."""
        source = random.choice(self.sources)
        self.client.get(f"/source/{source}")
    
    @task(2)
    def get_available_sources(self):
        """Get list of available sources."""
        self.client.get("/api/process/sources")
    
    @task(2)
    def get_available_years(self):
        """Get available years for a source."""
        source = random.choice(self.sources)
        self.client.get(f"/api/process/years/{source}")
    
    @task(1)
    def upload_and_process_file(self):
        """Upload and process a CSV file (most important operation)."""
        source = random.choice(self.sources)
        
        # Generate sample CSV data
        csv_data = self.generate_sample_csv(source, rows=random.randint(10, 100))
        
        # Upload file
        files = {
            "file": (f"test_upload_{self.file_counter}.csv", csv_data, "text/csv")
        }
        
        with self.client.post(
            f"/api/files/upload/{source}",
            files=files,
            catch_response=True,
            name="/api/files/upload/[source]"
        ) as response:
            if response.status_code == 200:
                response.success()
                self.file_counter += 1
            else:
                response.failure(f"Upload failed: {response.status_code}")
    
    @task(1)
    def process_source(self):
        """Process data for a specific source."""
        source = random.choice(self.sources)
        
        with self.client.post(
            f"/api/process/process/{source}",
            json={},
            catch_response=True,
            name="/api/process/process/[source]"
        ) as response:
            if response.status_code in [200, 404]:  # 404 is OK if no files to process
                response.success()
            else:
                response.failure(f"Processing failed: {response.status_code}")
    
    @task(1)
    def get_processing_status(self):
        """Get processing status for a source."""
        source = random.choice(self.sources)
        self.client.get(f"/api/process/status/{source}")
    
    @task(1)
    def health_check(self):
        """Check application health."""
        self.client.get("/health/")
    
    @task(1)
    def view_analytics(self):
        """View analytics for a source."""
        source = random.choice(self.sources)
        self.client.get(f"/source/{source}/analytics")
    
    def generate_sample_csv(self, source: str, rows: int = 50) -> str:
        """Generate sample CSV data for testing."""
        output = io.StringIO()
        
        if source in ["bankofamerica", "chase", "gg", "ar"]:
            # Bank/merchant format
            fieldnames = ["Date", "Description", "Amount"]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for i in range(rows):
                writer.writerow({
                    "Date": f"0{random.randint(1, 9)}/{random.randint(10, 28)}/2024",
                    "Description": f"TEST TRANSACTION {i}",
                    "Amount": f"{random.uniform(-500, 500):.2f}"
                })
        else:
            # Supplier format (restaurantdepot, sysco)
            fieldnames = ["Date", "Description", "Total"]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for i in range(rows):
                writer.writerow({
                    "Date": f"0{random.randint(1, 9)}/{random.randint(10, 28)}/2024",
                    "Description": f"TEST INVOICE {i}",
                    "Total": f"{random.uniform(50, 5000):.2f}"
                })
        
        return output.getvalue()


class AdminUser(HttpUser):
    """Simulates an admin user performing monitoring tasks."""
    
    wait_time = between(60, 120)  # Check less frequently
    
    @task(5)
    def check_health(self):
        """Check detailed health status."""
        self.client.get("/health/detailed")
    
    @task(3)
    def check_metrics(self):
        """Check application metrics."""
        self.client.get("/health/metrics")
    
    @task(2)
    def check_prometheus_metrics(self):
        """Check Prometheus metrics."""
        self.client.get("/health/prometheus")
    
    @task(1)
    def check_readiness(self):
        """Check readiness probe."""
        self.client.get("/health/ready")
    
    @task(1)
    def check_liveness(self):
        """Check liveness probe."""
        self.client.get("/health/live")


# Custom events for reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts."""
    print("\n" + "="*50)
    print("Starting Financial Data Processor Load Test")
    print(f"Target: 100+ files/day (~4-10 files/hour)")
    print("="*50 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops."""
    print("\n" + "="*50)
    print("Load Test Complete")
    print("="*50 + "\n")
