
# Welcome to your CDK Python project!

This is a blank project for CDK development with Python.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

# Website Monitoring with AWS CDK

## Overview
This project deploys a **canary monitoring system** using AWS CDK.  
A Lambda function crawls multiple websites every 5 minutes and publishes custom metrics (Availability, Latency, HTTP Status) to CloudWatch.  
CloudWatch dashboards display the metrics, and alarms notify via SNS email when thresholds are breached.

---

## Architecture
- **Lambda Function** – Crawls the target websites.  
- **EventBridge Rule** – Triggers the Lambda every 5 minutes.  
- **CloudWatch Metrics** – Custom metrics: Availability, Latency, Status.  
- **CloudWatch Dashboard** – Graphs to visualize metrics per website.  
- **CloudWatch Alarms** – Threshold-based alerts (e.g., latency > 1s, availability = 0).  
- **SNS Topic** – Sends email notifications when alarms go into ALARM state.

---

## Deployment

### Prerequisites
- AWS CLI configured (`aws configure`)  
- Node.js and npm  
- Python 3.9+  
- AWS CDK installed (`npm install -g aws-cdk`)  

### Steps
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
