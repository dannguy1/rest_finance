# Grafana Dashboards for Financial Data Processor

This directory contains Grafana dashboard JSON definitions for monitoring the Financial Data Processor application.

## Dashboards

### 1. System Health (`system_health.json`)
Monitors overall system health and resource usage:
- CPU Usage
- Memory Usage  
- Disk Usage
- Active Processing Jobs
- HTTP Request Rate
- HTTP Request Duration (p95)

### 2. Processing Metrics (`processing_metrics.json`)
Tracks data processing performance:
- File Upload Rate
- Processing Duration (p95)
- Processing Errors Rate
- Records Processed Rate
- Files Processed by Status
- Upload File Size (avg)
- Cache Hit Rate

## Setup

### Prerequisites
- Prometheus server running and scraping `/health/prometheus` endpoint
- Grafana instance with Prometheus data source configured

### Import Dashboards

1. Open Grafana UI
2. Go to Dashboards → Import
3. Upload the JSON files from this directory
4. Select your Prometheus data source
5. Click Import

### Prometheus Configuration

Add this to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'financial-processor'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/health/prometheus'
    scrape_interval: 10s
```

## Metrics Endpoints

- `/health/prometheus` - Prometheus-format metrics
- `/health/metrics` - JSON format application metrics
- `/health/detailed` - Detailed health check with system info

## Dashboard Features

### Refresh Rates
All dashboards are configured with 10-second refresh intervals for near real-time monitoring.

### Time Ranges
Metrics use 5-minute rate calculations (`rate()[5m]`) for smooth graphs and accurate trend analysis.

### Alerts (Optional)
Consider setting up alerts for:
- CPU usage > 80%
- Memory usage > 85%
- Disk usage > 90%
- Processing error rate > 5%
- HTTP 5xx error rate > 1%

## Customization

You can customize these dashboards in Grafana UI:
1. Edit dashboard
2. Modify panels, queries, or thresholds
3. Save changes
4. Export JSON for version control

## Troubleshooting

### No Data Showing
1. Verify Prometheus is scraping the endpoint: `http://localhost:9090/targets`
2. Check Prometheus logs for scrape errors
3. Verify the application is running and accessible
4. Test the metrics endpoint directly: `curl http://localhost:8000/health/prometheus`

### Missing Metrics
1. Ensure the application is generating activity (uploads, processing)
2. Check application logs for errors
3. Verify prometheus_client is installed: `pip install prometheus-client`

## Production Recommendations

1. **Persistent Storage**: Configure Grafana with persistent storage for dashboards
2. **Authentication**: Enable Grafana authentication for production
3. **Backup**: Regularly backup dashboard JSON files
4. **Retention**: Configure Prometheus retention policy based on your needs
5. **High Availability**: Run Prometheus and Grafana in HA mode for production
