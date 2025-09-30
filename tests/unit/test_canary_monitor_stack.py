import aws_cdk as core
import aws_cdk.assertions as assertions

from canary_monitor.canary_monitor_stack import CanaryMonitorStack

# example tests. To run these tests, uncomment this file along with the example
# resource in canary_monitor/canary_monitor_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CanaryMonitorStack(app, "canary-monitor")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
