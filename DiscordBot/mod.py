from enum import Enum, auto
import discord
import re

class Review:
    def __init__(self, client):
        self.state = None  # Allows transition between `report` and `block` midway through processes
        self.client = client
        self.message = None
        self.reported_user = None