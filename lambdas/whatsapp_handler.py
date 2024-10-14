"""
This module contains the Lambda handler class to process incoming WhatsApp messages.
"""

from channel_handler import ChannelHandler
import requests
from app_common.base_lambda_handler import BaseLambdaHandler
import os


class WhatsAppHandler(ChannelHandler):
    """
    The Lambda handler class to process incoming WhatsApp messages.
    """

    def __init__(self, lambda_handler: BaseLambdaHandler) -> None:
        super().__init__(lambda_handler)
        # WhatsApp Access Token and Phone Number ID from environment variables
        self._access_token = os.environ.get("WHATSAPP_ACCESS_TOKEN")
        self._phone_number_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
        self._whatsapp_api_url = (
            f"https://graph.facebook.com/v17.0/{self._phone_number_id}/messages"
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

    def extract_app_token(self):
        """
        There is no app token to extract from the incoming WhatsApp message.
        """
        return None

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
        if "entry" in body:
            try:
                user_id = body["entry"][0]["changes"][0]["value"]["contacts"][0][
                    "wa_id"
                ]
                return user_id
            except (IndexError, KeyError):
                return None
        return None

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
        simply returning the challenge code
        provided in the query parameters without validating the token.
        """
        print(self._lambda_handler.event)
        print(self._lambda_handler.context)
        query_params = self._lambda_handler.event.get("queryStringParameters", {})
        print(query_params, type(query_params))
        challenge = query_params.get("hub.challenge")
        print(f"WhatsApp challenge: {challenge}")

        # Return the challenge to validate the webhook
        return challenge
