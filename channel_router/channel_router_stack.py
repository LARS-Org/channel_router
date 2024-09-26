"""
This is stack is responsible for handler the incoming and outcoming messages from all supported channels.
The incoming messages are received by a unique Lambda function and stored in a FIFO SQS queue.
The messages are then processed by another Lambda function and forwarded to a SNS topic.
The outcoming messages are received by another Lambda function from a SNS topic and sent to the appropriate channel.
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

# List of channels for which the chatbot will be configured.
CHANNELS_LIST = ["telegram", "whatsapp", "messenger"]  # Add other channels here

class ChannelRouterStack(Stack):
    """
    AWS CDK stack to deploy the ChannelRouter infrastructure for multi-channel chatbot interactions.
    Uses FIFO SQS queues to ensure message ordering between the receiver and handler Lambdas.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create API Gateway to handle incoming webhooks from various channels
        api_gateway = apigateway.RestApi(
            self,
            "ChannelRouterWebhookAPI",
            rest_api_name="ChannelRouter Webhook API",
            description="API Gateway to receive webhooks from various channels.",
        )
        
        # Create a unique Lambda function to receive messages from all channels
        channel_router_lambda = _lambda.Function(
            self,
            "ChannelRouterLambda",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="channel_router.handler",
            code=_lambda.Code.from_asset("lambdas"),
            timeout=Duration.seconds(60),
        )
        
        # Create a FIFO queue to keep all incoming messages from all channels
        all_channels_queue = sqs.Queue(
            self,
            "AllChannelsMessagesQueueFifo",
            queue_name="all-channels-messages-queue.fifo",
            fifo=True,
            content_based_deduplication=True,
            visibility_timeout=Duration.seconds(300),
            retention_period=Duration.days(14),
        )
        
        # Grant the channel router Lambda permission to send messages to the all-channels queue
        all_channels_queue.grant_send_messages(channel_router_lambda)
        
        # Add the all-channels queue URL to the channel router Lambda environment variables
        channel_router_lambda.add_environment("ALL_CHANNELS_MSGS_QUEUE_URL", all_channels_queue.queue_url)
        
        # Config one path for each channel handled by the channel_router_lambda
        for channel in CHANNELS_LIST:
            api_gateway.root.add_resource(channel).add_method(
                "POST", apigateway.LambdaIntegration(channel_router_lambda)
            )
            
        # Create a Lambda function to process messages from the all-channels
        all_channels_handler_lambda = _lambda.Function(
            self,
            "AllChannelsHandlerLambda",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="all_channels_handler.handler",
            code=_lambda.Code.from_asset("lambdas"),
            timeout=Duration.seconds(60),
        )
        
        # Grant the all-channels handler Lambda permission to receive messages from the all-channels queue
        all_channels_queue.grant_consume_messages(all_channels_handler_lambda)
        
        # Add a SQS event source to the all-channels handler Lambda
        all_channels_handler_lambda.add_event_source(SqsEventSource(all_channels_queue))
        
        # AllChannelsHandlerLambda, after consume and processing the incoming messages, 
        # must forward the messages using a SNS topic.
        # Create a SNS topic to forward messages from all channels to the chatbot handler Lambda
        all_channels_sns_topic = sns.Topic(
            self,
            "AllChannelsMessagesTopic",
            display_name="All Channels Messages Topic",
            topic_name="all-channels-messages-topic",
        )
        
        # Grant the all-channels handler Lambda permission to publish messages to the all-channels SNS topic
        all_channels_sns_topic.grant_publish(all_channels_handler_lambda)
        
        # Add the all-channels SNS topic ARN to the all-channels handler Lambda environment variables
        all_channels_handler_lambda.add_environment("ALL_CHANNELS_SNS_TOPIC_ARN", all_channels_sns_topic.topic_arn)
        
        
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