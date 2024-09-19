from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_iam as iam,
    aws_sqs as sqs,
)
from aws_cdk.aws_lambda_event_sources import SqsEventSource

from constructs import Construct

# List of channels for which the chatbot will be configured.
CHANNELS_LIST = ["telegram"]  # Add other channels here

class ChannelRouterStack(Stack):
    """
    AWS CDK stack to deploy the chatbot infrastructure.
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

        # Create channel-specific Lambda functions (receiver and handler) and endpoints
        for channel in CHANNELS_LIST:
            # Create channel-specific handler Lambda
            channel_receiver_lambda = self.__create_lambda(channel, "Receiver")

            # Create channel-specific endpoint
            self.__create_endpoint(api_gateway, channel, channel_receiver_lambda)

            # Create channel-specific handler Lambda
            channel_handler_lambda = self.__create_lambda(channel, "Handler")

            # Create channel-specific SQS queue
            queue = self.__create_msgs_queue(channel)

            # Grant the receiver Lambda the permission to send messages to the queue
            queue.grant_send_messages(channel_receiver_lambda)
            # Add the queue URL to the receiver Lambda environment variables
            channel_receiver_lambda.add_environment(f"{channel.upper()}_MSGS_QUEUE_URL", queue.queue_url)

            # Grant the handler Lambda the permission to receive messages from the queue
            queue.grant_consume_messages(channel_handler_lambda)
            # Add the queue as a trigger for the handler Lambda
            channel_handler_lambda.add_event_source(SqsEventSource(queue))        
        
        
    def __create_lambda(self, channel: str, sufix: str) -> _lambda.Function:
        """
        Helper function to create a receiver Lambda function with basic configuration.
        """
        lambda_name = f"ChannelRouterStack-{channel.capitalize()}{sufix}Lambda"
        return _lambda.Function(
            self,
            lambda_name,
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler=f"{channel}_{sufix}.handler".lower(),
            code=_lambda.Code.from_asset(f"lambdas"),
            timeout=Duration.seconds(60),
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
    
    def __create_msgs_queue(self, channel: str) -> sqs.Queue:
        """
        Helper function to create an SQS queue for a specific channel.
        """
        return sqs.Queue(
            self,
            f"{channel.capitalize()}MessagesQueue2",
            queue_name=f"{channel}-messages-queue2",
            visibility_timeout=Duration.seconds(300),
            retention_period=Duration.days(14),
        )