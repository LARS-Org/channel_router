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

class AllChannelsReceiver(BaseLambdaHandler):
    """
    The Lambda handler class to process incoming Telegram messages.
    """
    def _handle(self):
        """
        The main method to process incoming Telegram messages.
        """
        # Just receive the message and put it in the queue for further processing by the handler
        queue_url = self.get_env_var("ALL_CHANNELS_MSGS_QUEUE_URL")
        self.send_message_to_sqs(queue_url, self.body)
        # nothing to do more here

def handler(event, context):
    """
    Lambda function to route messages from the multi-channel SQS queue to the appropriate handler.
    """
    _handler = AllChannelsReceiver()
    # Implicitly invokes __call__() ...
    #   ... which invokes _do_the_job() ...
    #     ... which invokes before_handle(), handle() and after_handle()
    _handler(event, context)
    # Respond with 200 OK to acknowledge receipt of the message
    # It is necessary to return a response to the Telegram webhook and avoid retries
    # https://core.telegram.org/bots/api#making-requests
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({"status": "ok"})  # Respond to Telegram
    }
