from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets
)
from constructs import Construct


class CanaryMonitorStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        # Create Lambda function
        canary_lambda = _lambda.Function(
            self, "CanaryLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="monitor.lambda_handler",  
            code=_lambda.Code.from_asset("lambda"),  
        )

        # Create EventBridge Rule to run Lambda every 5 minutes
        rule = events.Rule(
            self, "CanaryScheduleRule",
            schedule=events.Schedule.rate(Duration.minutes(5))
        )

        # Link rule to Lambda
        rule.add_target(targets.LambdaFunction(canary_lambda))
        # The code that defines your stack goes here

        # example resource
        # queue = sqs.Queue(
        #     self, "CanaryMonitorQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )
