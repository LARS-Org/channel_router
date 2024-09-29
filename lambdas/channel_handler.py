from abc import ABC, abstractmethod
import sys
import os

from app_common.base_lambda_handler import BaseLambdaHandler


class ChannelHandler:
    """
    Base class for channel handlers
    """

    def __init__(self, lambda_handler: BaseLambdaHandler) -> None:
        """
        The constructor receives the channel message object.
        """
        self._lambda_handler = lambda_handler

    def send_plain_text_reply(
        self,
        full_reply_plain_text_msg,
    ):
        """
        This method must send the message to the chatbot.
        """

        if not full_reply_plain_text_msg:
            # nothing to do
            return

        # dividing the message into segments, just in case.
        # Telegram, per example, doesn't allow messages with more than 4096 characters, so
        # we need to divide the message into segments. We may need to insert
        # the ellipsis character (…) twice per segment as we do the division.
        # ATTENTION: If the ellipsis goes in the start of the segment, it needs
        # an additional space!
        msg_segments = self.__divide_msg_into_segments(
            full_reply_plain_text_msg, self._get_max_message_length() - 3, "… ", "…"
        )

        for msg_segment in msg_segments:
            self._do_reply_with_plain_text(msg_segment)

    def send_error_reply(self, error_msg):
        """
        This method replies the user with an error message.
        """
        # TODO: #7 Implements sending email to developers support for errors.
        # Maybe we can build a exception handling class to do this.
        # Throwing an exception to be caught by the lambda layer.
        # send a email to the developers, just in case
        # if send_email_to_developers:
        #     log_msg = (
        #         error_msg
        #         + "<br><br><b>*context:</b><br>"
        #         + str(self.context)
        #         + "<br><br><b>*event:</b><br>"
        #         + str(self.event)
        #     )
        # email_util.send_email("Alert in ChatBotHandler", log_msg)
        # sending the error message to the user
        # TODO: #8 Implements the automatic translation of the error message
        self.send_plain_text_reply(
            error_msg,
        )

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
    def extract_app_token(self):
        """
        This method must return the app id.
        """
        # must be implemented by the subclass

    @abstractmethod
    def extract_user_txt_msg(self) -> str:
        """
        This method must return the user message, if the message is a user message.
        Otherwise, it must return None.
        """
        # must be implemented by the subclass

    @abstractmethod
    def extract_channel_user_firstname(self):
        """
        Returns the first name of the user that is participating in the chat
        currently being serviced by this lambda function. The default
        implementation simply raises an exception, and is meant to be
        overridden by subclasses.
        """
        # must be implemented by the subclass

    @abstractmethod
    def extract_channel_user_id(self):
        """
        Returns the ID of the user that is participating in the chat currently
        currently being serviced by this lambda function. The default
        implementation simply raises an exception, and is meant to be
        overridden by subclasses.
        """
        # must be implemented by the subclass

    @abstractmethod
    def extract_channel_chat_id(self):
        """
        This method must return the chat id.
        """
        # must be implemented by the subclass

    @abstractmethod
    def extract_channel_msg_id(self):
        """
        This method must return the message id.
        """
        # must be implemented by the subclass

    @abstractmethod
    def validate_user_as_human(self) -> bool:
        """
        Check if the user is a human.
        returns True if the user is a human,
        otherwise, returns False (it means the user is a bot).
        """
        # must be implemented by the subclass
