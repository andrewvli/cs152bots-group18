from enum import Enum, auto
import discord
import re
import heapq

class ReportState(Enum):
    # Abuse Types
    SPAM = auto()
    HARM_ENDANGERMENT = auto()
    SEXUALLY_EXPLICIT = auto()
    FRAUD_SCAM = auto()
    FINANCIAL_FRAUD_CLASSIFICATION = auto()
    MISINFORMATION = auto()
    HATE_HARASSMENT = auto()
    CSAM = auto()
    INTELLECTUAL = auto()
    ILLICIT_TRADE_SUBSTANCES = auto()

class State(Enum):
    REVIEW_START = auto()
    REVIEWING_VIOLATION = auto()
    # REVIEWING_RECLASSIFICATION = auto()
    # RECLASSIFYING = auto()
    # REVIEWING_NONVIOLATION = auto()
    # REVIEWING_ADVERSARIAL_REPORTING = auto()
    # REVIEWING_LEGALITY_DANGER = auto()
    # REVIEWING_FRAUD_SCAM_1 = auto()
    # REVIEWING_FRAUD_SCAM_2 = auto()
    # REVIEWING_MISLEADING_OFFENSIVE_1 = auto()
    # REVIEWING_MISLEADING_OFFENSIVE_2 = auto()
    # REVIEWING_FURTHER = auto()
    # REVIEWING_ESCALATE = auto()
    # REVIEW_COMPLETE = auto()
    # REVIEW_ANOTHER = auto()
    REVIEWING_CLASSIFICATION = auto()
    REVIEWING_RECLASSIFICATION = auto()
    REVIEWING_CATEGORY = auto()
    REVIEWING_NONVIOLATION = auto()
    REVIEWING_SPAM = auto()
    REVIEWING_SPAM_2 = auto()
    REVIEWING_HARM_ENDANGERMENT = auto()
    REVIEWING_SEXUALLY_EXPLICIT = auto()
    REVIEWING_FRAUD_SCAM = auto()
    REVIEWING_FRAUD_SCAM_2 = auto()
    REVIEWING_FINANCIAL = auto()
    REVIEWING_LINKS = auto()
    REVIEWING_MISINFORMATION = auto()
    REVIEWING_MISINFORMATION_2 = auto()
    REVIEWING_HATE_HARASSMENT = auto()
    REVIEWING_HATE_HARASSMENT_2 = auto()
    REVIEWING_CSAM = auto()
    REVIEWING_INTELLECTUAL = auto()
    REVIEWING_ILLICIT = auto()
    REVIEWING_FURTHER_ACTION = auto()
    REVIEWING_FURTHER_ACTION_2 = auto()

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
                reply = "The violating content has been removed.\n"
                # self.State = State.REVIEWING_FURTHER_ACTION 
                reply += self.prompt_new_review()
                return [reply]
            else:
                self.State == State.REVIEWING_RECLASSIFICATION
            
                if self.State == State.REVIEWING_CLASSIFICATION:
                    reply = "Does this content violate platform policies? Please respond with `yes` or `no`."
                    self.State = State.REVIEWING_RECLASSIFICATION
                    return [reply]
                    
                if self.State == State.REVIEWING_RECLASSIFICATION:
                    if message.content != "yes" and message.content != "no":
                        return ["Please respond with `yes` or `no`."]

                    if message.content == "yes":
                        await self.report.reported_message.delete()
                        reply = "The violating content has been removed.\n"
                        reply += "Which category best describes the nature of this violation? Please respond with one of the following options.\n"
                        reply += "1. Spam.\n"
                        reply += "2. Harm and endangerment.\n"
                        reply += "3. Nudity and sexual content.\n"
                        reply += "4. Fraud or scam.\n"
                        reply += "5. Misinformation.\n"
                        reply += "6. Hate and harassment.\n"
                        reply += "7. Sexual content involving a child.\n"
                        reply += "8. Intellectual property theft.\n"
                        reply += "9. Illicit trade and substances.\n"
                        self.State = State.REVIEWING_CATEGORY
                        return [reply]
                    else:
                        reply = "Does it seem like this content was reported with malicious intent? Please respond with `yes` or `no`."
                        self.State = State.REVIEWING_NONVIOLATION
                        return [reply]
                
                if self.state == State.REVIEWING_RECLASSIFICATION:
                    if message.content not in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
                        return ["That is not a valid option. Please select the number corresponding to the appropriate category for reporting this message, or say `cancel` to cancel."]
                    
                    if message.content == "1":
                        self.report.report_category = ReportState.SPAM
                        self.State = State.REVIEWING_SPAM
                        return [reply]
                    if message.content == "2":
                        reply = "Which subcategory best describes the nature of this content? Please respond with one of the following options.\n"
                        reply += "1. Self-harm or suicidal content.\n"
                        reply += "2. Terrorism.\n"
                        reply += "3. Threat or depictions of violence and abuse.\n"
                        reply += "4. Death or severe injury.\n"
                        self.report.report_category = ReportState.HARM_ENDANGERMENT
                        self.State = State.REVIEWING_HARM_ENDANGERMENT
                        return [reply]
                    if message.content == "3":
                        reply = "Which subcategory best describes the nature of this content? Please respond with one of the following options.\n"
                        reply += "1. Adult nudity or pornography.\n"
                        reply += "2. Sexual harassment or abuse.\n"
                        self.report.report_category = ReportState.SEXUALLY_EXPLICIT
                        self.State = State.REVIEWING_SEXUALLY_EXPLICIT
                        return [reply]
                    if message.content == "4":
                        reply = "Which subcategory best describes the nature of this content? Please respond with one of the following options.\n"
                        reply += "1. Impersonation.\n"
                        reply += "2. Romance.\n"
                        reply += "3. Financial.\n"
                        self.report.report_category = ReportState.FRAUD_SCAM
                        self.State = State.REVIEWING_FRAUD_SCAM
                        return [reply]
                    if message.content == "5":
                        reply = "Which subcategory best describes the nature of this content? Please respond with one of the following options.\n"
                        reply += "1. Health.\n"
                        reply += "2. Climate.\n"
                        reply += "3. Political.\n"
                        self.report.report_category = ReportState.MISINFORMATION
                        self.State = State.REVIEWING_MISINFORMATION
                        return [reply]
                    if message.content == "6":
                        reply = "Which subcategory best describes the nature of this content? Please respond with one of the following options.\n"
                        reply += "1. Bullying.\n"
                        reply += "2. Reviewing private information.\n"
                        reply += "3. Hate speech.\n"
                        reply += "4. Stalking.\n"
                        self.report.report_category = ReportState.HATE_HARASSMENT
                        self.State = State.REVIEWING_HATE_HARASSMENT
                        return [reply]
                    if message.content == "7":
                        self.report.report_category = ReportState.CSAM
                        self.State = State.REVIEWING_CSAM
                        return [reply]
                    if message.content == "8":
                        reply = "Which subcategory best describes the nature of this content? Please respond with one of the following options.\n"
                        reply += "1. Infringes my copyright.\n"
                        reply += "2. Infringes my trademark.\n"
                        self.report.report_category = ReportState.INTELLECTUAL
                        self.State = State.REVIEWING_INTELLECTUAL
                        return [reply]
                    if message.content == "9":
                        reply = "Which subcategory best describes the nature of this content? Please respond with one of the following options.\n"
                        reply += "1. Illegal drug use or sale.\n"
                        reply += "2. Sale or promotion of counterfeit goods.\n"
                        reply += "3. Black market and smuuggling.\n"
                        self.report.report_category = ReportState.ILLICIT_TRADE_SUBSTANCES
                        self.State = State.REVIEWING_ILLICIT
                        return [reply]
                
                if self.State == State.REVIEWING_SPAM:
                    reply = "Does the reported user have a history of violation? Please respond with `yes` or `no`."
                    self.State = State.REVIEWING_SPAM_2
                    return [reply]
                if self.State == State.REVIEWING_SPAM_2:
                    if message.content != "yes" and message.content != "no":
                        return ["Please respond with `yes` or `no`."]
                    if message.content == "yes":
                        reply = "The reported user has been permanently banned.\n"
                    else:
                        reply = "The reported user has been temporarily banned.\n"
                    self.State = State.REVIEWING_FURTHER_ACTION
                    return [reply]
                
                if self.State == State.REVIEWING_HARM_ENDANGERMENT:
                    if message.content not in ["1", "2", "3", "4"]:
                        return ["That is not a valid option. Please select the number corresponding to the appropriate subcategory for the violating content, or say `cancel` to cancel."]
                    else:
                        reply = "This report will be submitted to local authorities. The reported user has been permanently banned.\n"
                        self.State = State.REVIEWING_FURTHER_ACTION
                        return [reply]
                    
                if self.State == State.REVIEWING_SEXUALLY_EXPLICIT:
                    if message.content not in ["1", "2"]:
                        return ["That is not a valid option. Please select the number corresponding to the appropriate subcategory for the violating content, or say `cancel` to cancel."]
                    if message.content == "1":
                        reply = "The reported user has been permanently banned.\n"
                    if message.content == "2":
                        reply = reply = "This report will be submitted to local authorities. The reported user has been permanently banned.\n"
                    self.State = State.REVIEWING_FURTHER_ACTION
                    return [reply]
                
                if self.State == State.REVIEWING_FRAUD_SCAM:
                    if message.content not in ["1", "2", "3"]:
                        return ["That is not a valid option. Please select the number corresponding to the appropriate subcategory for the violating content, or say `cancel` to cancel."]
                    if message.content in ["1", "2"]:
                        reply = "Does the reported user have a history of violation? Please respond with `yes` or `no`.\n"
                        self.State = State.REVIEWING_FRAUD_SCAM_2
                    if message.content == "3":
                        reply = "Which subcategory of financial fraud best describes the nature of this content? Please respond with one of the following options.\n"
                        reply += "1. Cryptocurrency.\n"
                        reply += "2. Investment.\n"
                        reply += "3. Phishing.\n"
                        reply += "4. Credit card.\n"
                        self.State = State.REVIEWING_FINANCIAL
                if self.State == State.REVIEWING_FRAUD_SCAM_2:
                    if message.content != "yes" and message.content != "no":
                        return ["Please respond with `yes` or `no`."]
                    if message.content == "yes":
                        reply = "The reported user has been permanently banned.\n"
                    else:
                        reply = "The reported user has been temporarily banned.\n"
                    self.State = State.REVIEWING_FURTHER_ACTION
                    return [reply]
                if self.State == State.REVIEWING_FINANCIAL:
                    reply = "Does the reported message contain any harmful links? Please respond with `yes` or `no`.\n"
                    self.State = State.REVIEWING_LINKS
                    return [reply]
                if self.State == State.REVIEWING_LINKS:
                    if message.content != "yes" and message.content != "no":
                        return ["Please respond with `yes` or `no`."]
                    if message.content == "yes":
                        reply = "The harmful links have been blacklisted.\n"
                    reply += "The reported user has been permanently banned.\n"
                    self.State = State.REVIEWING_FURTHER_ACTION
                    return [reply]
                
                if self.State == State.REVIEWING_MISINFORMATION:
                    if message.content not in ["1", "2", "3"]:
                        return ["That is not a valid option. Please select the number corresponding to the appropriate subcategory for the violating content, or say `cancel` to cancel."]
                    else:
                        reply = "Does the reported user have a history of violation? Please respond with `yes` or `no`.\n"
                        self.State = State.REVIEWING_MISINFORMATION_2
                        return [reply]
                if self.State == State.REVIEWING_MISINFORMATION_2:
                    if message.content != "yes" and message.content != "no":
                        return ["Please respond with `yes` or `no`."]
                    if message.content == "yes":
                        reply = "The reported user has been flagged.\n"
                    self.State = State.REVIEWING_FURTHER_ACTION
                    return [reply]
                
                if self.State == State.REVIEWING_HATE_HARASSMENT:
                    if message.content not in ["1", "2", "3", "4"]:
                        return ["That is not a valid option. Please select the number corresponding to the appropriate subcategory for the violating content, or say `cancel` to cancel."]
                    else:
                        reply = "Does the reported user have a history of violation? Please respond with `yes` or `no`.\n"
                        self.State = State.REVIEWING_HATE_HARASSMENT_2
                        return [reply]
                if self.State == State.REVIEWING_HATE_HARASSMENT_2:
                    if message.content != "yes" and message.content != "no":
                        return ["Please respond with `yes` or `no`."]
                    if message.content == "yes":
                        reply = "The reported user has been permanently banned.\n"
                    else:
                        reply = "The reported user has been temporarily banned.\n"
                    self.State = State.REVIEWING_FURTHER_ACTION
                    return [reply]
                
                if self.State == State.REVIEWING_CSAM:
                    reply = "This report will be submitted to local authorities. The reported user has been permanently banned.\n"
                    self.State = State.REVIEWING_FURTHER_ACTION
                    return [reply]
                
                if self.State == State.REVIEWING_INTELLECTUAL:
                    if message.content not in ["1", "2"]:
                        return ["That is not a valid option. Please select the number corresponding to the appropriate subcategory for the violating content, or say `cancel` to cancel."]
                    else:
                        self.State = State.REVIEWING_FURTHER_ACTION
                
                if self.State == State.REVIEWING_ILLICIT:
                    if message.content not in ["1", "2", "3"]:
                        return ["That is not a valid option. Please select the number corresponding to the appropriate subcategory for the violating content, or say `cancel` to cancel."]
                    if message.content in ["1", "2"]:
                        self.State = State.REVIEWING_FURTHER_ACTION
                        return
                    if message.content == "3":
                        reply = "This report will be submitted to local authorities. The reported user has been permanently banned.\n"
                        self.State = State.REVIEWING_FURTHER_ACTION
                        return [reply]
                
            
            if self.State == State.REVIEWING_FURTHER_ACTION:
                reply = "Is further action necessary to review this report? Plese respond with `yes` or `no`.\n"
                self.State = State.REVIEWING_FURTHER_ACTION_2
                return [reply]
            if self.State == State.REVIEWING_FURTHER_ACTION_2:
                if message.content != "yes" and message.content != "no":
                    return ["Please respond with `yes` or `no`."]
                if message.content == "yes":
                    reply = "This report will be escalated to a higher moderation team for additional review.\n"
                else:
                    "No further action will be taken.\n"
                reply += self.prompt_new_review()
                return [reply]

            if self.State == State.REVIEWING_NONVIOLATION:
                if message.content != "yes" and message.content != "no":
                    return ["Please respond with `yes` or `no`."]
                
                if message.content == "yes":
                    reply = "The reporting user has been temporarily banned."
                if message.content == "no":
                    reply = "No further action will be taken."
                reply += self.prompt_new_review()
                return [reply]

        return []


    def start_review(self):
        reply = "Here is the next report to review.\n\n"

        self.report = heapq.heappop(self.client.reports_to_review)[1]

        reply += f"User reported: `{self.report.reported_user}`\n"
        reply += f"Message reported: `{self.report.reported_message.content}`\n"
        reply += f"Report category: {self.report.report_category}\n"
        reply += f"Report subcategory: {self.report.report_subcategory}\n"
        reply += f"Additional details filed by reporting: {self.report.additional_details}\n\n"

        # reply += f"Is this in violation of platform policies? Please respond with `yes` or `no`."
        reply += "Is this classification correct? Please respond with `yes` or `no`.\n"
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