from enum import Enum, auto
import discord
import re

class State(Enum):
    REVIEW_START = auto()
    AWAITING_MESSAGE = auto()

class Review:
    START_KEYWORD = "review"

    def __init__(self, client):
        self.state = State.REVIEW_START
        self.client = client
        self.message = None
        self.reported_user = None

    async def handle_review(self, message):
        '''
        This function makes up the meat of the user-side reporting flow. It defines how we transition between states and what 
        prompts to offer at each of those states. You're welcome to change anything you want; this skeleton is just here to
        get you started and give you a model for working with Discord. 
        '''
        
        if message.content.startswith(self.START_KEYWORD):
            reply = "Thank you for starting the reviewing process.\n"
            reply += "Here is the next report to review."
            return [reply]
            
        return []