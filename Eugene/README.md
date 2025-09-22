
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
$ python3 -m venv .venv
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

# AWS Lambda Monitoring with CDK and Synthetics Canary
## Update 4/8/25

This project integrates an AWS Lambda function and an AWS Synthetics Canary using AWS CDK (Python) to monitor an external web resource. The Canary simulates a real user visiting a webpage every 5 minutes, helping track the availability and performance of the resource.


What it does:
- Deploys lambda function with a simple hello message
- Sets up a Synthetics Canary that periodically checks the health of a web page (every 5 minutes).
- Metrics and alarms setup is commented out for the time being, and will be added in a future update.

How to deploy:
- AWS CLI configured with valid credientials
- Python 3.11+
- AWS CDK v2
- Node.js (for Canary Puppeteer runtime)

Steps to deploy:
- Open AWS Lambda Console.
- Click “Create function” → select "Author from scratch".
- Name the function (e.g., MyLambda) and choose the runtime (e.g., Python or Node.js).
- Paste the Lambda code into the inline editor.
- Save and deploy the function using the AWS Console UI.

Testing:
- after doing cdk synth, deploy go onto the lambda function website and you should see this output
    {
    "statusCode": 200,
    "body": "\"Hello from Lambda!\""
    // there is also some mention of latency and availability
    }

Quality Characteristics:
- Performance: 
    - Canary runs every 5 minutes with a 1-minute timeout 
    to minimise latency and catch outages quickly.
- Usability: 
    - Canary can be built upon with matrics later on


Future Improvements:
- Add Cloudwatch Alarms for Lambda metrics

# AWS - Building the Foundation of DevOps
## Update 18/8/25
This project integrates the availability and latency metrics into the Web Health module. The crawler runs periodically every 5 min to write the availability and latency for metrics of a website. Using the Cloudwatch it produces a dashboard showing the web health(metrics) of each website.


What it does:
- Display the availabilty and latency of Google, Youtube and Facebook websites
- Publishes metrics to CloudWatch
- Display results in a CloudWatch dashboard

How to deploy:
- AWS CLI configured with valid credientials
- Python 3.11+
- AWS CDK v2
- Node.js (for Canary Puppeteer runtime)

Steps to deploy:
- On visual studio code, type cdk synth, then cdk deploy. This will deploy the code onto
the Lambda website.
-  Once on the lambda website your code will appear in a function, and once you make a test,
it will test the websites.
- After testing, go to the Cloudwatch dashboard and you will see graphs of the metrics of the website

Testing:
- After doing the test it should show this in the console (function logs)
    Health check for https://www.youtube.com: {'
        url': 'https://www.youtube.com', 
        'availability': 1, 
        'latency_ms': 478.26457023620605, 
        'status_code': 200
    }

Quality Characteristics:
- Security: 
    - Uses IAM least privilege by restricting the Lambda function to only the necessary cloudwatch:PutMetricData action. 
    - AWS credentials and access are managed through standard AWS identity and permissions.
- Performance: 
    - Canary runs every 5 minutes with a 1-minute timeout to minimise latency and catch outages quickly.
    - Latency metrics allow performance monitoring of external sites in near real-time.
    - Availability metrics show if the website is a available (1) or not available (0)
- Reliability
    - Lambda and CloudWatch provide built-in fault tolerance. If a site fails, the metric reports unavailability, making outages visible on the dashboard.
    - Scheduled EventBridge rules guarantee regular execution.
- Usability:
    - Results are visible in CloudWatch dashboards, and the code is modular (separate Lambda handler, metric publisher, and CDK stack), making it easy to extend with more sites or metrics in the future.

Future Improvements:
- The log removal policy is not functioning
- Testing fails for the third website (fixed now due to timeout of lambda being too short)
- Add a third metric to test for.

# AWS - Building the Foundation of DevOps
## Update 22/8/25
This update involves the additoinal metric response size into the Web Health Module. It also includes the ability to create a Cloudwatch dashboard to monitor all three metrics of three websites give. It includes alarms that alert the user if the latency or response size is too much to handle or if the availability is less than 1, meaning not available. It also includes a constants file to to centralize configuration values (such as URLs, thresholds, and metric names), and has fixed all the future improvements from the previous update.

What it does:
- Display the availabilty, latency, and response size of Google, Youtube and Facebook websites
- Creates its on Cloudwatch dashboard
- Publishes metrics to CloudWatch
- Display results in a CloudWatch dashboard

How to deploy:
- AWS CLI configured with valid credientials
- Python 3.11+
- AWS CDK v2
- Node.js (for Canary Puppeteer runtime)

Steps to deploy:
- On visual studio code, type cdk synth, then cdk deploy. This will deploy the code onto
the Lambda website.
-  Once on the lambda website your code will appear in a function, and once you make a test,
it will test the websites.
- After testing, go to the Cloudwatch dashboard and you will see three graphs each representing a metric, with a key indicating each website.

Testing:
- After pressing the test button on lambda, go to cloudwatch -> all alarms, this will show which metrics have triggered an alarm.
- Also after pressing the test button, go to cloudwatch -> Dashboards -> URL_Monitor_Dashboard, you should all the metrics of the websites, shown in the graphs.

Quality Characteristics:
- Security: 
    - Uses IAM least privilege by restricting the Lambda function to only the necessary cloudwatch:PutMetricData action. 
    - AWS credentials and access are managed through standard AWS identity and permissions.

- Performance: 
    - Canary runs every 5 minutes with a 1-minute timeout to minimise latency and catch outages quickly.
    - Latency metrics allow performance monitoring of external sites in near real-time.
    - Availability metrics show if the website is a available (1) or not available (0).
    - Response size metric allows monitoring of abnormal increases/decreases in webpage content size that may indicate outages, errors, or changes.
    - The metrics are checked every minuete to provide more data points to capture and display on the graphs.
    - Scalability: It can perform metrics on any number of websites, as long as you add the website link in the url list that is on WHLambda and stack file.

- Reliability
    - Lambda and CloudWatch provide built-in fault tolerance. If a site fails, the user will have an alarm appear in Cloudwatch indicating that it has been set off. 
    - The metric reports if the website exceeds the limit on response size and latency, or if the website is not available.

- Usability:
    - Results are visible in CloudWatch dashboards, and the code is modular (separate Lambda handler, metric publisher, and CDK stack), making it easy to extend with more sites or metrics in the future.

Future Improvements:
- Add SMS/email feature where the user is to be notified if a metric's alarm has been sent off.
- Implement another lambda (Dynamo DB) to write alarm information into a Dynamo Database, from this we want to log the information in a Dynamo DB.
