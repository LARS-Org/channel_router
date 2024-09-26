"""
This stack is responsible for handler the incoming and outcoming messages 
from all supported channels.
The incoming messages are received by a unique Lambda function and forwarded to 
a SNS topic after the channel identification.
The outcoming messages are received by another Lambda function from a SNS topic and sent to 
the appropriate channel.
"""
from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_sqs as sqs,
    aws_sns as sns,
)
from aws_cdk import aws_sns_subscriptions as sns_subscriptions
from aws_cdk.aws_lambda_event_sources import SqsEventSource
from constructs import Construct

class ChannelRouterStack(Stack):
    """
    AWS CDK stack to deploy the ChannelRouter infrastructure for multi-channel chatbot interactions.
    Uses FIFO SQS queues to ensure message ordering between the receiver and handler Lambdas.
    """

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
            
        # AllChannelsReceiverLambda, after consume and processing the incoming messages, 
        # must forward the messages using a SNS topic.
        # Create a SNS topic to forward messages from all channels to the chatbot handler Lambda
        # TODO: #6 Add a dead-letter queue to handle failed messages
        # TODO: #5 Study the use of FIFO SNS topics to ensure message ordering
        incoming_msgs_sns_topic = sns.Topic(
            self,
            "IncomingMessagesTopic",
            display_name="Incoming Messages Topic",
            topic_name="incoming-messages-topic",
        )
        
        # Grant the all-channels handler Lambda permission to publish messages to the all-channels SNS topic
        incoming_msgs_sns_topic.grant_publish(all_channels_receiver_lambda)
        
        # Add the all-channels SNS topic ARN to the all-channels handler Lambda environment variables
        all_channels_receiver_lambda.add_environment("INCOMING_MSGS_SNS_TOPIC_ARN", incoming_msgs_sns_topic.topic_arn)
                
        # The outcoming messages coming from a SNS topic and must be processed by another Lambda function called OutcomingMessagesHandlerLambda.
        # Create a SNS topic to receive outcoming messages from external systems
        outcoming_messages_sns_topic = sns.Topic(
            self,
            "OutcomingMessagesTopic",
            display_name="Outcoming Messages Topic",
            topic_name="outcoming-messages-topic",
        )

        # Create a Lambda function to send outcoming messages to the appropriate channel
        outcoming_messages_sender_lambda = _lambda.Function(
            self,
            "OutcomingMessagesSenderLambda",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="outcoming_messages_sender.handler",
            code=_lambda.Code.from_asset("lambdas"),
            timeout=Duration.seconds(60),
        )
        
        # Grant the outcoming messages sender Lambda permission to receive messages from the outcoming messages SNS topic
        outcoming_messages_sns_topic.grant_subscribe(outcoming_messages_sender_lambda)
        
        # Configure the outcoming messages sender Lambda as a listener of the outcoming messages SNS topic
        outcoming_messages_sns_topic.add_subscription(
            sns_subscriptions.LambdaSubscription(outcoming_messages_sender_lambda)
        )