from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_dynamodb as dynamodb,
    Duration
)
from constructs import Construct

class ApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config_table: dynamodb.Table = None, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Use provided config table
        self.config_table = config_table

        # Create API Lambda functions
        self.fn_CRUD = _lambda.Function(
            self, "WebsiteCrudLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("modules/api"),
            handler="api_handler.handler",
            timeout=Duration.minutes(1),
            environment={
                "CONFIG_TABLE": config_table.table_name
            }
        )

        # Grant DynamoDB permissions
        config_table.grant_read_write_data(self.fn_CRUD)

        # Create API Gateway
        api = apigw.RestApi(
            self, "WebsiteManagementApi",
            rest_api_name="Website Management API",
            description="API for CRUD websites",
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
            apigw.LambdaIntegration(self.fn_CRUD)
        )

        # POST /websites (Create new website)
        websites.add_method(
            "POST",
            apigw.LambdaIntegration(self.fn_CRUD)
        )

        # Single website operations
        website = websites.add_resource("{websiteId}")
        
        # GET /websites/{websiteId}
        website.add_method(
            "GET",
            apigw.LambdaIntegration(self.fn_CRUD)
        )

        # PUT /websites/{websiteId}
        website.add_method(
            "PUT",
            apigw.LambdaIntegration(self.fn_CRUD)
        )

        # DELETE /websites/{websiteId}
        website.add_method(
            "DELETE",
            apigw.LambdaIntegration(self.fn_CRUD)
        )