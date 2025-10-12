from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_dynamodb as dynamodb,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cloudwatch_actions,
    aws_iam as iam,
    Duration
)
from constructs import Construct
from typing import List

class WebMonitoringStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # -------DynamoDB Database Service------------
        # Create table for website configurations
        # Name as "Website", with partition key "id" (string)
        # Set removal policy to DESTROY for easy cleanup during development
        # Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/TableV2.html
        self.web_table = dynamodb.TableV2(
            self, "Website",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            )
        )
        # Create table for monitoring events
        # Name as "AlarmEvents", with partition key "timestamp" (string) and sort key "website" (string)
        # Set removal policy to DESTROY for easy cleanup during development
        # Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/TableV2.html
        self.events_table = dynamodb.TableV2(
            self, "AlarmEvents",
            partition_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="website",
                type=dynamodb.AttributeType.STRING
            )
        )

        # Create table for crawl results and content storage
        # Name as "CrawlResults", with partition key "target_id" and sort key "crawl_timestamp"
        # Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/TableV2.html
        self.crawl_results_table = dynamodb.TableV2(
            self, "CrawlResults",
            partition_key=dynamodb.Attribute(
                name="target_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="crawl_timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            time_to_live_attribute="ttl"
        )

        # ------------SNS Topic for alarms service------------
        # Create SNS topic for alarm notifications
        # Name as "WebMonitorAlarmTopic"
        # Add a default email subscription - for more emails can be added through AWS Console or manually add here as well
        # Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns/Topic.html
        self.alarm_topic = sns.Topic(self, "WebAlarmTopic")
        self.alarm_topic.add_subscription(subscriptions.EmailSubscription("long.nm187254@gmail.com"))

        # ------------ Build Lambda Function Service -----------
        # Build Lambda function for web crawling
        # Name as "WebCrawlerFunction"
        # Set environment variables for DynamoDB table names
        # Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Function.html
        self.crawler_lambda = _lambda.Function(
            self, "WebCrawlerFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("/Users/dannguyen/Downloads/DevOps/ManhDevOpsProject/modules/lambda_webcrawler"),
            handler="lambda_webcrawler.lambda_handler",
            environment={
                "TARGETS_TABLE": self.web_table.table_name,
                "CRAWL_RESULTS_TABLE": self.crawl_results_table.table_name,
                "EVENTS_TABLE": self.events_table.table_name,
            },
            timeout=Duration.minutes(10),  # Longer timeout for crawling
            memory_size=1024  # More memory for content processing
        )

        # Build Lambda function to handle SNS alarm notifications and write to DynamoDB
        # Name as "AlarmHandler"
        # Set environment variable for DynamoDB events table name
        # Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Function.html
        alarm_handler = _lambda.Function(
            self, "AlarmHandler",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="alarm_handler.lambda_handler",
            code=_lambda.Code.from_asset("/Users/dannguyen/Downloads/DevOps/ManhDevOpsProject/modules/alarm_handler"),
            environment={
                'ALARM_TABLE_NAME': self.events_table.table_name
            }
        )

        # From Lambda function to handle SNS alarm notifications and write to DynamoDB
        # Subscribe the Lambda to the SNS topic
        # Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns_subscriptions/LambdaSubscription.html
        self.alarm_topic.add_subscription(subscriptions.LambdaSubscription(alarm_handler))
        # Grant the Lambda write permissions to the DynamoDB table
        self.events_table.grant_write_data(alarm_handler)

        # Grant the crawler Lambda read/write permissions to the DynamoDB tables
        # Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/TableV2.html#aws_cdk.aws_dynamodb.TableV2.grant_read_data
        # Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/TableV2.html#aws_cdk.aws_dynamodb.TableV2.grant_write_data
        self.web_table.grant_read_data(self.crawler_lambda)
        self.crawl_results_table.grant_read_write_data(self.crawler_lambda)
        self.events_table.grant_write_data(self.crawler_lambda)

        # ------------ EventBridge Rule to trigger Lambda every 5 minutes -----------
        # Create EventBridge rule to trigger the crawler Lambda every 5 minutes
        # Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_events/Rule.html
        # Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_events_targets/LambdaFunction.html
        events.Rule(
            self, "CrawlerSchedule",
            schedule=events.Schedule.rate(Duration.minutes(5)),
            targets=[targets.LambdaFunction(self.crawler_lambda)]
        )

        # ------------ CloudWatch Dashboard Service -----------
        # Create CloudWatch dashboard to visualize website monitoring metrics
        # Name as "WebMonitoringDashboard"
        # Add widgets for each monitored website
        # Reference: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Dashboard.html
        self.dashboard = cloudwatch.Dashboard(
            self, "WebMonitoringDashboard"
        )
