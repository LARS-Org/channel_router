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


class AllChannelsReceiver(BaseLambdaHandler):
    """
    The Lambda handler class to process incoming messages.
    """

    def _handle(self):
        """
        The main method to process incoming messages.
        """
        # The resource corresponds to the channel name that sent the message
        channel_name = self.event["resource"].split("/")[-1]
        # TODO: #3 Refactor to use a common do_log method from the BaseLambdaHandler
        self.do_log(f"Received message from channel: {channel_name}")

        # Get the SNS topic ARN from the environment variable
        sns_topic_arn = os.environ.get("INCOMING_MSGS_SNS_TOPIC_ARN")
        sns_message = json.dumps(
            {"channel": channel_name, "incoming_message": self.body}
        )
        # Forward the message to the SNS topic
        self.publish_to_sns(topic_arn=sns_topic_arn, message=sns_message)


def handler(event, context):
    """
    Lambda function to process the incoming messages and send to a SNS topic.
    """
    _handler = AllChannelsReceiver()
    # Implicitly invokes __call__() ...
    #   ... which invokes _do_the_job() ...
    #     ... which invokes before_handle(), handle() and after_handle()
    _handler(event, context)
    # Respond with 200 OK to acknowledge receipt of the message
    # It is necessary to return a response to the Telegram webhook and avoid retries
    # https://core.telegram.org/bots/api#making-requests
    # TODO: #2 refator to use the common response method from the BaseLambdaHandler
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"status": "ok"}),  # Respond to channel webhook with 200 OK
    }
