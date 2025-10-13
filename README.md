# Web Crawler and Website Monitoring System

A comprehensive AWS CDK-based solution for website monitoring, web crawling, and automated deployment with rollback capabilities.

## 🏗️ Architecture Overview

### Project 1: Web Crawler and Monitoring Canary

#### Core Components
- **Website Monitor Lambda**: Performs availability checks and web crawling
- **CloudWatch Metrics**: Tracks availability, latency, and operational health
- **CloudWatch Alarms**: Automated alerting for availability and performance issues
- **SNS/SQS Notifications**: Tagged notifications for alarm filtering
- **DynamoDB**: Alarm history logging and website configuration storage

#### Key Features
- **Multi-stage Pipeline**: Beta → Gamma → Production with test blockers
- **Automated Rollback**: Triggers on alarm conditions or health check failures
- **Operational Metrics**: Memory usage, crawl time, and processing health
- **Comprehensive Testing**: Unit, integration, and performance tests

### Project 2: CRUD API for Website Management

#### API Gateway Endpoints
- `GET/POST/PUT/DELETE /websites` - Website configuration management
- `GET /crawler/status` - Real-time crawler status
- `POST /crawler/start` - Manual crawler execution

#### Features
- **Dynamic Website Management**: Add/remove websites without code changes
- **Real-time Monitoring**: Live crawler status and metrics
- **Performance Tracking**: DynamoDB read/write time monitoring

## 🚀 Quick Start

### Prerequisites
```bash
# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Install AWS CDK
npm install -g aws-cdk

# Configure AWS credentials
aws configure
```

### Deployment

#### Single Environment Deployment
```bash
# Synthesize CloudFormation templates
cdk synth

# Deploy to default account/region
cdk deploy
```

#### Multi-Stage Pipeline Deployment
```bash
# Bootstrap CDK (one-time setup)
cdk bootstrap

# Deploy pipeline
cdk deploy WebCrawlerPipelineStack

# Monitor pipeline execution
aws codepipeline get-pipeline-state --name WebCrawlerPipeline
```

### Testing
```bash
# Run unit tests
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Run performance tests
pytest tests/performance/ -v

# Run all tests with coverage
pytest --cov=manh_dev_ops_project --cov-report=html
```

## 📊 Monitoring and Observability

### CloudWatch Dashboards
- **Website Monitoring**: Availability and latency metrics per website
- **Crawler Operations**: Memory usage, crawl time, pages processed
- **Pipeline Health**: Deployment status and rollback events

### Key Metrics
```javascript
// Website Monitoring Namespace
{
  "Namespace": "WebsiteMonitoring",
  "Metrics": ["Availability", "Latency", "StatusCode"]
}

// Crawler Operations Namespace
{
  "Namespace": "WebCrawler/Operational",
  "Metrics": ["CrawlTime", "PagesCrawled", "MemoryUsage"]
}
```

### Alarms and Notifications
- **Availability Alarm**: Triggers when uptime < 95%
- **Latency Alarm**: Triggers when response time > 2000ms
- **Memory Alarm**: Triggers when Lambda memory > 80%
- **Crawl Time Alarm**: Triggers when crawling takes > 30 seconds

## 🔧 Configuration

### Environment Variables
```bash
# Crawler Configuration
MAX_CRAWL_DEPTH=2          # Maximum link depth to crawl
MAX_PAGES_PER_SITE=10      # Maximum pages per website
CRAWL_TIMEOUT=30           # HTTP request timeout in seconds

# Pipeline Configuration
PIPELINE_NAME=WebCrawlerPipeline
ROLLBACK_TIMEOUT=30        # Minutes to wait for rollback completion

# Monitoring Configuration
ALARM_EMAIL=your-email@example.com
HEALTH_CHECK_TIMEOUT=300   # Seconds for health checks
```

### Website Configuration
```json
{
  "id": "unique-website-id",
  "name": "Example Website",
  "url": "https://example.com",
  "enabled": true,
  "createdAt": "2024-01-15T10:00:00Z",
  "updatedAt": "2024-01-15T10:00:00Z"
}
```

## 🧪 Testing Strategy

### Unit Tests
- Lambda function logic
- API validation and error handling
- CloudWatch metrics publishing
- DynamoDB operations

### Integration Tests
- End-to-end API workflows
- CloudWatch alarm publishing
- SNS/SQS message processing
- Multi-website crawling scenarios

