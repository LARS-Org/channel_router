"""
This stack is responsible for handling the incoming and outgoing messages 
from all supported channels.
The incoming messages are received by a unique Lambda function and forwarded to 
an SNS topic after the channel identification.
The outgoing messages are received by another Lambda function from an SNS topic and sent to 
the appropriate channel.
"""

from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_sns as sns,
    CfnOutput,
)
from aws_cdk import aws_sns_subscriptions as sns_subscriptions
from constructs import Construct


class ChannelRouterStack(Stack):
    """
    AWS CDK stack to deploy the ChannelRouter infrastructure for multi-channel chatbot interactions.
    """

    # TODO: #11 Use FIFO SQS queues to ensure message ordering between the receiver and handler Lambdas.

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # List of supported channels
        # TODO: #1 get this list from a configuration file or environment variables
        channels_list = {"telegram", "whatsapp", "messenger"}

        # Create API Gateway to handle incoming webhooks from various channels
        api_gateway = apigateway.RestApi(
            self,
            "ChannelRouterWebhookAPI",
            rest_api_name="ChannelRouter Webhook API",
            description="API Gateway to receive webhooks from various channels.",
        )

        # Create a unique Lambda function to receive messages from all channels
        all_channels_receiver_lambda = _lambda.Function(
            self,
            "AllChannelsReceiverLambda",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="all_channels_receiver.handler",
            code=_lambda.Code.from_asset("lambdas"),
            timeout=Duration.seconds(60),
        )

        # Config one path for each channel handled by the all_channels_receiver_lambda
        for channel in channels_list:
            api_gateway.root.add_resource(channel).add_method(
                "POST", apigateway.LambdaIntegration(all_channels_receiver_lambda)
            )

        # AllChannelsReceiverLambda, after consuming and processing the incoming messages,
        # must forward the messages using an SNS topic.
        # Create an SNS topic to forward messages from all channels to the chatbot handler Lambda
        incoming_msgs_sns_topic = sns.Topic(
            self,
            "IncomingMessagesTopic",
            display_name="Incoming Messages Topic",
            topic_name="incoming-messages-topic",
        )

        # Grant the all-channels handler Lambda permission to publish messages to the all-channels SNS topic
        incoming_msgs_sns_topic.grant_publish(all_channels_receiver_lambda)

        # Add the all-channels SNS topic ARN to the all-channels handler Lambda environment variables
        all_channels_receiver_lambda.add_environment(
            "INCOMING_MSGS_SNS_TOPIC_ARN", incoming_msgs_sns_topic.topic_arn
        )

        # *** Export the SNS Topic ARN using CfnOutput for cross-stack reference ***
        CfnOutput(
            self,
            "IncomingMessagesTopicArn",
            value=incoming_msgs_sns_topic.topic_arn,
            export_name="IncomingMessagesTopicArn",  # Export name to be referenced by other stacks
        )
        # This makes the SNS topic's ARN accessible to other stacks (like ChatBotAppManager)

        # The outgoing messages coming from an SNS topic must be processed by another Lambda function called OutcomingMessagesHandlerLambda.
        # Create an SNS topic to receive outgoing messages from external systems
        outgoing_messages_sns_topic = sns.Topic(
            self,
            "OutgoingMessagesTopic",
            display_name="Outgoing Messages Topic",
            topic_name="OutgoingMessagesTopic",
        )

        # Create a Lambda function to send outgoing messages to the appropriate channel
        outgoing_messages_sender_lambda = _lambda.Function(
            self,
            "OutgoingMessagesSenderLambda",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="outgoing_messages_sender.handler",
            code=_lambda.Code.from_asset("lambdas"),
            timeout=Duration.seconds(60),
        )

        # Grant the outgoing messages sender Lambda permission to receive messages from the outgoing messages SNS topic
        outgoing_messages_sns_topic.grant_subscribe(outgoing_messages_sender_lambda)

        # Configure the outgoing messages sender Lambda as a listener of the outgoing messages SNS topic
        outgoing_messages_sns_topic.add_subscription(
            sns_subscriptions.LambdaSubscription(outgoing_messages_sender_lambda)
        )

        # Export the SNS Topic ARN using CfnOutput for cross-stack reference
        CfnOutput(
            self,
            "OutgoingMessagesTopicArn",
            value=outgoing_messages_sns_topic.topic_arn,
            export_name="OutgoingMessagesTopicArn",  # Export name to be referenced by other stacks
        )
