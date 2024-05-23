from enum import Enum, auto
import discord
import re
import heapq

class State(Enum):
    REVIEW_START = auto()
    REVIEWING_VIOLATION = auto()
    REVIEWING_NONVIOLATION = auto()
    REVIEWING_ADVERSARIAL_REPORTING = auto()
    REVIEWING_LEGALITY_DANGER = auto()
    REVIEWING_FRAUD_SCAM_1 = auto()
    REVIEWING_FRAUD_SCAM_2 = auto()
    REVIEWING_MISLEADING_OFFENSIVE_1 = auto()
    REVIEWING_MISLEADING_OFFENSIVE_2 = auto()
    REVIEWING_FURTHER = auto()
    REVIEWING_ESCALATE = auto()
    REVIEW_COMPLETE = auto()
    REVIEW_ANOTHER = auto()

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

            reply = f"Thank you for starting the reviewing process. There are {len(self.client.reports_to_review)} pending reports to review.\n"
            reply += self.start_review()
            return [reply]
        
        if self.state == State.REVIEWING_VIOLATION:
            if message.content != "yes" and message.content != "no":
                return ["Please respond with `yes` or `no`."]
            
            if message.content == "yes":
                await self.report.reported_message.delete()
                reply = "Violating content has been removed.\n"
                reply += "Was the content illegal? Does the content pose an immediate danger? Please respond with `yes` or `no`."
                self.state = State.REVIEWING_LEGALITY_DANGER
                return [reply]
            else:
                reply = "Do you suspect the content was reported maliciously? Please respond with `yes` or `no`."
                self.state = State.REVIEWING_NONVIOLATION
                return [reply]

        if self.state == State.REVIEWING_NONVIOLATION:
            if message.content != "yes" and message.content != "no":
                return ["Please respond with `yes` or `no`."]

            if message.content == "yes":
                reply = "Do you suspect there was coordinated reporting from multiple actors? Please respond with `yes` or `no`."
                self.state = State.REVIEWING_ADVERSARIAL_REPORTING
            else:
                reply = "Thank you. No further action will be taken.\n\n"
                reply += self.prompt_new_review()
            return [reply]

        if self.state == State.REVIEWING_ADVERSARIAL_REPORTING:
            if message.content != "yes" and message.content != "no":
                return ["Please respond with `yes` or `no`."]
            
            if message.content == "yes":
                reply = f"Reported user `{self.report.reported_user}` has been temporarily banned.\n"
                reply += "This report will be escalated to higher moderation teams for further review.\n\n"
            else:
                reply = f"Reported user `{self.report.reported_user}` has been temporarily banned.\n"
            reply += self.prompt_new_review()
            return [reply]
            
        if self.state == State.REVIEWING_LEGALITY_DANGER:
            if message.content != "yes" and message.content != "no":
                return ["Please respond with `yes` or `no`."]
            
            if message.content == "yes":
                reply = "This message will be submitted to local authorities.\n"
                reply += f"Reported user `{self.report.reported_user}` has been permanently banned.\n\n"
                reply += self.prompt_new_review()
                return [reply]
            else:
                reply = "Did the reported message violate policies on fraud or scam? Please respond with `yes` or `no`."
                self.state = State.REVIEWING_FRAUD_SCAM_1
                return [reply]

        if self.state == State.REVIEWING_FRAUD_SCAM_1:
            if message.content != "yes" and message.content != "no":
                return ["Please respond with `yes` or `no`."]
            
            if message.content == "yes":
                if self.report.additional_details:
                    reply = "The report contains these additional details.\n\n"
                    reply += self.report.additional_details + "\n\n"
                    reply += "Do the additional details contain any harmful links? Please respond with `yes` or `no`."
                    self.state = State.REVIEWING_FRAUD_SCAM_2
                    return [reply]
                if not self.report.additional_details:
                    reply = f"Reported user `{self.report.reported_user}` has been permanently banned.\n\n"
                    reply += self.prompt_new_review()
                    return [reply]
            else:
                reply = "Was the reported message misleading or offensive? Please respond with `yes` or `no`."
                self.state = State.REVIEWING_MISLEADING_OFFENSIVE_1
                return [reply]

        if self.state == State.REVIEWING_FRAUD_SCAM_2:
            if message.content != "yes" and message.content != "no":
                return ["Please respond with `yes` or `no`."]
            
            if message.content == "yes":
                reply = "The harmful links have been blacklisted.\n"
            reply += f"Reported user `{self.report.reported_user}` has been permanently banned.\n\n"
            reply += self.prompt_new_review()
            return [reply]

        if self.state == State.REVIEWING_MISLEADING_OFFENSIVE_1:
            if message.content != "yes" and message.content != "no":
                return ["Please respond with `yes` or `no`."]

            if message.content == "yes":
                reply = "Does the user have a history of violation?\n"
                reply += "Please respond with `yes` or `no`."
                self.state =  State.REVIEWING_MISLEADING_OFFENSIVE_2
                return [reply]
            else:
                reply = "The report has not been classified into any existing categories.\n"
                reply += "Please provide details about your review.\n\n"
                self.state = State.REVIEWING_FURTHER
                return [reply]

        if self.state == State.REVIEWING_MISLEADING_OFFENSIVE_2:
            if message.content != "yes" and message.content != "no":
                return ["Please respond with `yes` or `no`."]
            
            if message.content == "yes":
                reply = f"Reported user `{self.report.reported_user}` has been flagged.\n\n"
            else:
                reply = f"Reported user `{self.report.reported_user}` has been warned.\n\n"
            reply += self.prompt_new_review()
            return [reply]

        if self.state == State.REVIEWING_FURTHER:
            reply = "Thank you for providing details about your review.\n\n"
            reply += "Is further action necessary to review the violating content? Please respond with `yes` or `no`.\n\n"
            self.state = State.REVIEWING_ESCALATE
            return [reply]

        if self.state == State.REVIEWING_ESCALATE:
            if message.content != "yes" and message.content != "no":
                return ["Please respond with `yes` or `no`."]

            if message.content == "yes":
                reply = "Thank you. This report will be escalated to a higher moderation team for further review.\n\n"
            else:
                reply = "Thank you. No further action will be taken.\n\n"
            reply += self.prompt_new_review()
            return [reply]

        if self.state == State.REVIEW_ANOTHER:
            if message.content != "yes" and message.content != "no":
                return ["Please respond with `yes` or `no`."]
            
            return [self.start_review()]
            
        return []


    def start_review(self):
        reply = "Here is the next report to review.\n\n"

        self.report = heapq.heappop(self.client.reports_to_review)[1]

        reply += f"User reported: `{self.report.reported_user}`\n"
        reply += f"Message reported: `{self.report.reported_message.content}`\n"
        reply += f"Report category: {self.report.report_category}\n"
        reply += f"Report subcategory: {self.report.report_subcategory}\n"
        reply += f"Additional details filed by reporting: {self.report.additional_details}\n\n"

        reply += f"Is this in violation of platform policies? Please respond with `yes` or `no`."
        self.state = State.REVIEWING_VIOLATION
        return reply
    

    def prompt_new_review(self):
        reply = "Thank you for reviewing this report.\n"
        if len(self.client.reports_to_review) == 0:
            reply += "There are no more pending reports to review.\n"
            self.state = State.REVIEW_COMPLETE
        else:
            reply += f"There are {len(self.client.reports_to_review)} pending reports to review. Would you like to review another report?\n"
            self.state = State.REVIEW_ANOTHER
        
        return reply