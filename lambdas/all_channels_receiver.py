"""
This module is the Lambda handler to process incoming Telegram messages.
"""

import os
import sys
import json

# Adds lambda/create/packages to the system path.
# This must be done before importing any modules from the packages directory.
sys.path.append(os.path.join(os.path.dirname(__file__), "packages"))

from app_common.base_lambda_handler import BaseLambdaHandler
from channels_config import CHANNELS_HANDLER_CLASS_MAP as HANDLERS_MAP
from channel_handler import ChannelHandler


class AllChannelsReceiver(BaseLambdaHandler):
    """
    The Lambda handler class to process incoming messages.
    """

    def _handle(self):
        """
        Handle the incoming messages from all channels.
        """
        # Extract app token and channel from the URL path
        path_parameters = self.event["pathParameters"]["proxy"].split("/")
        channel_name = path_parameters[0]  # e.g., "whatsapp"
        app_token = path_parameters[1]  # e.g., "bot123"

        self.do_log(
            f"Received message from channel: {channel_name} with app token: {app_token}"
        )

        # Get the handler class for the channel
        handler_class = HANDLERS_MAP.get(channel_name)
        if not handler_class:
            self.do_log(f"Channel {channel_name} not supported.")
            return

        # Create the handler instance
        handler_instance: ChannelHandler = handler_class(self)

        # test if is a GET request
        if self.event["httpMethod"] == "GET":
            return self._handle_get(handler_instance)
        # test if is a POST request
        if self.event["httpMethod"] == "POST":
            return self._handle_post(handler_instance, app_token)
        # if it is not a GET or POST request, return an error
        self.do_log("Invalid request method.")
        return {
            "statusCode": 405,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Method Not Allowed"}),
        }

    def _handle_get(self, handler_instance: ChannelHandler):
        """
        Handle the GET request.
        """
        return {
            # Respond to channel webhook with 200 OK
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": handler_instance.extract_channel_webhook_validation_code(),
        }

    def _handle_post(self, handler_instance: ChannelHandler, app_token: str):
        """
        The main method to process incoming messages.
        """
        # Get the message details from the handler
        user_message = handler_instance.extract_user_txt_msg()
        channel_user_firstname = handler_instance.extract_channel_user_firstname()
        channel_user_id = handler_instance.extract_channel_user_id()
        channel_chat_id = handler_instance.extract_channel_chat_id()
        channel_msg_id = handler_instance.extract_channel_msg_id()
        user_message_timestamp = handler_instance.extract_message_timestamp()

        # Get the SNS topic ARN from the environment variable
        sns_topic_arn = self.get_env_var("INCOMING_MSGS_SNS_TOPIC_ARN")
        sns_message = json.dumps(
            {
                "app_token": app_token,
                "channel": handler_instance.get_channel_name(),
                "user_message": user_message,
                "channel_user_firstname": channel_user_firstname,
                "channel_user_id": channel_user_id,
                "channel_chat_id": channel_chat_id,
                "channel_msg_id": channel_msg_id,
                "user_message_timestamp": user_message_timestamp,
            }
        )
        # Forward the message to the SNS topic
        self.publish_to_sns(topic_arn=sns_topic_arn, message=sns_message)
        # Respond with 200 OK to acknowledge receipt of the message
        # It is necessary to return a response to the Channel webhook and avoid retries
        # v.g: https://core.telegram.org/bots/api#making-requests
        # TODO: #2 refator to use the common response method from the BaseLambdaHandler
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {"status": "ok"}
            ),  # Respond to channel webhook with 200 OK
        }


def handler(event, context):
    """
    Lambda function to process the incoming messages and send to a SNS topic.
    """
    _handler = AllChannelsReceiver()
    # Implicitly invokes __call__() ...
    #   ... which invokes _do_the_job() ...
    #     ... which invokes before_handle(), handle() and after_handle()
    return _handler(event, context)
