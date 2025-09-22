from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    aws_synthetics as synthetics,
    aws_lambda as lambda_,
    aws_events as events_,
    aws_events_targets as targets,
    # lamba_. or import removal policy. one of the two
    aws_logs as logs,
    RemovalPolicy,

    Duration,
    aws_iam as iam,

    aws_cloudwatch as cloudwatch,
    aws_codedeploy as codedeploy,
)
from constructs import Construct
from modules import constants


class EugeneStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # function to run WHLambda file
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/README.html#function-timeout
        fn = lambda_.Function(self, "WHLambda",
            runtime=lambda_.Runtime.PYTHON_3_13,
            timeout=Duration.minutes(10),
            handler="WHLambda.lambda_handler",
            code=lambda_.Code.from_asset("./modules"),
        )
        fn.apply_removal_policy(RemovalPolicy.DESTROY)
        
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_scheduler/README.html
        schedule = events_.Schedule.rate(Duration.minutes(1)) # 1 for testing, 30 for normal
        target = targets.LambdaFunction(fn)
        rule = events_.Rule(self, "Rule",
            schedule=schedule,
            targets=[target],
            description="This rule triggers the WHLambda function every 30 minutes."
        )
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_iam/PolicyStatement.html
        fn.add_to_role_policy(iam.PolicyStatement(
            actions=["cloudwatch:PutMetricData"],
            resources=["*"],
        ))

        urls = [
            "https://www.youtube.com",
            "https://www.google.com",
            "https://www.instagram.com",
        ]

        for url in urls:
            # To create metrics: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Metric.html
            avail_metric = cloudwatch.Metric(
                namespace=constants.URL_NAMESPACE,
                metric_name=constants.URL_MONITOR_AVAILABILITY,
                period=Duration.minutes(5),
                label=f"Availability {url}",
                dimensions_map={"URL": url}
            )
            # To create alarms: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Alarm.html
            avail_alarm = cloudwatch.Alarm(self, f"AvailAlarm-{url}",
                threshold=1,
                comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
                evaluation_periods=1, # We want to compare every value of the metric
                metric=avail_metric,
                treat_missing_data = cloudwatch.TreatMissingData.BREACHING,
                alarm_description=f"Alarm when the availability metric is below 1 for {url}"
                
            )

            latency_metric = cloudwatch.Metric(
                namespace=constants.URL_NAMESPACE,
                metric_name=constants.URL_MONITOR_LATENCY,
                period=Duration.minutes(5),
                label=f"Latency {url}",
                dimensions_map={"URL": url}
            )
            latency_alarm = cloudwatch.Alarm(self, f"LatencyAlarm-{url}",
                threshold=250,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                evaluation_periods=1, # We want to compare every value of the metric
                metric=latency_metric,
                treat_missing_data = cloudwatch.TreatMissingData.BREACHING,
                alarm_description=f"Alarm when the latency metric is above 250ms for {url}"
            )
            response_size_metric = cloudwatch.Metric(
                namespace=constants.URL_NAMESPACE,
                metric_name=constants.URL_MONITOR_SIZE,
                period=Duration.minutes(5),
                label = f"Response Size {url}",
                dimensions_map={"URL": url}
            )
            response_size_alarm = cloudwatch.Alarm(self, f"ResponseSizeAlarm-{url}",
                threshold=450000,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                evaluation_periods=1, # We want to compare every value of the metric
                metric=response_size_metric,
                treat_missing_data = cloudwatch.TreatMissingData.BREACHING,
                alarm_description="Alarm when the Response size metric is above 450000 bytes",
            )
            # set up dashboard from stack: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/GraphWidget.html

        metrics = [avail_metric, latency_metric, response_size_metric]

        # Setup dashboard from stack: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Dashboard.html
        dashboard = cloudwatch.Dashboard(
            scope = self, 
            id = "dashboard",
            dashboard_name = "URL_Monitor_Dashboard",
        )
        for metric_name, title in [
            (constants.URL_MONITOR_AVAILABILITY, "Availability"),
            (constants.URL_MONITOR_LATENCY, "Latency"),
            (constants.URL_MONITOR_SIZE, "Response Size")
        ]:
            metrics_for_widget = []
            for url in urls:
                metric = cloudwatch.Metric(
                    namespace=constants.URL_NAMESPACE,
                    metric_name=metric_name,
                    period=Duration.minutes(1),
                    dimensions_map={"URL": url},
                    label=url,
                )
                metrics_for_widget.append(metric)

            # configure displays of graphs: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/GraphWidget.html
            widget = cloudwatch.GraphWidget(
                title=title,
                left=metrics_for_widget,
                legend_position=cloudwatch.LegendPosition.RIGHT,
                period=Duration.minutes(1), # every minute it should show metric on dashboard
                left_y_axis=cloudwatch.YAxisProps(min=0),  # start at 0
            )
            dashboard.add_widgets(widget)

''' No more recordings for the tutoral anymore, so take your own notes
- To reference you code make sure you get it from AWS cdk links
- roles are needed later on 
- move constants from WHLambda to a constants.py file in module

- in the cloudwatch logs if it has start and end, it means the function is working


To create a dashboard:
- Lambda function, publish metrics to cloudwatch ( this has been done)
- Based on these metrics we want alarms ( set threshold for latency and availability 
    - if theshold is bellow 1 then website not avialble)
    - if latency is above x ammount, raise alarm
- From these alarms we want a simple notification service (email and sms stating that one of the metrics has an alarm)
    It also triggers another lambda (Dynamo DB), once it runs it writes alarm informaiton into Dynamo Database
- From these we want to log the information in a Dynamo DB ()

- Stack file contains all components of your infrastructure (alarms, lambda functions, synth, dynamo DB) not your metrics as thats on lambda 
- Lambda is using SDK, stack file uses CDK
- Make it reference using one namespace

- We currently have custom metrics


Metric: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Metric.html

# Create a metric
metric = cloudwatch.Metric(
    namespace="AWS/EC2",
    metric_name="CPUUtilization",
    statistic="Average",
    period=Duration.minutes(5)
)

In Boto3 the dimentiosn is a list of dictionaries

Aim for 18 lines total on dashboard



'''