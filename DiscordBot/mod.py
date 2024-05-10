from enum import Enum, auto
import discord
import re

class State(Enum):
    REVIEW_START = auto()
    REVIEWING_VIOLATION = auto()

class Review:
    START_KEYWORD = "review"

    def __init__(self, client):
        self.state = State.REVIEW_START
        self.client = client
        self.message = None
        self.report = None

    async def handle_review(self, message):
        '''
        This function handles the moderator-side review process for reported messages.
        '''
        if message.content.startswith(self.START_KEYWORD):
            if len(self.client.reports_to_review) == 0:
                reply = "There are no pending reports to review.\n"
                return [reply]

            reply = "Thank you for starting the reviewing process.\n"
            reply += "Here is the next report to review.\n\n"

            self.report = self.client.reports_to_review.pop(0)
            reply += f"User reported: `{self.report.reported_user}`\n"
            reply += f"Message reported: `{self.report.reported_message.content}`\n"
            reply += f"Report category: {self.report.report_category}\n"
            reply += f"Additional details filed by reporting: {self.report.additional_details}\n\n"

            reply += f"Is this in violation of platform policies? Please respond with `yes` or `no`."
            self.state = State.REVIEWING_VIOLATION
            return [reply]
        
        if self.state == State.REVIEWING_VIOLATION:
            if message.content != "yes" and message.content != "no":
                return ["Please respond with `yes` or `no`."]
            
            if message.content == "yes":
                await self.report.reported_message.delete()
                reply = "Violating content has been removed.\n"
                reply += "Was the content illegal? Does the content pose an immediate danger? Please respond with `yes` or `no`."
                return [reply]
            
        return []