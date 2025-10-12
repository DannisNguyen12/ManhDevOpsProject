from aws_cdk import (
    Stack,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as pipeline_actions,
    aws_codecommit as codecommit,
    aws_codebuild as codebuild,
    aws_iam as iam,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    SecretValue,
    Environment,
    Duration
)
from constructs import Construct
from typing import Dict, List

class PipelineStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        # Default configurations
        github_config = {
            'owner': 'socdms',  # Your GitHub username
            'repo': 'ManhDevOpsProject',  # Your repo name
            'branch': 'main'
        }
        
        # Default environments configuration
        environments = {
            "Beta": {
                "account": kwargs.get('env', {}).get('account', ''),
                "region": kwargs.get('env', {}).get('region', 'us-east-1')
            },
            "Gamma": {
                "account": kwargs.get('env', {}).get('account', ''),
                "region": kwargs.get('env', {}).get('region', 'us-east-1')
            },
            "Prod": {
                "account": kwargs.get('env', {}).get('account', ''),
                "region": kwargs.get('env', {}).get('region', 'us-east-1')
            }
        }

        # Pipeline notification topic
        pipeline_topic = sns.Topic(self, "PipelineNotificationTopic")
        pipeline_topic.add_subscription(
            subscriptions.EmailSubscription("long.nm187254@gmail.com")  # Default notification email
        )

        # Source artifact
        source_output = codepipeline.Artifact()
        
        # GitHub source action
        source_action = pipeline_actions.GitHubSourceAction(
            action_name="GitHub_Source",
            owner=github_config['owner'],
            repo=github_config['repo'],
            branch=github_config['branch'],
            oauth_token=SecretValue.secrets_manager('github-token'),
            output=source_output,
            trigger=pipeline_actions.GitHubTrigger.WEBHOOK
        )

        pipeline = codepipeline.Pipeline(
            self, "WebsiteMonitorPipeline",
            pipeline_name="WebsiteMonitorPipeline",
            cross_account_keys=True
        )

        pipeline.add_stage(
            stage_name="Source",
            actions=[source_action]
        )

        # Create stages for each environment
        self._create_environment_stages(
            pipeline=pipeline,
            source_artifact=source_output,
            environments=environments,
            notification_topic=pipeline_topic
        )

    def _create_environment_stages(
            self,
            pipeline: codepipeline.Pipeline,
            source_artifact: codepipeline.Artifact,
            environments: Dict[str, Dict[str, str]],
            notification_topic: sns.Topic
        ) -> None:
        
        for env_name, env_config in environments.items():
            # Build project for unit tests
            unit_test_project = codebuild.PipelineProject(
                self, f"{env_name}UnitTests",
                environment=codebuild.BuildEnvironment(
                    build_image=codebuild.LinuxBuildImage.STANDARD_5_0,
                    privileged=True
                ),
                build_spec=codebuild.BuildSpec.from_object({
                    "version": "0.2",
                    "phases": {
                        "install": {
                            "runtime-versions": {
                                "python": "3.9"
                            },
                            "commands": [
                                "pip install -r requirements.txt",
                                "pip install -r requirements-dev.txt"
                            ]
                        },
                        "build": {
                            "commands": [
                                "pytest tests/unit -v"
                            ]
                        }
                    }
                })
            )

            # Build project for integration tests
            integration_test_project = codebuild.PipelineProject(
                self, f"{env_name}IntegrationTests",
                environment=codebuild.BuildEnvironment(
                    build_image=codebuild.LinuxBuildImage.STANDARD_5_0,
                    privileged=True
                ),
                build_spec=codebuild.BuildSpec.from_object({
                    "version": "0.2",
                    "phases": {
                        "install": {
                            "runtime-versions": {
                                "python": "3.9"
                            },
                            "commands": [
                                "pip install -r requirements.txt",
                                "pip install -r requirements-dev.txt"
                            ]
                        },
                        "build": {
                            "commands": [
                                "pytest tests/integration -v"
                            ]
                        }
                    }
                })
            )

            # Deploy action
            deploy_project = codebuild.PipelineProject(
                self, f"{env_name}Deploy",
                environment=codebuild.BuildEnvironment(
                    build_image=codebuild.LinuxBuildImage.STANDARD_5_0,
                    privileged=True
                ),
                build_spec=codebuild.BuildSpec.from_object({
                    "version": "0.2",
                    "phases": {
                        "install": {
                            "runtime-versions": {
                                "python": "3.9"
                            },
                            "commands": [
                                "npm install -g aws-cdk",
                                "pip install -r requirements.txt"
                            ]
                        },
                        "build": {
                            "commands": [
                                "cdk deploy --require-approval never"
                            ]
                        }
                    }
                })
            )

            # Add stage to pipeline
            pipeline.add_stage(
                stage_name=env_name,
                actions=[
                    pipeline_actions.CodeBuildAction(
                        action_name=f"{env_name}_UnitTests",
                        project=unit_test_project,
                        input=source_artifact,
                        outputs=[codepipeline.Artifact(f"{env_name.lower()}-unit-tests")]
                    ),
                    pipeline_actions.CodeBuildAction(
                        action_name=f"{env_name}_IntegrationTests",
                        project=integration_test_project,
                        input=source_artifact,
                        outputs=[codepipeline.Artifact(f"{env_name.lower()}-integration-tests")]
                    ),
                    pipeline_actions.CodeBuildAction(
                        action_name=f"{env_name}_Deploy",
                        project=deploy_project,
                        input=source_artifact,
                        environment_variables={
                            "CDK_DEFAULT_ACCOUNT": codebuild.BuildEnvironmentVariable(
                                value=env_config["account"]
                            ),
                            "CDK_DEFAULT_REGION": codebuild.BuildEnvironmentVariable(
                                value=env_config["region"]
                            ),
                            "STAGE": codebuild.BuildEnvironmentVariable(
                                value=env_name.lower()
                            )
                        }
                    )
                ]
            )

            # Add notifications for stage failures
            deploy_project.on_build_failed(env_name).add_target(notification_topic)