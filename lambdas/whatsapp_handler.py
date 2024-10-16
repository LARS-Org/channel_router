"""
This module contains the Lambda handler class to process incoming WhatsApp messages.
See:
https://developers.facebook.com/docs/whatsapp/api/messages/text/
"""

from channel_handler import ChannelHandler
import requests
from app_common.base_lambda_handler import BaseLambdaHandler


class WhatsAppHandler(ChannelHandler):
    """
    The Lambda handler class to process incoming WhatsApp messages.
    """

    def __init__(self, lambda_handler: BaseLambdaHandler) -> None:
        super().__init__(lambda_handler)
        self._access_token = None
        self._phone_number_id = None
        self._whatsapp_api_url = None
        token_info = self._extract_bot_token()
        if token_info:
            # the expected structure for WhatsApp token_info is:
            # {
            #     "access_token": "access token",
            #     "phone_number_id": "phone number id"
            # }
            # observe that "access token" and "phone number id" will be available
            # only after the message be processed by other components.
            # So, it's necessary keep the access using ".get" method.
            self._access_token = token_info.get("access_token")
            self._phone_number_id = token_info.get("phone_number_id")
            self._whatsapp_api_url = (
                f"https://graph.facebook.com/v21.0/{self._phone_number_id}/messages"
            )

    def get_channel_name(self) -> str:
        return "whatsapp"

    def _do_reply_with_plain_text(self, full_msg):
        """
        Leverages the WhatsApp API to send a text-only message to the WhatsApp
        user currently being serviced by this lambda function, and returns the
        response provided by WhatsApp after converting it to JSON format.
        """
        data = {
            "messaging_product": "whatsapp",
            "to": self.extract_channel_chat_id(),
            "type": "text",
            "text": {"body": full_msg},
        }
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }
        response = requests.post(
            self._whatsapp_api_url, json=data, headers=headers, timeout=10
        )
        response.raise_for_status()
        response_json = response.json()
        return response_json

    def _get_max_message_length(self) -> int:
        """
        Returns the maximum message length supported by WhatsApp.
        """
        return 4096

    def extract_user_txt_msg(self) -> str:
        """
        Returns the text of a message (most likely the latest message) in the
        WhatsApp conversation currently being serviced by this lambda function.
        """
        body = self._lambda_handler.body
        if "entry" in body:
            try:
                message = body["entry"][0]["changes"][0]["value"]["messages"][0]
                if message["type"] == "text" and "text" in message:
                    return message["text"]["body"]
            except (IndexError, KeyError):
                return None
        return None

    def extract_channel_user_firstname(self):
        """
        Returns the name of the user that is participating in the
        WhatsApp conversation currently being serviced by this lambda function.
        """
        body = self._lambda_handler.body
        if "entry" in body:
            try:
                name = body["entry"][0]["changes"][0]["value"]["contacts"][0][
                    "profile"
                ]["name"]
                return name
            except (IndexError, KeyError):
                return None
        return None

    def extract_channel_user_id(self):
        """
        Returns the ID (phone number) of the user that is participating in the
        WhatsApp conversation currently being serviced by this lambda function.
        """
        body = self._lambda_handler.body

        if "channel_user_id" in body:
            # This is the structure of the body when the
            # chatbot message arrives after the processing
            return body["channel_user_id"]
        # else:
        # This is the structure of the body when the message arrives to be processed
        user_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
        return user_id

    def extract_channel_chat_id(self):
        """
        Returns the ID (phone number) of the WhatsApp conversation currently being serviced by this
        lambda function.
        """
        return self.extract_channel_user_id()

    def extract_channel_msg_id(self):
        """
        Returns the ID of a message (most likely the latest message) in the
        WhatsApp conversation currently being serviced by this lambda function.
        """
        body = self._lambda_handler.body
        if "entry" in body:
            try:
                message_id = body["entry"][0]["changes"][0]["value"]["messages"][0][
                    "id"
                ]
                return message_id
            except (IndexError, KeyError):
                return None
        return None

    def validate_user_as_human(self) -> bool:
        """
        Returns `True` in case the user that sent a message (most likely the
        latest message) in the WhatsApp conversation currently being serviced by this
        lambda function is a bot, and `False` otherwise.
        """
        # WhatsApp messages are assumed to be from humans
        return True

    def extract_message_timestamp(self) -> int:
        """
        Extracts the timestamp of the WhatsApp message.
        """
        body = self._lambda_handler.body
        if "entry" in body:
            try:
                timestamp_str = body["entry"][0]["changes"][0]["value"]["messages"][0][
                    "timestamp"
                ]
                return int(timestamp_str)
            except (IndexError, KeyError, ValueError):
                return None
        return None

    def extract_channel_webhook_validation_code(self):
        """
        This method handles the WhatsApp webhook validation process by
        simply returning the challenge code provided in the query parameters
        without validating the token.
        """
        query_params = self._lambda_handler.event.get("queryStringParameters", {})
        challenge = query_params.get("hub.challenge")

        # Return the challenge to validate the webhook
        return challenge
