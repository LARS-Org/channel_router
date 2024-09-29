"""
This module contains the configuration for the channels supported.
"""

from telegram_handler import TelegramHandler

# Mapping of channel names to their respective handler classes
CHANNELS_HANDLER_CLASS_MAP = {
    "telegram": TelegramHandler,
    "whatsapp": "WhatsAppHandler", # TODO: #9 Implement the WhatsAppHandler class
    "messenger": "MessengerHandler", #TODO: #10 Implement the MessengerHandler class
    # Add more handlers here as needed
}
