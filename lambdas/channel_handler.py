from abc import ABC, abstractmethod

class ChannelHandler:
    """
    Base class for channel handlers
    """
    @abstractmethod
    def reply_with_text_msg(self, , ):
        """
        Sends a text message to the channel
        """
        raise NotImplementedError("Method send_message() must be implemented in the subclass")
    
    @abstractmethod
    def extract_message(self, event):
        """
        Extracts the message from the event
        """
        raise NotImplementedError("Method extract_message() must be implemented in the subclass")
    
    @abstractmethod
    def extract_sender(self, event):
        """
        Extracts the sender from the event
        """
        raise NotImplementedError("Method extract_sender() must be implemented in the subclass")
    
    @abstractmethod
    def extract_timestamp(self, event):
        """
        Extracts the timestamp from the event
        """
        raise NotImplementedError("Method extract_timestamp() must be implemented in the subclass")
    
    @abstractmethod
    def extract_chat_id(self, event):
        """
        Extracts the chat_id from the event
        """
        raise NotImplementedError("Method extract_chat_id() must be implemented in the subclass")
    
    @abstractmethod
    def extract_message_id(self, event):
        """
        Extracts the message_id from the event
        """
        raise NotImplementedError("Method extract_message_id() must be implemented in the subclass")