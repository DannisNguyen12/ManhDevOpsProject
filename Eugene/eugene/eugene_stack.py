from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    Duration,
    aws_synthetics as synthetics,

    aws_lambda as lambda_,
    aws_cloudwatch as cloudwatch,
    aws_codedeploy as codedeploy,
    Environment
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
        fn = lambda_.Function(self, "MyLambda",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="WHLambda.lambda_handler",
            code=lambda_.Code.from_asset("./modules")
        )
        '''
        canary = synthetics.Canary(self, "MyCanary",
            runtime=synthetics.Runtime.SYNTHETICS_NODEJS_PUPPETEER_3_5,
            test=synthetics.Test.custom({
                "code": synthetics.Code.from_asset("canary"),
                "handler": "index.handler"
            }),
            schedule=synthetics.Schedule.rate(Duration.minutes(5)), # runs canary test every 5 minutes (checks for availability and latency)
            timeout=Duration.minutes(1) # The max time allowed for the Canary test to complete each time it runs.
        )
        '''

















'''
        # Create version and alias for deployment
        version = fn.current_version
        alias = lambda_.Alias(self, "LambdaAlias",
            alias_name="Prod",
            version=version
        )

        # Metric 1 - CPUUtilization from EC2 namespace (example) - done based on original code
        metric1 = cloudwatch.Metric(
            namespace="AWS/EC2",
            metric_name="CPUUtilization",
            statistic="Average",
            period=Duration.minutes(5)
        )

        cloudwatch.AnomalyDetectionAlarm(self, "AnomalyAlarm", # done based on orginal code
            metric=metric1,
            evaluation_periods=1,
            std_devs=2,
            comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_LOWER_OR_GREATER_THAN_UPPER_THRESHOLD,
            alarm_description="Alarm when metric is outside the expected band"
        )

        # Metric 2 - Lambda errors
        error_alarm = cloudwatch.Alarm(self, "ErrorsAlarm",
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            threshold=1,
            evaluation_periods=1,
            metric=alias.metric_errors()
        )

        # Blue-green deployment group
        deployment_group = codedeploy.LambdaDeploymentGroup(self, "BlueGreenDeployment",
            alias=alias,
            deployment_config=codedeploy.LambdaDeploymentConfig.LINEAR_10PERCENT_EVERY_1MINUTE,
            alarms=[error_alarm]
        )

        # Optional additional alarm
        deployment_group.add_alarm(cloudwatch.Alarm(self, "BlueGreenErrors",
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            threshold=1,
            evaluation_periods=1,
            metric=alias.metric_errors()
        ))
'''

'''
        # Creates metrix 1 
        metric = cloudwatch.Metric(
            namespace="AWS/EC2",
            metric_name="CPUUtilization",
            statistic="Average",
            period=Duration.minutes(5)
        )
        # Create an anomaly detection alarm
        alarm = cloudwatch.AnomalyDetectionAlarm(self, "AnomalyAlarm",
            metric=metric,
            evaluation_periods=1,

            # Number of standard deviations for the band (default: 2)
            std_devs=2,
            # Alarm outside on either side of the band, or just below or above it (default: outside)
            comparison_operator=cloudwatch.ComparisonOperator.LESS_THAN_LOWER_OR_GREATER_THAN_UPPER_THRESHOLD,
            alarm_description="Alarm when metric is outside the expected band"
        )

        # Creates Matrix 2
        alarm = cloudwatch.Alarm(self, "Errors",
        comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        threshold=1,
        evaluation_periods=1,
        metric=alias.metric_errors()
        )
        deployment_group = codedeploy.LambdaDeploymentGroup(self, "BlueGreenDeployment",
            alias=alias,
            deployment_config=codedeploy.LambdaDeploymentConfig.LINEAR_10PERCENT_EVERY_1MINUTE,
            alarms=[alarm
            ]
        )
        deployment_group.add_alarm(cloudwatch.Alarm(self, "BlueGreenErrors",
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            threshold=1,
            evaluation_periods=1,
            metric=blue_green_alias.metric_errors()
        ))

        # Creates Matrix 3
        alarm = cloudwatch.Alarm(self, "Errors",
        comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        threshold=1,
        evaluation_periods=1,
        metric=alias.metric_errors()
        )
        deployment_group = codedeploy.LambdaDeploymentGroup(self, "BlueGreenDeployment",
            alias=alias,
            deployment_config=codedeploy.LambdaDeploymentConfig.LINEAR_10PERCENT_EVERY_1MINUTE,
            alarms=[alarm
            ]
        )
        deployment_group.add_alarm(cloudwatch.Alarm(self, "BlueGreenErrors",
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            threshold=1,
            evaluation_periods=1,
            metric=blue_green_alias.metric_errors()
        ))    
'''
        
