"""
This module contains the ChatBotHandler class, that is the base class for all chatbot handlers.
"""

from abc import abstractmethod

import requests

from messages import ERROR_MSG_GENERAL, ERROR_MSG_UNKNOWN_MESSAGE_TYPE, ERROR_MSG_USER_MESSAGE_TOO_LONG, REPLY_USER_MESSAGE_RECEIVED
from config import MAX_USER_MESSAGE_LENGTH

# import email_util

from app_common.base_lambda_handler import BaseLambdaHandler
import app_common.app_utils as util


class ChatBotHandler(BaseLambdaHandler):
    """
    This class is the base class for all chatbot handlers.
    """

    def on_error(self, e):
        """
        Invokes ``on_error()`` on the base class and follows by sending an
        error message to the chat user.
        """
        # call super method
        super().on_error(e)
        # answering the user with an error message
        try:
            self._reply_with_error(ERROR_MSG_GENERAL)
        except Exception as e:  # pylint: disable=broad-except
            # using a generic exception because we don't know which exception will be raised
            # only log the error, because we are already on a error handling method
            util.do_log(
                "** ChatBotHandler::on_error() is done. Error on trying reply user:", e
            )

    def handle(self):
        """
        Handles the lambda function invocation by checking whether a message
        (most likely the last message) in the chat currently being serviced is
        a user message or a callback query, and follows by processing it
        accordingly.
        """

        util.do_log("** ChatBotHandler.handle()")
        # callback_data: dict = self.get_callback_data()
        # if self.get_callback_data():
        #     # the message is a callback query
        #     return self.handle_callback_query(callback_data)
        # # else
        # user_document: UploadedDoc = self.get_user_document()
        # if user_document:
        #     # the message is a user document
        #     return self.handle_user_document(user_document)
        # else
        user_txt_msg: str = self._get_user_txt_msg()
        if self._get_user_txt_msg():  # it is a user txt message
            return self.__handle_user_txt_msg(user_txt_msg)
        else:
            util.do_log("** it's a message that we don't know how to handle")
            # it's a message that we don't know how to handle
            self._reply_with_error(ERROR_MSG_UNKNOWN_MESSAGE_TYPE)
          

    def __handle_user_txt_msg(self, user_msg: str):
        """
        This method handles the user message.
        """
        util.do_log(f"** handle_user_msg(): {user_msg}")

        # checking the user message length
        if len(user_msg) > MAX_USER_MESSAGE_LENGTH:
            self._reply_with_error(
                ERROR_MSG_USER_MESSAGE_TOO_LONG,
                # send_email_to_developers=True,
            )
            return
        # else: the message is valid
        self._do_handle_user_txt_msg(user_msg)
        
        
    def _do_handle_user_txt_msg(self, user_txt_msg: str):
        """
        This method processes the user message.
        """
        # default implementation
        answer = f"{REPLY_USER_MESSAGE_RECEIVED}: {user_txt_msg}"
        
        custom_handler_url = self.get_env_var("CHATBOT_CUSTOM_HANDLER_WEBHOOK")
        if custom_handler_url:
            # There is a custom handler; we must call the custom handler API
            payload = {
                "user_txt_msg": user_txt_msg,
                "user_id": self._get_channel_user_id(),
                "chat_id": self._get_channel_chat_id(),
                "msg_id": self._get_channel_msg_id(),
                "channel_id": self._get_channel_id(),
            }

            # Send a POST request to the custom handler webhook
            response = requests.post(custom_handler_url, json=payload, timeout=10)
            response.raise_for_status()  # Raise an error if the request failed          
            # Handle the response from the webhook
            answer = response.json()["body"]
            
        self._reply_with_plain_text(answer)
        

    def _reply_with_error(self, error_msg, send_email_to_developers=False):
        """
        This method replies the user with an error message.
        """
        # send a email to the developers, just in case
        if send_email_to_developers:
            log_msg = (
                error_msg
                + "<br><br><b>*context:</b><br>"
                + str(self.context)
                + "<br><br><b>*event:</b><br>"
                + str(self.event)
            )
            # email_util.send_email("Alert in ChatBotHandler", log_msg)
        # sending the error message to the user
        try:
            self._reply_with_plain_text(
                error_msg,
                # test_if_there_is_a_new_message=False
            )
        except Exception:  # pylint: disable=broad-except
            # trying again without translation
            # maybe the error is related to the translation
            # it's important answering the user, even in the default language (English)
            self._reply_with_plain_text(
                error_msg,
                # translate=False,
                # test_if_there_is_a_new_message=False
            )

    def _reply_with_plain_text(
        self,
        full_msg,
        # save_reply=True,
        # translate=True,
        # full_msg_language_id=config.DEFAULT_USER_LANGUAGE_ID,
        # test_if_there_is_a_new_message=True,
    ):
        """
        This method must send the message to the chatbot.
        full_msg_language_id is the language id of the full_msg.
        save_reply is a flag to indicate if the reply must be saved on database.
        translate is a flag to indicate if the message must be translated.
        full_msg_language_id is the language id of the full_msg.
        """

        if not full_msg:
            # nothing to do
            return

        # if test_if_there_is_a_new_message and self.there_is_a_new_message():
        #     # there is a new message waiting to be processed
        #     # so, we don't send the message now because it regards
        #     # to a previous message that doesn't matter anymore.
        #     return

        # # translating the message according to the user preferred language
        # # only translate if the message language is not already the user preferred language
        # translate = translate and (
        #     full_msg_language_id != self.user.preferred_language_id
        # )

        # if translate:
        #     full_msg = translate_text(
        #         la_user_id=self.user.id,
        #         text=full_msg,
        #         target_language_id=self.user.preferred_language_id,
        #         target_language_name=self.__get_user_language_as_string(),
        #     )["response"]["text"]

        # dividing the message into segments, just in case.
        # Telegram, per example, doesn't allow messages with more than 4096 characters, so
        # we need to divide the message into segments. We may need to insert
        # the ellipsis character (…) twice per segment as we do the division.
        # ATTENTION: If the ellipsis goes in the start of the segment, it needs
        # an additional space!
        msg_segments = self.__divide_msg_into_segments(
            full_msg, self._get_max_message_length() - 3, "… ", "…"
        )

        for msg_segment in msg_segments:
            self._do_reply_with_plain_text(msg_segment)

        # if save_reply:
        #     # saving the reply
        #     self.replies.append(full_msg)

    @staticmethod
    def __divide_msg_into_segments(
        full_msg, max_segment_size=4096, segment_prefix="", segment_suffix=""
    ):
        """
        This method divides the message into segments.
        """
        if segment_prefix is None:
            segment_prefix = ""

        if segment_suffix is None:
            segment_suffix = ""

        step = max_segment_size - len(segment_prefix) - len(segment_suffix)

        if full_msg is None:
            full_msg = ""

        full_msg_len = len(full_msg)
        cur_start_pos = 0
        result = []

        while True:
            msg_segment = full_msg[cur_start_pos : cur_start_pos + step].lstrip()
            next_start_pos = cur_start_pos + step
            last_pos = cur_start_pos + step - 1

            # Do we need to make adjustments to the segment?
            if last_pos + 1 < full_msg_len:
                if full_msg[last_pos] == " ":
                    # The segment ends with a blank space
                    msg_segment = msg_segment.rstrip()
                    msg_segment_len = len(msg_segment)

                    if (
                        msg_segment_len > 0
                        and not msg_segment[msg_segment_len - 1].isalpha()
                    ):
                        msg_segment += " "
                elif full_msg[last_pos + 1] != " ":
                    # The segment ends with a piece of a word and the rest of
                    # the word is in the next segment. We try to make things
                    # prettier by backtracking in the segment looking for spaces
                    # and making the segment a bit shorter than before
                    while last_pos > cur_start_pos:
                        if full_msg[last_pos] == " ":
                            next_start_pos = last_pos
                            msg_segment = full_msg[cur_start_pos:last_pos].lstrip()
                            break

                        last_pos = last_pos - 1

            if cur_start_pos > 0:
                # We're continuing from a previous segment
                msg_segment = segment_prefix + msg_segment

            is_last_segment = True

            if cur_start_pos + step < full_msg_len:
                # Some extra content still follows, we're not done yet
                msg_segment += segment_suffix
                is_last_segment = False

            cur_start_pos = next_start_pos

            result.append(msg_segment)

            if is_last_segment:
                break

        return result

    @abstractmethod
    def _get_max_message_length(self) -> int:
        """
        This method must return the maximum number of characters per message for that channel.
        """
        # must be implemented by the subclass

    @abstractmethod
    def _do_reply_with_plain_text(self, full_msg):
        """
        This method must send the message to the chatbot.
        """
        # must be implemented by the subclass

    @abstractmethod
    def _get_user_txt_msg(self) -> str:
        """
        This method must return the user message, if the message is a user message.
        Otherwise, it must return None.
        """
        # must be implemented by the subclass

    @abstractmethod
    def _get_channel_user_firstname(self):
        """
        Returns the first name of the user that is participating in the chat
        currently being serviced by this lambda function. The default
        implementation simply raises an exception, and is meant to be
        overridden by subclasses.
        """
        # must be implemented by the subclass

    @abstractmethod
    def _get_channel_id(self):
        """
        Returns the ID of the channel that is participating in the chat
        currently being serviced by this lambda function. The default
        implementation simply raises an exception, and is meant to be
        overridden by subclasses.
        """
        # must be implemented by the subclass

    @abstractmethod
    def _get_channel_user_id(self):
        """
        Returns the ID of the user that is participating in the chat currently
        currently being serviced by this lambda function. The default
        implementation simply raises an exception, and is meant to be
        overridden by subclasses.
        """
        # must be implemented by the subclass

    @abstractmethod
    def _get_channel_chat_id(self):
        """
        This method must return the chat id.
        """
        # must be implemented by the subclass

    @abstractmethod
    def _get_channel_msg_id(self):
        """
        This method must return the message id.
        """
        # must be implemented by the subclass

    @abstractmethod
    def _check_if_user_is_a_bot(self) -> bool:
        """
        Check if the user is a bot.
        returns True if the user is a bot
        otherwise, returns False
        """
        # must be implemented by the subclass
