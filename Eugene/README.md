
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

# 📈 AWS Lambda Monitoring with CDK and Synthetics Canary
## Update 4/8/24

This project integrates an AWS Lambda function and an AWS Synthetics Canary 
using AWS CDK (Python) to monitor an external web resource. The Canary 
simulates a real user visiting a webpage every 5 minutes, helping 
track the availability and performance of the resource.


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
- Performance: Canary runs every 5 minutes with a 1-minute timeout 
    to minimise latency and catch outages quickly.
- Usability: Canary can be built upon with matrics later on


Future Improvements:
- Add Cloudwatch Alarms for Lambda metrics