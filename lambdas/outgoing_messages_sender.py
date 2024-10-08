"""
This module is the Lambda handler to process outgoing messages.
"""

import os
import sys
import json

# Adds lambda/create/packages to the system path.
# This must be done before importing any modules from the packages directory.
sys.path.append(os.path.join(os.path.dirname(__file__), "packages"))

from app_common.base_lambda_handler import BaseLambdaHandler
from app_common.app_utils import do_log
from channels_config import CHANNELS_HANDLER_CLASS_MAP as HANDLERS_MAP
from channel_handler import ChannelHandler


class MessageSender(BaseLambdaHandler):
    """
    The Lambda handler class to process incoming messages.
    """

    def _handle(self):
        """
        The main method to process outcoming messages.
        """
        # Getting the channel name from the body
        channel_name = self.body["channel"]
        # Getting the handler class instance for the channel
        channel_handler: ChannelHandler = HANDLERS_MAP.get(channel_name)(self)
        # send the message
        channel_server_response = channel_handler.send_plain_text_reply(
            self.body["bot_message"]
        )
        #TODO: #12 Deal with erros when sending the message


def handler(event, context):
    """
    Lambda function to process the incoming messages and send to a SNS topic.
    """
    _handler = MessageSender()
    # Implicitly invokes __call__() ...
    #   ... which invokes _do_the_job() ...
    #     ... which invokes before_handle(), handle() and after_handle()

    # Respond with 200 OK to acknowledge receipt of the message
    # It is necessary to return a response to the Telegram webhook and avoid retries
    # https://core.telegram.org/bots/api#making-requests
    return _handler(event, context)
