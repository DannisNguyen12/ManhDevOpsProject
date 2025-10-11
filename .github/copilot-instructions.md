# AI Assistant Instructions for ManhDevOpsProject

## Project Overview
This is an AWS CDK project in Python that implements a website monitoring system with the following features:
- Monitors availability, latency, and status codes for configured websites
- Uses AWS Lambda for periodic checks
- Stores metrics in CloudWatch
- Generates alarms based on thresholds
- Records alarm history in DynamoDB
- Provides a CloudWatch dashboard for visualization

## Key Components

### Infrastructure (monitorStack.py)
- Main CDK stack defining all AWS resources
- Uses EventBridge for scheduling website checks every 5 minutes
- Creates CloudWatch dashboard with metrics for each monitored site
- Sets up SNS topic for alarm notifications
- Configures DynamoDB table for alarm history

### Website Monitoring (modules/Metrix.py)
- Lambda function that performs the actual website checks
- Collects three metrics per site:
  - Availability (1 if status 200-399, 0 otherwise)
  - Latency (milliseconds)
  - Status Code (HTTP response code)
- Pushes metrics to CloudWatch namespace 'WebTest'

### Alarm Handler (modules/alarm_handler.py)
- Lambda function that processes CloudWatch alarms
- Stores alarm details in DynamoDB for historical tracking
- Triggered by SNS notifications

## Project Conventions

### Configuration
- Website list and thresholds are defined in `monitorStack.py`:
  ```python
  websites = [
      {"name": "Google", "url": "https://www.google.com"},
      {"name": "Facebook", "url": "https://www.facebook.com"},
      {"name": "YouTube", "url": "https://www.youtube.com"}
  ]

  THRESHOLD_METRICS = {
      "latency": 100,
      "availability": 1,
      "status_code": 200
  }
  ```

### Development Workflow
1. Activate virtualenv:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # (or .venv\Scripts\activate.bat on Windows)
   ```
2. Install dependencies: `pip install -r requirements.txt`
3. Deploy changes: `cdk deploy`
4. Check differences: `cdk diff`
5. Run tests: Located in `tests/unit/`

### Project Structure
- `manh_dev_ops_project/`: Main project code
  - `monitorStack.py`: Infrastructure definition
  - `modules/`: Lambda function implementations
- `tests/`: Test files
- `cdk.json`: CDK configuration and context
- `requirements.txt`: Python dependencies

## Common Development Tasks
- Adding a new website to monitor: Update `websites` list in `monitorStack.py`
- Modifying alarm thresholds: Update `THRESHOLD_METRICS` in `monitorStack.py`
- Adding new metrics: Update both `Metrix.py` and `monitorStack.py`
- Changing check frequency: Modify `trigger_interval` in `monitorStack.py`