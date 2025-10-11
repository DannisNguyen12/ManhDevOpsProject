import aws_cdk as core
import aws_cdk.assertions as assertions

from manh_dev_ops_project.monitorStack import ManhDevOpsProjectStack

# example tests. To run these tests, uncomment this file along with the example
# resource in manh_dev_ops_project/manh_dev_ops_project_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ManhDevOpsProjectStack(app, "manh-dev-ops-project")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
