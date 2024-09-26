from channel_handler import ChannelHandler

class TelegramHandler(ChannelHandler):
    """
    Handler class for Telegram channel
    """
    def send_message(self, message):
        """
        Sends a message to the Telegram channel
        """
        pass
    
    def extract_message(self, event):
        """
        Extracts the message from the event
        """
        pass
    
    def extract_sender(self, event):
        """
        Extracts the sender from the event
        """
        pass
    
    def extract_timestamp(self, event):
        """
        Extracts the timestamp from the event
        """
        pass
    
    def extract_chat_id(self, event):
        """
        Extracts the chat_id from the event
        """
        pass
    
    def extract_message_id(self, event):
        """
        Extracts the message_id from the event
        """
        pass