import aws_cdk as core
import aws_cdk.assertions as assertions

from channel_router.channel_router_stack import ChannelRouterStack

# example tests. To run these tests, uncomment this file along with the example
# resource in channel_router/channel_router_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ChannelRouterStack(app, "channel-router")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
