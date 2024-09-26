"""
This module contains the configuration for the channels supported.
"""
from telegram_handler import TelegramHandler

# Mapping of channel names to their respective handler classes
CHANNELS_HANDLER_CLASS_MAP = {"telegram": TelegramHandler(), 
                              "whatsapp": "WhatsAppHandler", 
                              "messenger": "MessengerHandler"}