### Performance Tests
- Crawler speed and memory usage
- DynamoDB read/write performance
- Concurrent website processing
- Large content handling

### Pipeline Tests
- CDK synthesis validation
- Security scanning (Bandit, Safety)
- Health check validation
- Rollback functionality

## 🔄 CI/CD Pipeline

### Stages
1. **Source**: GitHub webhook triggers
2. **Beta**: Unit tests, security scans
3. **Gamma**: Integration tests, performance validation
4. **Production**: Manual approval, health checks, automated rollback

### Test Blockers
- Unit test failure rate > 0%
- Security vulnerabilities found
- Performance regression > 10%
- Health check failures

### Automated Rollback Triggers
- CloudWatch alarms in ALARM state
- Health check failures
- Memory usage > 85%
- Deployment timeouts

## 📈 API Reference

### Website Management
```http
GET    /websites           # List all websites
POST   /websites           # Create website
GET    /websites/{id}      # Get website details
PUT    /websites/{id}      # Update website
DELETE /websites/{id}      # Delete website
```

### Crawler Management
```http
GET    /crawler/status     # Get crawler status
POST   /crawler/start      # Trigger manual crawl
```

### Response Format
```json
{
  "websites": [
    {
      "id": "string",
      "name": "string",
      "url": "string",
      "enabled": true,
      "createdAt": "ISO8601",
      "updatedAt": "ISO8601"
    }
  ]
}
```

## 🛠️ Development

### Project Structure
```
manh_dev_ops_project/
├── website_monitor_stack.py     # Main infrastructure
├── api_stack.py                 # API Gateway and Lambda
├── web_crawler_pipeline.py      # CI/CD pipeline
├── pipeline_stack.py           # Legacy pipeline (deprecated)
modules/
├── monitor/                    # Website monitoring Lambda
├── api_handler/               # API Lambda functions
├── alarm_handler/             # Alarm processing Lambda
tests/
├── unit/                      # Unit tests
├── integration/              # Integration tests
├── performance/              # Performance tests
scripts/
├── health_check.py           # Deployment health validation
├── rollback_manager.py       # Automated rollback logic
```

### Adding New Websites
```bash
# Via API
curl -X POST https://your-api.com/websites \
  -H "Content-Type: application/json" \
  -d '{"name": "New Site", "url": "https://newsite.com", "enabled": true}'
```

### Customizing Crawler Behavior
```python
# In monitor/monitor.py
class WebsiteMonitor:
    def __init__(self):
        self.max_crawl_depth = int(os.environ.get('MAX_CRAWL_DEPTH', '2'))
        self.max_pages_per_site = int(os.environ.get('MAX_PAGES_PER_SITE', '10'))
        # Add custom crawling logic here
```

## 🔒 Security

### Best Practices
- **IAM Least Privilege**: Minimal required permissions
- **VPC Deployment**: Resources in private subnets
- **Encryption**: Data encrypted at rest and in transit
- **Security Scanning**: Automated vulnerability detection

### Compliance
- **SOC 2**: Infrastructure security controls
- **GDPR**: Data minimization and consent
- **HIPAA**: Protected health information handling (if applicable)

## 📚 Troubleshooting

### Common Issues

#### Pipeline Failures
```bash
# Check pipeline status
aws codepipeline get-pipeline-state --name WebCrawlerPipeline

# View CloudWatch logs
aws logs tail /aws/codebuild/WebCrawlerPipeline
```

#### Lambda Timeouts
```bash
# Increase timeout in CDK
timeout=Duration.minutes(15)

# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace WebCrawler/Operational \
  --metric-name CrawlTime
```

#### Alarm Not Triggering
```bash
# Check alarm configuration
aws cloudwatch describe-alarms --alarm-names WebsiteAvailabilityAlarm

# Verify metrics are publishing
aws cloudwatch list-metrics --namespace WebsiteMonitoring
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Code Standards
- **Python**: PEP 8 with type hints
- **Testing**: pytest with >= 80% coverage
- **Documentation**: Inline docstrings and README updates
- **Security**: No hardcoded secrets or credentials

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting guide
2. Review CloudWatch logs and metrics
3. Open an issue with detailed information
4. Include relevant log snippets and configuration

---

**Note**: This system is designed for monitoring and crawling publicly accessible websites only. Ensure compliance with website terms of service and robots.txt directives.