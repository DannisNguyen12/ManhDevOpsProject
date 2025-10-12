from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_dynamodb as dynamodb,
    aws_cloudwatch as cloudwatch,
    aws_iam as iam,
    RemovalPolicy,
    Duration
)
from constructs import Construct

class ApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config_table: dynamodb.Table = None, crawl_results_table: dynamodb.Table = None, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Use provided config table or create a new one
        if config_table:
            self.config_table = config_table
        else:
            self.config_table = dynamodb.Table(
                self, "WebsiteConfigTable",
                partition_key=dynamodb.Attribute(
                    name="id",
                    type=dynamodb.AttributeType.STRING
                ),
                removal_policy=RemovalPolicy.RETAIN
            )

        # Use provided crawl results table or create a new one
        if crawl_results_table:
            self.crawl_results_table = crawl_results_table
        else:
            self.crawl_results_table = dynamodb.Table(
                self, "CrawlResultsTable",
                partition_key=dynamodb.Attribute(
                    name="target_id",
                    type=dynamodb.AttributeType.STRING
                ),
                sort_key=dynamodb.Attribute(
                    name="crawl_timestamp",
                    type=dynamodb.AttributeType.STRING
                ),
                removal_policy=RemovalPolicy.RETAIN
            )

        # Create API Lambda functions
        self.crud_lambda = _lambda.Function(
            self, "WebsiteCrudLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("/Users/dannguyen/Downloads/DevOps/ManhDevOpsProject/modules"),
            handler="api_handler.handler",
            timeout=Duration.minutes(1),
            environment={
                "CONFIG_TABLE": config_table.table_name,
                "CRAWL_RESULTS_TABLE": crawl_results_table.table_name
            }
        )

        # Grant DynamoDB permissions
        config_table.grant_read_write_data(self.crud_lambda)
        crawl_results_table.grant_read_write_data(self.crud_lambda)

        # Create API Gateway
        api = apigw.RestApi(
            self, "WebsiteManagementApi",
            rest_api_name="Website Management API",
            description="API for managing monitored websites",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS
            )
        )

        # Create API resources and methods
        websites = api.root.add_resource("websites")
        
        # GET /websites (List all websites)
        websites.add_method(
            "GET",
            apigw.LambdaIntegration(self.crud_lambda)
        )

        # POST /websites (Create new website)
        websites.add_method(
            "POST",
            apigw.LambdaIntegration(self.crud_lambda)
        )

        # Single website operations
        website = websites.add_resource("{websiteId}")
        
        # GET /websites/{websiteId}
        website.add_method(
            "GET",
            apigw.LambdaIntegration(self.crud_lambda)
        )

        # PUT /websites/{websiteId}
        website.add_method(
            "PUT",
            apigw.LambdaIntegration(self.crud_lambda)
        )

        # DELETE /websites/{websiteId}
        website.add_method(
            "DELETE",
            apigw.LambdaIntegration(self.crud_lambda)
        )

        # Crawl results endpoints
        crawl_results = api.root.add_resource("crawl-results")
        
        # GET /crawl-results (List all crawl results)
        crawl_results.add_method(
            "GET",
            apigw.LambdaIntegration(self.crud_lambda)
        )

        # POST /crawl-results (Create new crawl result - for crawler Lambda)
        crawl_results.add_method(
            "POST",
            apigw.LambdaIntegration(self.crud_lambda)
        )

        # Single crawl result operations
        crawl_result = crawl_results.add_resource("{resultId}")
        
        # GET /crawl-results/{resultId}
        crawl_result.add_method(
            "GET",
            apigw.LambdaIntegration(self.crud_lambda)
        )

        # DELETE /crawl-results/{resultId}
        crawl_result.add_method(
            "DELETE",
            apigw.LambdaIntegration(self.crud_lambda)
        )

        # Crawler status and control endpoints
        crawler = api.root.add_resource("crawler")
        
        # GET /crawler/status (Get crawler status)
        crawler_status = crawler.add_resource("status")
        crawler_status.add_method(
            "GET",
            apigw.LambdaIntegration(self.crud_lambda)
        )

        # POST /crawler/start (Start crawler manually)
        crawler_start = crawler.add_resource("start")
        crawler_start.add_method(
            "POST",
            apigw.LambdaIntegration(self.crud_lambda)
        )

        # Add CloudWatch metrics
        self.api_metrics = cloudwatch.Metric(
            namespace="WebsiteAPI",
            metric_name="Invocations",
            dimensions_map={
                "ApiName": api.rest_api_name
            },
            period=Duration.minutes(1)
        )

        # Create dashboard widget
        self.dashboard_widget = cloudwatch.GraphWidget(
            title="API Metrics",
            left=[self.api_metrics],
            width=12,
            height=6
        )