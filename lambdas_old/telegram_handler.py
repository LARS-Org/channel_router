"""
This module is the Lambda handler to process incoming Telegram messages.
"""
import os
import sys

# Adds lambda/create/packages to the system path.
# This must be done before importing any modules from the packages directory.
sys.path.append(os.path.join(os.path.dirname(__file__), "packages"))

import requests
from chatbot_handler import ChatBotHandler
import app_common.app_utils as util

# Telegram Bot Token from environment variable
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/"

class TelegramHandler(ChatBotHandler):
    """
    The Lambda handler class to process incoming Telegram messages.
    """
    def _do_reply_with_plain_text(self, full_msg):
        """
        Leverages the Telegram API to send a text-only message to the Telegram
        chat currently being serviced by this lambda function, and returns the
        response provided by Telegram after converting it to JSON format.
        """
        data = {
            "chat_id": self._get_channel_chat_id(),
            "text": full_msg,
            "parse_mode": "HTML",
        }
        response = requests.post(
            TELEGRAM_BASE_URL + "sendMessage", data=data, timeout=10
        )

        response_json = response.json()
        util.do_log(title="Chatbot's Response", obj=response_json)
              
        return response_json
    
    def _get_max_message_length(self) -> int:
        """
        Returns the maximum message length supported by Telegram.
        """
        return 4096

    def _get_user_txt_msg(self) -> str:
        """
        Returns the text of a message (most likely the latest message) in the
        Telegram chat currently being serviced by this lambda function. The
        message text comes from the ``body`` attribute. For an example of a
        dictionary with data from a Telegram message, see the file
        ``docs/telegram/typical-lambda-function-parameters.txt``.
        """
        if (
            "message" in self.body
            and "text" in self.body["message"]
            and self.body["message"]["text"]
        ):
            return self.body["message"]["text"]
        # else
        return None

    
    def _get_channel_user_firstname(self):
        """
        Returns the first name of the user that is participating in the
        Telegram chat currently being serviced by this lambda function. The
        first name can come either from the ``callback_query`` dictionary or
        the ``message`` dictionary of the ``body`` attribute. For an example of
        a dictionary with data from a Telegram message, see the file
        ``docs/telegram/typical-lambda-function-parameters.txt``.
        """
        # if self.get_callback_data():
        #     return self.body["callback_query"]["from"]["first_name"]
        # else
        return self.body["message"]["from"]["first_name"]
    
    def _get_channel_id(self):
        """
        Returns the ID of the Telegram channel currently being serviced by this
        lambda function. The channel ID is always ``telegram``.
        """

        return "telegram"

    
    def _get_channel_user_id(self):
        """
        Returns the ID of the user that is participating in the Telegram chat
        currently being serviced by this lambda function. The user ID can come
        either from the ``callback_query`` dictionary or the ``message``
        dictionary of the ``body`` attribute. For an example of a dictionary
        with data from a Telegram message, see the file
        ``docs/telegram/typical-lambda-function-parameters.txt``.
        """

        # if self.get_callback_data() is not None:
        #     return self.body["callback_query"]["from"]["id"]
        # else
        return self.body["message"]["from"]["id"]

    
    def _get_channel_chat_id(self):
        """
        Returns the ID of the Telegram chat currently being serviced by this
        lambda function. The chat ID can come either from the ``callback_query``
        dictionary or the ``message`` dictionary of the ``body`` attribute. For
        an example of a dictionary with data from a Telegram message, see the
        file ``docs/telegram/typical-lambda-function-parameters.txt``.
        """

        # if self.get_callback_data():
        #     return self.body["callback_query"]["message"]["chat"]["id"]
        # else
        return self.body["message"]["chat"]["id"]

    # returns the telegram update_id
    def _get_channel_msg_id(self):
        """
        Returns the ID of a message (most likely the latest message) in the
        Telegram chat currently being serviced by this lambda function. The
        message ID can come either from the ``callback_query`` dictionary or
        the ``message`` dictionary of the ``body`` attribute. For an example of
        a dictionary with data from a Telegram message, see the file
        ``docs/telegram/typical-lambda-function-parameters.txt``.
        """

        # if self.get_callback_data():
        #     return self.body["callback_query"]["message"]["message_id"]
        # else
        return self.body["message"]["message_id"]

    
    def _check_if_user_is_a_bot(self) -> bool:
        """
        Returns ``True`` in case the user that sent a message (most likely the
        latest message) in the Telegram chat currently being serviced by this
        lambda function is a bot, and ``False`` otherwise.

        ATTENTION: Telegram bots cannot send messages to other bots -- if our
        bot ever receives a message from another Telegram bot, something must
        be quite wrong! Also, when a user clicks on an inline button in a
        Telegram chat, the destination bot receives a callback query.
        """

        # if self.get_callback_data():
        #     return self.body["callback_query"]["from"]["is_bot"]
        # else
        return self.body["message"]["from"]["is_bot"]    

    

def handler(event, context):
    """
    Lambda function to route messages from the multi-channel SQS queue to the appropriate handler.
    """
    _handler = TelegramHandler()
    # Implicitly invokes __call__() ...
    #   ... which invokes _do_the_job() ...
    #     ... which invokes before_handle(), handle() and after_handle()
    return _handler(event, context)
