import aws_cdk as core
import aws_cdk.assertions as assertions

from dang_quoc_toan.dang_quoc_toan_stack import DangQuocToanStack

# example tests. To run these tests, uncomment this file along with the example
# resource in dang_quoc_toan/dang_quoc_toan_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = DangQuocToanStack(app, "dang-quoc-toan")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
