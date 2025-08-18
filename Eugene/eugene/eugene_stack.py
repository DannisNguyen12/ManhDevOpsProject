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

class EugeneStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # example resource
        # queue = sqs.Queue(
        #     self, "EugeneQueue",
        #     visibility_timeout=Duration.seconds(300),
        # 

        # function to run WHLambda file
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/README.html#function-timeout
        fn = lambda_.Function(self, "WHLambda",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="WHLambda.lambda_handler",
            code=lambda_.Code.from_asset("./modules"),
            # log_removal_policy=Lambda_.RemovalPolicy.DESTROY  # Remove logs on stack deletion, this don't work
        )
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_logs/README.html#loggroup
        #  moved loge removal policy to a log group instead of in function as part of AWS CDK v2
        '''
        logs.LogGroup(
            self, 
            "WHLambdaLogGroup",
            log_group_name=f"/aws/lambda/{fn.function_name}",
            removal_policy=RemovalPolicy.DESTROY
        )
        '''
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_scheduler/README.html

        schedule = events_.Schedule.rate(Duration.minutes(30))
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