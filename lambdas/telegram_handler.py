"""
This module contains the Lambda handler class to process incoming Telegram messages.
"""

from channel_handler import ChannelHandler
import requests
from app_common.base_lambda_handler import BaseLambdaHandler


class TelegramHandler(ChannelHandler):
    """
    The Lambda handler class to process incoming Telegram messages.
    """

    def __init__(self, lambda_handler: BaseLambdaHandler) -> None:
        super().__init__(lambda_handler)
        # Telegram Bot Token from environment variable
        self._bot_token = self._extract_bot_token()
        self._telegram_server_url = f"https://api.telegram.org/bot{self._bot_token}/"

    def get_channel_name(self) -> str:
        return "telegram"

    def _do_reply_with_plain_text(self, full_msg):
        """
        Leverages the Telegram API to send a text-only message to the Telegram
        chat currently being serviced by this lambda function, and returns the
        response provided by Telegram after converting it to JSON format.
        """
        data = {
            "chat_id": self.extract_channel_chat_id(),
            "text": full_msg,
            "parse_mode": "HTML",
        }
        response = requests.post(
            self._telegram_server_url + "sendMessage", data=data, timeout=10
        )

        response.raise_for_status()

        response_json = response.json()

        return response_json

    def _get_max_message_length(self) -> int:
        """
        Returns the maximum message length supported by Telegram.
        """
        return 4096

    def extract_user_txt_msg(self) -> str:
        """
        Returns the text of a message (most likely the latest message) in the
        Telegram chat currently being serviced by this lambda function. The
        message text comes from the ``body`` attribute. For an example of a
        dictionary with data from a Telegram message, see the file
        ``docs/telegram/typical-lambda-function-parameters.txt``.
        """
        body = self._lambda_handler.body
        if "message" in body and "text" in body["message"] and body["message"]["text"]:
            return body["message"]["text"]
        # else
        return None

    def extract_channel_user_firstname(self):
        """
        Returns the first name of the user that is participating in the
        Telegram chat currently being serviced by this lambda function. The
        first name can come either from the ``callback_query`` dictionary or
        the ``message`` dictionary of the ``body`` attribute. For an example of
        a dictionary with data from a Telegram message, see the file
        ``docs/telegram/typical-lambda-function-parameters.txt``.
        """
        # if self.get_callback_data():
        #     return self._incoming_user_msg_obj["callback_query"]["from"]["first_name"]
        # else
        return self._lambda_handler.body["message"]["from"]["first_name"]

    def extract_channel_user_id(self):
        """
        Returns the ID of the user that is participating in the Telegram chat
        currently being serviced by this lambda function. The user ID can come
        either from the ``callback_query`` dictionary or the ``message``
        dictionary of the ``body`` attribute. For an example of a dictionary
        with data from a Telegram message, see the file
        ``docs/telegram/typical-lambda-function-parameters.txt``.
        """

        # if self.get_callback_data() is not None:
        #     return self._incoming_user_msg_obj["callback_query"]["from"]["id"]
        # else
        return self._lambda_handler.body["message"]["from"]["id"]

    def extract_channel_chat_id(self):
        """
        Returns the ID of the Telegram chat currently being serviced by this
        lambda function. The chat ID can come either from the ``callback_query``
        dictionary or the ``message`` dictionary of the ``body`` attribute. For
        an example of a dictionary with data from a Telegram message, see the
        file ``docs/telegram/typical-lambda-function-parameters.txt``.
        """

        # if self.get_callback_data():
        #     return self._incoming_user_msg_obj["callback_query"]["message"]["chat"]["id"]
        # else
        if "channel_chat_id" in self._lambda_handler.body:
            # This is the structure of the body when the
            # chatbot message arrives after the processing
            return self._lambda_handler.body["channel_chat_id"]
        # else:
        return self._lambda_handler.body["message"]["chat"]["id"]

    # returns the telegram update_id
    def extract_channel_msg_id(self):
        """
        Returns the ID of a message (most likely the latest message) in the
        Telegram chat currently being serviced by this lambda function. The
        message ID can come either from the ``callback_query`` dictionary or
        the ``message`` dictionary of the ``body`` attribute. For an example of
        a dictionary with data from a Telegram message, see the file
        ``docs/telegram/typical-lambda-function-parameters.txt``.
        """

        # if self.get_callback_data():
        #     return self._incoming_user_msg_obj["callback_query"]["message"]["message_id"]
        # else
        return self._lambda_handler.body["message"]["message_id"]

    def validate_user_as_human(self) -> bool:
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
        #     return self._incoming_user_msg_obj["callback_query"]["from"]["is_bot"]
        # else
        return self._lambda_handler.body["message"]["from"]["is_bot"]

    def extract_message_timestamp(self) -> int:
        """
        Extracts the timestamp of the Telegram message.
        """
        return self._lambda_handler.body["message"]["date"]
