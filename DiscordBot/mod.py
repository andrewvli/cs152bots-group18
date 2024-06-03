from enum import Enum, auto
import logging
import discord
from report import Report
import sqlite3

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


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
    REVIEWING_RECLASSIFICATION = auto()
    REVIEWING_CLASSIFICATION = auto()
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
    REVIEW_ANOTHER = auto()
    REVIEW_COMPLETE = auto()


class Review:
    START_KEYWORD = "review"

    def __init__(self, client):
        self.state = State.REVIEW_START
        self.client = client
        self.message = None
        self.report = None

    async def handle_review(self, message):
        logger.debug(
            f"Handling review with state: {self.state} and message: {message.content}")

        if message.content.startswith(self.START_KEYWORD):
            pending_reports = self.fetch_pending_reports()
            if not pending_reports:
                reply = "There are no pending reports to review.\n"
                return [reply]
            reply = f"Thank you for starting the reviewing process. There are {len(pending_reports)} pending reports to review.\n"
            reply += self.start_review(pending_reports)
            logger.debug(f"Replying to review start, state: {self.state}")
            return [reply]

        if self.state == State.REVIEWING_VIOLATION:
            logger.debug("State: REVIEWING_VIOLATION")
            if message.content.lower() not in ["yes", "no"]:
                logger.debug(
                    f"Invalid response in REVIEWING_VIOLATION state: {message.content}")
                return ["Please respond with `yes` or `no`."]
            
            if message.content == "yes":
                await self.report.reported_message.delete()
                reply = "The violating content has been removed.\n"
                reply += self.prompt_new_review()
                return [reply]
            else:
                reply = "Does this content violate platform policies? Please respond with `yes` or `no`."
                self.state = State.REVIEWING_RECLASSIFICATION
                return [reply]

        if self.state == State.REVIEWING_RECLASSIFICATION:
            logger.debug("State: REVIEWING_RECLASSIFICATION")
            if message.content.lower() not in ["yes", "no"]:
                logger.debug(
                    f"Invalid response in REVIEWING_RECLASSIFICATION state: {message.content}")
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
                self.state = State.REVIEWING_CATEGORY
                return [reply]
            else:
                reply = "Does it seem like this content was reported with malicious intent? Please respond with `yes` or `no`."
                self.state = State.REVIEWING_NONVIOLATION
                return [reply]

        if self.state == State.REVIEWING_CATEGORY:
            logger.debug("State: REVIEWING_CATEGORY")
            if message.content.lower() not in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
                logger.debug(
                    f"Invalid response in REVIEWING_CATEGORY state: {message.content}")
            if message.content not in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
                return ["That is not a valid option. Please select the number corresponding to the appropriate category for reporting this message, or say `cancel` to cancel."]

            if message.content == "1":
                self.report.report_category = ReportState.SPAM
                self.state = State.REVIEWING_SPAM
            elif message.content == "2":
                reply = "Which subcategory best describes the nature of this content? Please respond with one of the following options.\n"
                reply += "1. Self-harm or suicidal content.\n"
                reply += "2. Terrorism.\n"
                reply += "3. Threat or depictions of violence and abuse.\n"
                reply += "4. Death or severe injury.\n"
                self.report.report_category = ReportState.HARM_ENDANGERMENT
                self.state = State.REVIEWING_HARM_ENDANGERMENT
                return [reply]
            elif message.content == "3":
                reply = "Which subcategory best describes the nature of this content? Please respond with one of the following options.\n"
                reply += "1. Adult nudity or pornography.\n"
                reply += "2. Sexual harassment or abuse.\n"
                self.report.report_category = ReportState.SEXUALLY_EXPLICIT
                self.state = State.REVIEWING_SEXUALLY_EXPLICIT
                return [reply]
            elif message.content == "4":
                reply = "Which subcategory best describes the nature of this content? Please respond with one of the following options.\n"
                reply += "1. Impersonation.\n"
                reply += "2. Romance.\n"
                reply += "3. Financial.\n"
                self.report.report_category = ReportState.FRAUD_SCAM
                self.state = State.REVIEWING_FRAUD_SCAM
                return [reply]
            elif message.content == "5":
                reply = "Which subcategory best describes the nature of this content? Please respond with one of the following options.\n"
                reply += "1. Health.\n"
                reply += "2. Climate.\n"
                reply += "3. Political.\n"
                self.report.report_category = ReportState.MISINFORMATION
                self.state = State.REVIEWING_MISINFORMATION
                return [reply]
            elif message.content == "6":
                reply = "Which subcategory best describes the nature of this content? Please respond with one of the following options.\n"
                reply += "1. Bullying.\n"
                reply += "2. Revealing private information.\n"
                reply += "3. Hate speech.\n"
                reply += "4. Stalking.\n"
                self.report.report_category = ReportState.HATE_HARASSMENT
                self.state = State.REVIEWING_HATE_HARASSMENT
                return [reply]
            elif message.content == "7":
                self.report.report_category = ReportState.CSAM
                self.state = State.REVIEWING_CSAM
                reply = "This report will be submitted to local authorities. The reported user has been permanently banned.\n"
                return [reply]
            elif message.content == "8":
                reply = "Which subcategory best describes the nature of this content? Please respond with one of the following options.\n"
                reply += "1. Infringes my copyright.\n"
                reply += "2. Infringes my trademark.\n"
                self.report.report_category = ReportState.INTELLECTUAL
                self.state = State.REVIEWING_INTELLECTUAL
                return [reply]
            elif message.content == "9":
                reply = "Which subcategory best describes the nature of this content? Please respond with one of the following options.\n"
                reply += "1. Illegal drug use or sale.\n"
                reply += "2. Sale or promotion of counterfeit goods.\n"
                reply += "3. Black market and smuggling.\n"
                self.report.report_category = ReportState.ILLICIT_TRADE_SUBSTANCES
                self.state = State.REVIEWING_ILLICIT
                return [reply]

        if self.state == State.REVIEWING_SPAM:
            logger.debug("State: REVIEWING_SPAM")            
            reply = "Does the reported user have a history of violation? Please respond with `yes` or `no`."
            self.state = State.REVIEWING_SPAM_2
            return [reply]

        if self.state == State.REVIEWING_SPAM_2:
            logger.debug("State: REVIEWING_SPAM_2")
            if message.content.lower() not in ["yes", "no"]:
                logger.debug(
                    f"Invalid response in REVIEWING_SPAM_2 state: {message.content}")
            if message.content != "yes" and message.content != "no":
                return ["Please respond with `yes` or `no`."]
            if message.content == "yes":
                reply = "The reported user has been permanently banned.\n"
            else:
                reply = "No further action will be taken.\n"
            reply += self.prompt_new_review()
            return [reply]

        if self.state == State.REVIEWING_HARM_ENDANGERMENT:
            logger.debug("State: REVIEWING_HARM_ENDANGERMENT")
            if message.content.lower() not in ["1", "2", "3", "4"]:
                logger.debug(
                    f"Invalid response in REVIEWING_HARM_ENDANGERMENT state: {message.content}")
            if message.content not in ["1", "2", "3", "4"]:
                return ["That is not a valid option. Please select the number corresponding to the appropriate subcategory for the violating content, or say `cancel` to cancel."]
            else:
                reply = "This report will be submitted to local authorities. The reported user has been permanently banned.\n"
                reply += self.prompt_new_review()
                return [reply]
                    
        if self.state == State.REVIEWING_SEXUALLY_EXPLICIT:
            logger.debug("State: REVIEWING_SEXUALLY_EXPLICIT")
            if message.content.lower() not in ["1", "2"]:
                logger.debug(
                    f"Invalid response in REVIEWING_SEXUALLY_EXPLICIT state: {message.content}")
            if message.content not in ["1", "2"]:
                return ["That is not a valid option. Please select the number corresponding to the appropriate subcategory for the violating content, or say `cancel` to cancel."]
            if message.content == "1":
                reply = "The reported user has been permanently banned.\n"
            if message.content == "2":
                reply = "This report will be submitted to local authorities. The reported user has been permanently banned.\n"
            reply += self.prompt_new_review()
            return [reply]
                
        if self.state == State.REVIEWING_FRAUD_SCAM:
            logger.debug("State: REVIEWING_FRAUD_SCAM")
            if message.content.lower() not in ["1", "2", "2"]:
                logger.debug(
                    f"Invalid response in REVIEWING_FRAUD_SCAM state: {message.content}")
            if message.content not in ["1", "2", "3"]:
                return ["That is not a valid option. Please select the number corresponding to the appropriate subcategory for the violating content, or say `cancel` to cancel."]
            if message.content in ["1", "2"]:
                reply = "Does the reported user have a history of violation? Please respond with `yes` or `no`.\n"
                self.state = State.REVIEWING_FRAUD_SCAM_2
                return [reply]
            if message.content == "3":
                reply = "Which subcategory of financial fraud best describes the nature of this content? Please respond with one of the following options.\n"
                reply += "1. Cryptocurrency.\n"
                reply += "2. Investment.\n"
                reply += "3. Phishing.\n"
                reply += "4. Credit card.\n"
                self.state = State.REVIEWING_FINANCIAL
                return [reply]

        if self.state == State.REVIEWING_FRAUD_SCAM_2:
            logger.debug("State: REVIEWING_FRAUD_SCAM_2")
            if message.content.lower() not in ["yes", "no"]:
                logger.debug(
                    f"Invalid response in REVIEWING_FRAUD_SCAM_2 state: {message.content}")
            if message.content != "yes" and message.content != "no":
                return ["Please respond with `yes` or `no`."]
            if message.content == "yes":
                reply = "The reported user has been permanently banned.\n"
            else:
                reply = "No further action will be taken.\n"
            reply += self.prompt_new_review()
            return [reply]

        if self.state == State.REVIEWING_FINANCIAL:
            logger.debug("State: REVIEWING_FINANCIAL")
            reply = "Does the reported message contain any harmful links? Please respond with `yes` or `no`.\n"
            self.state = State.REVIEWING_LINKS
            return [reply]

        if self.state == State.REVIEWING_LINKS:
            logger.debug("State: REVIEWING_LINKS")
            if message.content.lower() not in ["yes", "no"]:
                logger.debug(
                    f"Invalid response in REVIEWING_LINKS state: {message.content}")
            if message.content != "yes" and message.content != "no":
                return ["Please respond with `yes` or `no`."]
            reply = ""
            if message.content == "yes":
                reply += "The harmful links have been blacklisted.\n"
            reply += "The reported user has been permanently banned.\n"
            reply += self.prompt_new_review()
            return [reply]
                
        if self.state == State.REVIEWING_MISINFORMATION:
            logger.debug("State: REVIEWING_MISINFORMATION")
            if message.content.lower() not in ["1", "2", "3"]:
                logger.debug(
                    f"Invalid response in REVIEWING_MISINFORMATION state: {message.content}")
            if message.content not in ["1", "2", "3"]:
                return ["That is not a valid option. Please select the number corresponding to the appropriate subcategory for the violating content, or say `cancel` to cancel."]
            else:
                reply = "Does the reported user have a history of violation? Please respond with `yes` or `no`.\n"
                self.state = State.REVIEWING_MISINFORMATION_2
                return [reply]

        if self.state == State.REVIEWING_MISINFORMATION_2:
            logger.debug("State: REVIEWING_MISINFORMATION_2")
            if message.content.lower() not in ["yes", "no"]:
                logger.debug(
                    f"Invalid response in REVIEWING_MISINFORMATION_2 state: {message.content}")
            if message.content != "yes" and message.content != "no":
                return ["Please respond with `yes` or `no`."]
            if message.content == "yes":
                reply = "The reported user has been flagged.\n"
            reply += self.prompt_new_review()
            return [reply]
                
        if self.state == State.REVIEWING_HATE_HARASSMENT:
            logger.debug("State: REVIEWING_HATE_HARASSMENT")
            if message.content.lower() not in ["1", "2", "3", "4"]:
                logger.debug(
                    f"Invalid response in REVIEWING_HATE_HARASSMENT state: {message.content}")
            if message.content not in ["1", "2", "3", "4"]:
                return ["That is not a valid option. Please select the number corresponding to the appropriate subcategory for the violating content, or say `cancel` to cancel."]
            else:
                reply = "Does the reported user have a history of violation? Please respond with `yes` or `no`.\n"
                self.state = State.REVIEWING_HATE_HARASSMENT_2
                return [reply]

        if self.state == State.REVIEWING_HATE_HARASSMENT_2:
            logger.debug("State: REVIEWING_HATE_HARASSMENT_2")
            if message.content.lower() not in ["yes", "no"]:
                logger.debug(
                    f"Invalid response in REVIEWING_HATE_HARASSMENT_2 state: {message.content}")
            if message.content != "yes" and message.content != "no":
                return ["Please respond with `yes` or `no`."]
            if message.content == "yes":
                reply = "The reported user has been permanently banned.\n"
            else:
                reply = "No further action will be taken.\n"
            reply += self.prompt_new_review()
            return [reply]
                
        if self.state == State.REVIEWING_CSAM:
            logger.debug("State: REVIEWING_CSAM")
            reply = "This report will be submitted to local authorities. The reported user has been permanently banned.\n"
            reply += self.prompt_new_review()
            return [reply]
                
        if self.state == State.REVIEWING_INTELLECTUAL:
            logger.debug("State: REVIEWING_INTELLECTUAL")
            if message.content.lower() not in ["1", "2"]:
                logger.debug(
                    f"Invalid response in REVIEWING_INTELLECTUAL state: {message.content}")
            if message.content not in ["1", "2"]:
                return ["That is not a valid option. Please select the number corresponding to the appropriate subcategory for the violating content, or say `cancel` to cancel."]
            reply = "The reported user has been flagged.\n"
            reply += self.prompt_new_review()
            return [reply]
                
        if self.state == State.REVIEWING_ILLICIT:
            logger.debug("State: REVIEWING_ILLICIT")
            if message.content.lower() not in ["1", "2"]:
                logger.debug(
                    f"Invalid response in REVIEWING_ILLICIT state: {message.content}")
            if message.content not in ["1", "2", "3"]:
                return ["That is not a valid option. Please select the number corresponding to the appropriate subcategory for the violating content, or say `cancel` to cancel."]
            if message.content in ["1", "2"]:
                reply = "The reported user has been flagged.\n"
            if message.content == "3":
                reply = "This report will be submitted to local authorities. The reported user has been permanently banned.\n"
            reply += self.prompt_new_review()
            return [reply]
                
        if self.state == State.REVIEWING_FURTHER_ACTION:            
            reply = "Is further action necessary to review this report? Please respond with `yes` or `no`.\n"
            self.state = State.REVIEWING_FURTHER_ACTION_2
            return [reply]

        if self.state == State.REVIEWING_FURTHER_ACTION_2:
            if message.content != "yes" and message.content != "no":
                return ["Please respond with `yes` or `no`."]
            if message.content == "yes":
                reply = "This report will be escalated to a higher moderation team for additional review.\n"
            else:
                reply = "No further action will be taken.\n"
            reply += self.prompt_new_review()
            return [reply]

        if self.state == State.REVIEWING_NONVIOLATION:
            logger.debug("State: REVIEWING_NONVIOLATION")
            if message.content.lower() not in ["yes", "no"]:
                logger.debug(
                    f"Invalid response in REVIEWING_NONVIOLATION state: {message.content}")
            if message.content != "yes" and message.content != "no":
                return ["Please respond with `yes` or `no`."]
                
            if message.content == "yes":
                reply = "The reporting user has been permanently banned.\n"
            if message.content == "no":
                reply = "No further action will be taken.\n"
            reply += self.prompt_new_review()
            return [reply]

        if self.state == State.REVIEW_ANOTHER:
            logger.debug("State: REVIEW_ANOTHER")
            if message.content.lower() not in ["yes", "no"]:
                logger.debug(
                    f"Invalid response in REVIEW_ANOTHER state: {message.content}")
            if message.content.lower() not in ["yes", "no"]:
                logger.debug(
                    f"Invalid response in REVIEW_ANOTHER state: {message.content}")
                return ["Please respond with `yes` or `no`."]
            if message.content == "yes":
                reply = self.start_review(self.fetch_pending_reports())
                return [reply]
            else:
                self.state = State.REVIEW_COMPLETE
                reply = "No further action will be taken.\n"
                return [reply]

        return []

    def start_review(self, pending_reports):
        logger.debug("Starting review")
        reply = "Here is the next report to review.\n\n"
        self.report = pending_reports.pop(0)

        reply += f"User reported: `{self.report.reported_user}`\n"
        reply += f"Message reported: `{self.report.reported_message}`\n"
        reply += f"Report category: {self.report.report_category}\n"
        reply += f"Report subcategory: {self.report.report_subcategory}\n"
        reply += f"Additional details filed by reporting: {self.report.additional_details}\n\n"

        reply += "Is this classification correct? Please respond with `yes` or `no`.\n"
        self.state = State.REVIEWING_VIOLATION
        logger.debug(f"State changed to: {self.state}")
        return reply

    def prompt_new_review(self):
        logger.debug("Prompting new review")
        reply = "Thank you for reviewing this report.\n"
        pending_reports = self.fetch_pending_reports()
        if not pending_reports:
            reply += "There are no more pending reports to review.\n"
            self.state = State.REVIEW_COMPLETE
            logger.debug(f"State changed to: {self.state}")
        else:
            reply += f"There are {len(pending_reports)} pending reports to review. Would you like to review another report?\n"
            self.state = State.REVIEW_ANOTHER
            logger.debug(f"State changed to: {self.state}")

        return reply

    def fetch_pending_reports(self):
        logger.debug("Fetching pending reports")
        self.client.db_cursor.execute('''
            SELECT report_id, reported_user_id, reporter_user_id, reportee, reported_user, reported_message, 
                   report_category, report_subcategory, additional_details, priority, report_status, time_reported 
            FROM reports WHERE report_status = 'pending' ORDER BY priority, time_reported
        ''')
        pending_reports = self.client.db_cursor.fetchall()
        return [
            Report(
                report_id=row[0],
                reported_user_id=row[1],
                reporter_user_id=row[2],
                reportee=row[3],
                reported_user=row[4],
                reported_message=row[5],
                report_category=row[6],
                report_subcategory=row[7],
                additional_details=row[8],
                priority=row[9],
                report_status=row[10],
                time_reported=row[11]
            ) for row in pending_reports
        ]

    def mark_report_resolved(self):
        logger.debug(f"Marking report {self.report.report_id} as resolved")
        try:
            self.client.db_cursor.execute('''
                UPDATE reports
                SET report_status = 'resolved'
                WHERE report_id = ?
            ''', (self.report.report_id,))
            self.client.db_connection.commit()
        except sqlite3.Error as e:
            logger.error(f"Error marking report as resolved: {e}")
            self.client.db_connection.rollback()
