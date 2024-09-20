from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_sqs as sqs,
)
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

        # Create channel-specific Lambda functions (receiver and handler) and FIFO SQS queues
        for channel in CHANNELS_LIST:
            # Create channel-specific receiver Lambda
            channel_receiver_lambda = self.__create_lambda(channel, "Receiver")

            # Create channel-specific handler Lambda
            channel_handler_lambda = self.__create_lambda(channel, "Handler")

            # Create FIFO SQS queue for message passing between the receiver and handler Lambdas
            queue = self.__create_fifo_queue(channel)

            # Grant the receiver Lambda permission to send messages to the FIFO queue
            queue.grant_send_messages(channel_receiver_lambda)

            # Add the queue URL to the receiver Lambda environment variables
            channel_receiver_lambda.add_environment(f"{channel.upper()}_MSGS_QUEUE_URL", queue.queue_url)

            # Grant the handler Lambda permission to consume messages from the FIFO queue
            queue.grant_consume_messages(channel_handler_lambda)

            # Add the FIFO SQS queue as an event source for the handler Lambda
            channel_handler_lambda.add_event_source(SqsEventSource(queue))

            # Create an API Gateway endpoint for each channel to send messages to the receiver Lambda
            self.__create_endpoint(api_gateway, channel, channel_receiver_lambda)

    def __create_lambda(self, channel: str, suffix: str) -> _lambda.Function:
        """
        Helper function to create a Lambda function with basic configuration for each channel.
        A receiver and handler Lambda are created for each channel.
        """
        lambda_name = f"ChannelRouterStack-{channel.capitalize()}{suffix}Lambda"
        return _lambda.Function(
            self,
            lambda_name,
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler=f"{channel}_{suffix}.handler".lower(),
            code=_lambda.Code.from_asset(f"lambdas"),
            timeout=Duration.seconds(60),
            environment={
                "CHANNEL_NAME": channel
            }
        )

    def __create_endpoint(self, api_gateway: apigateway.RestApi,  
                          channel: str, 
                          receiver_lambda: _lambda.Function) -> apigateway.Resource:
        """
        Helper function to create an API Gateway endpoint for a specific channel.
        """
        integration = apigateway.LambdaIntegration(receiver_lambda)
        resource = api_gateway.root.add_resource(channel)
        resource.add_method("POST", integration)
        return resource

    def __create_fifo_queue(self, channel: str) -> sqs.Queue:
        """
        Helper function to create a FIFO SQS queue for a specific channel to ensure message order 
        between the receiver and handler Lambdas.
        """
        return sqs.Queue(
            self,
            f"{channel.capitalize()}MessagesQueueFifo",
            queue_name=f"{channel}-messages-queue.fifo",  # FIFO queue name must end with .fifo
            fifo=True,
            content_based_deduplication=True,  # Ensures messages with identical content are not duplicated
            visibility_timeout=Duration.seconds(300),
            retention_period=Duration.days(14),
        )
