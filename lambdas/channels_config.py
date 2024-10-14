"""
This module contains the configuration for the channels supported.
"""

from telegram_handler import TelegramHandler
from whatsapp_handler import WhatsAppHandler

# Mapping of channel names to their respective handler classes
CHANNELS_HANDLER_CLASS_MAP = {
    "telegram": TelegramHandler,
    "whatsapp": WhatsAppHandler, 
    "messenger": "MessengerHandler", #TODO: #10 Implement the MessengerHandler class
    # Add more handlers here as needed
}
