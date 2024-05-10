from enum import Enum, auto
import discord
import re

class State(Enum):
    REPORT_START = auto()
    AWAITING_MESSAGE = auto()
    MESSAGE_IDENTIFIED = auto()
    BLOCK_USER = auto()
    REPORT_COMPLETE = auto()
    BLOCK_START = auto()
    AWAITING_BLOCK = auto()
    AWAITING_BLOCK_CONFIRM = auto()
    BLOCK_COMPLETE = auto()
    PROMPTING_ADDITIONAL_DETAILS = auto()
    AWAITING_DETAILS = auto()

    # Abuse Types
    SPAM = auto()
    OFFENSIVE_CONTENT = auto()
    NUDITY = auto()
    FRAUD = auto()
    FINANCIAL_FRAUD_CLASSIFICATION = auto()
    MISINFORMATION = auto()
    HATE_HARASSMENT = auto()
    CSAM = auto()
    INTELLECTUAL = auto()

class Report:
    START_KEYWORD = "report"
    CANCEL_KEYWORD = "cancel"
    HELP_KEYWORD = "help"
    BLOCK_KEYWORD = "block"
    REPORTING_OPTIONS = ["1", "2", "3", "4", "5", "6", "7", "8"]

    def __init__(self, client):
        self.state = None  # Allows transition between `report` and `block` midway through processes
        self.client = client
        self.message = None
        self.reported_user = None
        self.reported_message = None
        self.report_category = None
        self.additional_details = None
    
    async def handle_message(self, message):
        '''
        This function makes up the meat of the user-side reporting flow. It defines how we transition between states and what 
        prompts to offer at each of those states. You're welcome to change anything you want; this skeleton is just here to
        get you started and give you a model for working with Discord. 
        '''

        if message.content == self.CANCEL_KEYWORD:
            self.state = State.REPORT_COMPLETE
            return ["Process cancelled."]

        if message.content.startswith(self.BLOCK_KEYWORD):
            return await self.handle_block(message)
        
        if message.content.startswith(self.START_KEYWORD):
            reply =  "Thank you for starting the reporting process."
            reply += "Say `help` at any time for more information.\n\n"
            reply += "Please copy paste the link to the message you want to report.\n"
            reply += "You can obtain this link by right-clicking the message and clicking `Copy Message Link`."
            self.state = State.AWAITING_MESSAGE
            return [reply]

        if self.state == State.AWAITING_MESSAGE:
            # Parse out the three ID strings from the message link
            m = re.search('/(\d+)/(\d+)/(\d+)', message.content)
            if not m:
                return ["I'm sorry, I couldn't read that link. Please try again or say `cancel` to cancel."]
            guild = self.client.get_guild(int(m.group(1)))
            if not guild:
                return ["I cannot accept reports of messages from guilds that I'm not in. Please have the guild owner add me to the guild and try again."]
            channel = guild.get_channel(int(m.group(2)))
            if not channel:
                return ["It seems this channel was deleted or never existed. Please try again or say `cancel` to cancel."]
            try:
                message = await channel.fetch_message(int(m.group(3)))
            except discord.errors.NotFound:
                return ["It seems this message was deleted or never existed. Please try again or say `cancel` to cancel."]

            # Here we've found the message - it's up to you to decide what to do next!
            self.state = State.MESSAGE_IDENTIFIED
            self.reported_user = message.author.name
            self.reported_message = message.content
            reply = "I found this message:" + "```" + message.author.name + ": " + message.content + "```" + "\n\n"
            reply += "Why are you reporting this message? Please select the number corresponding to the appropriate category.\n"
            reply += "1. Spam.\n"
            reply += "2. Offensive content.\n"
            reply += "3. Nudity and sexual content.\n"
            reply += "4. Fraud or scam.\n"
            reply += "5. Misinformation.\n"
            reply += "6. Hate and harassment.\n"
            reply += "7. Child sexual abuse material.\n"
            reply += "8. Intellectual property theft.\n"
            return [reply]
        
        if self.state == State.MESSAGE_IDENTIFIED:
            if message.content not in self.REPORTING_OPTIONS:
                return ["That is not a valid option. Please select the number corresponding to the appropriate category for reporting this message, or say `cancel` to cancel."]

            return self.classify_report(message)

        if self.state == State.OFFENSIVE_CONTENT:
            if message.content not in ["1", "2", "3", "4"]:
                return ["That is not a valid option. Please select the number corresponding to the appropriate category for reporting this message, or say `cancel` to cancel."]
            
            return self.complete_report()
        
        if self.state == State.NUDITY:
            if message.content not in ["1", "2"]:
                return ["That is not a valid option. Please select the number corresponding to the appropriate category for reporting this message, or say `cancel` to cancel."]
            
            return self.complete_report()
        
        if self.state == State.FRAUD:
            if message.content not in ["1", "2", "3", "4"]:
                return ["That is not a valid option. Please select the number corresponding to the appropriate category for reporting this message, or say `cancel` to cancel."]
            
            if message.content == "4":
                self.state = State.FINANCIAL_FRAUD_CLASSIFICATION
                reply = "What kind of financial fraud are you reporting?\n"
                reply += "1. Cryptocurrency.\n"
                reply += "2. Investment.\n"
                reply += "3. Phishing.\n"
                reply += "4. Credit card fraud.\n"
                return [reply]
            
            return self.complete_report()
        
        if self.state == State.FINANCIAL_FRAUD_CLASSIFICATION:
            if message.content not in ["1", "2", "3", "4"]:
                return ["That is not a valid option. Please select the number corresponding to the appropriate category for reporting this message, or say `cancel` to cancel."]
            
            self.state = State.PROMPTING_ADDITIONAL_DETAILS
            reply = "We may investigate your private message history when evaluating this report. Would you like to include any additional details? Please respond with `yes` or `no`."
            return [reply]
        
        if self.state == State.MISINFORMATION:
            if message.content not in ["1", "2"]:
                return ["That is not a valid option. Please select the number corresponding to the appropriate category for reporting this message, or say `cancel` to cancel."]
            
            self.state = State.MISINFORMATION
            return self.complete_report()
        
        if self.state == State.HATE_HARASSMENT:
            if message.content not in ["1", "2", "3", "4"]:
                return ["That is not a valid option. Please select the number corresponding to the appropriate category for reporting this message, or say `cancel` to cancel."]
            
            self.state = State.HATE_HARASSMENT
            return self.complete_report()
        
        if self.state == State.INTELLECTUAL:
            if message.content not in ["1", "2"]:
                return ["That is not a valid option. Please select the number corresponding to the appropriate category for reporting this message, or say `cancel` to cancel."]
            
            self.state = State.HATE_HARASSMENT
            return self.complete_report()
        
        if self.state == State.PROMPTING_ADDITIONAL_DETAILS:
            if message.content != "yes" and message.content != "no":
                return ["That is not a valid option. Please reply with `yes` or `no`."]
            
            self.state = State.AWAITING_DETAILS
            if message.content == "yes":
                return ["Please provide any additional details below."]
            elif message.content == "no":
                return self.complete_report()

        if self.state == State.AWAITING_DETAILS:
            self.additional_details = message.content
            return self.complete_report()
        
        if self.state == State.BLOCK_USER:
            if message.content != "yes" and message.content != "no":
                return ["That is not a valid option. Please reply with `yes` or `no`."]
            
            self.state = State.REPORT_COMPLETE
            if message.content == "yes":
                return ["Thank you. The user has been blocked."]
            else: 
                return []

        return []
    

    def classify_report(self, message):
        if message.content == "1":
            self.report_category = State.SPAM
            return self.complete_report()
        elif message.content == "2":
            self.state = State.OFFENSIVE_CONTENT
            self.report_category = State.OFFENSIVE_CONTENT
            return self.classify_offensive_content()
        elif message.content == "3":
            self.state = State.NUDITY
            self.report_category = State.NUDITY
            return self.classify_nudity()
        elif message.content == "4":
            self.state = State.FRAUD
            self.report_category = State.FRAUD
            return self.classify_fraud()
        elif message.content == "5":
            self.state = State.MISINFORMATION
            self.report_category = State.MISINFORMATION
            return self.classify_misinformation()
        elif message.content == "6":
            self.state = State.HATE_HARASSMENT
            self.report_category = State.HATE_HARASSMENT
            return self.classify_hate_harassment()
        elif message.content == "7":
            self.report_category = State.CSAM
            return self.complete_report()
        else:
            self.state = State.INTELLECTUAL
            self.report_category = State.INTELLECTUAL
            return self.classify_intellectual()


    def complete_report(self):
        self.state = State.BLOCK_USER
        reply = "Thank you for submitting a report. Our content moderation will review the report and take appropriate action. This may include contacting local authorities.\n\n"
        reply += f"Would you like to block `{self.reported_user}`?\n"
        reply += "You will no longer be able to interact with them.\n"
        reply += "Please reply with `yes` or `no`."
        return [reply]
    
    
    def classify_offensive_content(self):
        reply = "What kind of offensive content are you reporting? Please select the number corresponding to the appropriate category.\n\n"
        reply += "1. Illegal drug use.\n"
        reply += "2. Gore and graphic violence.\n"
        reply += "3. Sale or promotion of counterfeit goods.\n"
        reply += "4. Self-harm or suicidal content.\n"
        return [reply]
    
    
    def classify_nudity(self):
        reply = "What kind of sexually explicit content are you reporting? Please select the number corresponding to the appropriate category.\n\n"
        reply += "1. Adult nudity.\n"
        reply += "2. Adult pornography.\n"
        return [reply]
    

    def classify_fraud(self):
        reply = "What kind of fraud or scam are you reporting? Please select the number corresponding to the appropriate category.\n\n"
        reply += "1. Impersonation.\n"
        reply += "2. Romance.\n"
        reply += "3. Investment.\n"
        reply += "4. Financial.\n"
        return [reply]
    

    def classify_misinformation(self):
        reply = "What kind of misinformation are you reporting? Please select the number corresponding to the appropriate category.\n\n"
        reply += "1. Health.\n"
        reply += "2. Climate.\n"
        return [reply]
    

    def classify_hate_harassment(self):
        reply = "What kind of hate or harassment are you reporting? Please select the number corresponding to the appropriate category.\n\n"
        reply += "1. Bullying.\n"
        reply += "2. Revealing private information.\n"
        reply += "3. Hate speech.\n"
        reply += "4. Credible threats of violence.\n"
        return [reply]
    

    def classify_intellectual(self):
        reply = "What kind of intellectual property theft are you reporting? Please select the number corresponding to the appropriate category.\n\n"
        reply += "1. Infringes my copyright.\n"
        reply += "2. Infringes my trademark.\n"
        return [reply]


    def report_complete(self):
        return self.state == State.REPORT_COMPLETE


    async def handle_block(self, message):
        if message.content == self.CANCEL_KEYWORD:
            self.state = State.BLOCK_COMPLETE

        if message.content.startswith(self.START_KEYWORD):
            return await self.handle_message(message)
        
        if message.content.startswith(self.BLOCK_KEYWORD):
            self.state = State.BLOCK_START
            reply = "Thank you for starting the blocking process.\n"
            reply += "Say `help` at any time for more information.\n\n"
            reply += "Please copy paste the username of the user you want to block.\n"
            reply += "You can obtain this by right-clicking the user, clicking `Profile,` and copying the username."
            self.state = State.AWAITING_BLOCK
            return [reply]

        if self.state == State.AWAITING_BLOCK:
            self.reported_user = message.content.lower()
            reply = "Please confirm that you would like to block '" + self.reported_user + "'\n"
            reply += "You will no longer be able to interact with them.\n"
            reply += "Please reply with `yes` or `no`."
            self.state = State.AWAITING_BLOCK_CONFIRM
            return [reply]
        
        if self.state == State.AWAITING_BLOCK_CONFIRM:
            if message.content.lower() == "yes":
                reply = "Thank you. User '" + self.reported_user + "' has been blocked."
            else:
                reply = "Thank you. User '" + self.reported_user + "' has not been blocked."
            self.state = State.BLOCK_COMPLETE
            return [reply]

        return []

    def block_complete(self):
        return self.state == State.BLOCK_COMPLETE