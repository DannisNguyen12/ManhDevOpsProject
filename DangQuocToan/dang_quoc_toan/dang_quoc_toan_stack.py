# import necessary libraries
from tkinter import RIGHT
from aws_cdk import (
    RemovalPolicy,
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_events as events_,
    aws_events_targets as targets_,
    aws_iam as iam,
    aws_cloudwatch as cloudwatch,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_cloudwatch_actions as cw_actions
)
from constructs import Construct
import os
import json

NAMESPACE = "THOMASPROJECT_WSU2025"


class DangQuocToanStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        #--- Load website so we can create per-URL alarms/widgets
        websites_path = os.path.join(os.path.dirname(__file__), "..", "modules", "website.json")
        with open(websites_path, "r", encoding = "utf-8") as f:
            website_list = [entry["url"] for entry in json.load(f)]
        
        # Create and define the Lambda function
        fn = _lambda.Function(self, "WHlambda",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="WHLambda.lambda_handler",
            code=_lambda.Code.from_asset("./modules"),
            timeout=Duration.seconds(30),
        )

        # Give the Lambda function permissions to publish metrics to CLoudWatch
        fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"],
            )
        )

        fn.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
        )
        
        # Schedule for scheduled events rules
        schedule= events_.Schedule.rate(Duration.minutes(5))

        # Create the event target
        target = targets_.LambdaFunction(fn)
        
        # AWS evetns_.Rule
        events_.Rule (
            self, "CanaryScheduleRule",
            schedule=schedule,
            targets=[target],
            description="This is a test rule that invokes a lambda function every 5 minutes"
        )

        # SNS Topic for alarms (uncomment and add your email)
        topic = sns.Topic(self, "WebHealthAlarms", topic_name="web-health-alarms")
        topic.add_subscription(subs.EmailSubscription("22119278@student.westernsydney.edu.au"))

        # Create CloudWatch metrics with dimension for each URL
        def metric_availability(url: str) -> cloudwatch.Metric:
            return cloudwatch.Metric(
                namespace=NAMESPACE,
                metric_name="availability",
                period=Duration.minutes(5),
                label=f"availability: {url}",
                dimensions_map={"WebsiteName": url},
                statistic="avg"
            )
        
        def metric_latency(url: str) -> cloudwatch.Metric:
            return cloudwatch.Metric(
                namespace=NAMESPACE,
                metric_name="latency",
                period=Duration.minutes(5),
                label=f"latency: {url}",
                dimensions_map={"WebsiteName": url},
                statistic="avg"
            )
        
        def metric_status(url: str) -> cloudwatch.Metric:
            return cloudwatch.Metric(
                namespace=NAMESPACE,
                metric_name="status",
                period=Duration.minutes(5),
                label=f"status: {url}",
                dimensions_map={"WebsiteName": url},
                statistic="avg"
            )
        
        # --- Alarms per URL
        alarms = []
        for url in website_list:
            avail = metric_availability(url)
            lat= metric_latency(url)
            stat = metric_status(url)

        # Availability alarm: alarm when < 1 (site down or non-2xx/3xx)
            avail_alarm = cloudwatch.Alarm(
            self, f"AvailabilityAlarm-{self._sanitize_id(url)}",
            metric=avail,
            threshold=1,
            comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
            evaluation_periods=1,
            datapoints_to_alarm=1,
            treat_missing_data = cloudwatch.TreatMissingData.BREACHING,
            alarm_description=f"Availability < 1 for {url}"
        )

        # Latency alarm: > 2000 ms (tune as needed)
            latency_alarm = cloudwatch.Alarm(
            self, f"LatencyAlarm-{self._sanitize_id(url)}",
            metric=lat,
            threshold=2000,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            evaluation_periods=1,
            datapoints_to_alarm=1,
            treat_missing_data = cloudwatch.TreatMissingData.BREACHING,
            alarm_description=f"Latency > 2000 ms for {url}"
        )
            
        # Create an SNS topic for alarm notifications
            status_alarm = cloudwatch.Alarm(
            self, f"StatusAlarm-{self._sanitize_id(url)}",
            metric=stat,
            threshold=399,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            evaluation_periods=1,
            datapoints_to_alarm=1,
            treat_missing_data = cloudwatch.TreatMissingData.BREACHING,
            alarm_description=f"Status > 399 for {url}"
            ) 
            avail_alarm.add_alarm_action(cw_actions.SnsAction(topic))
            latency_alarm.add_alarm_action(cw_actions.SnsAction(topic))
            status_alarm.add_alarm_action(cw_actions.SnsAction(topic))
            alarms.extend([avail_alarm, latency_alarm, status_alarm])

        # Create a graph widget for availability metric
        avail_widget = cloudwatch.GraphWidget(
            title = "Availability (avg by URL, 5m)",
            left = [metric_availability(url) for url in website_list],
            legend_position=cloudwatch.LegendPosition.RIGHT,
            period=Duration.minutes(5)
        )

        # Create a graph widget for the latency metric
        latency_widget = cloudwatch.GraphWidget(
            title = "Latency (avg by URL, 5m)",
            left = [metric_latency(url) for url in website_list],
            legend_position=cloudwatch.LegendPosition.RIGHT,
            period=Duration.minutes(5)
        )

        # Create a graph widget for the status code metric
        status_code_widget = cloudwatch.GraphWidget(
            title = "HTTP Status (avg by URL, 5m)",
            left = [metric_status(url) for url in website_list],
            legend_position=cloudwatch.LegendPosition.RIGHT,
            period=Duration.minutes(5)
        )

        # Create a dashboard
        dashboard = cloudwatch.Dashboard(
            scope = self,
            id = "WHLambdaDashboard",
            dashboard_name = "URLMONITOR_DASHBOARD",
            widgets=[
                    [avail_widget], 
                    [latency_widget], 
                    [status_code_widget]
        
        ]
        )

        # Helper for ID-safe names (CDK IDs must avoid problematic chars)
    def _sanitize_id(self, url: str) -> str:
        return(
            url.replace("https://", "")
            .replace("http://", "")
            .replace("/", "_")
            .replace(".", "_")[:100]
)
