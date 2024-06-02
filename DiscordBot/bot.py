import discord
from discord.ext import commands
import os
import json
import logging
import re
import openai
import sqlite3
from datetime import datetime
from googleapiclient import discovery
from report import Report
from mod import Review
import heapq

# Set up logging to the console
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(
    filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# There should be a file called 'tokens.json' inside the same folder as this file
token_path = 'tokens.json'
if not os.path.isfile(token_path):
    raise Exception(f"{token_path} not found!")
with open(token_path) as f:
    tokens = json.load(f)
    discord_token = tokens['discord']
    openai_key = tokens['openai']
    google_key = tokens['google']


class ModBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='.', intents=intents)
        self.openai = openai.OpenAI(api_key=openai_key)
        self.group_num = None
        self.mod_channels = {}  # Map from guild to the mod channel id for that guild
        self.db_connection = sqlite3.connect('mod_db.sqlite')
        self.reviews = {}  # Add a dictionary to keep track of reviews per user
        self.reports = {}
        self.reports_to_review = []

        # Create the database schema if it doesn't exist
        self.db_cursor = self.db_connection.cursor()
        self.db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                report_id INTEGER PRIMARY KEY AUTOINCREMENT,
                reported_user_id INTEGER,
                reporter_user_id INTEGER,
                reportee TEXT,
                reported_user TEXT,
                reported_message TEXT,
                report_category TEXT,
                report_subcategory TEXT,
                additional_details TEXT,
                priority INTEGER,
                report_status TEXT DEFAULT 'pending',
                time_reported TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.db_connection.commit()

    async def on_ready(self):
        print(f'{self.user.name} has connected to Discord! It is these guilds:')
        for guild in self.guilds:
            print(f' - {guild.name}')
        print('Press Ctrl-C to quit.')

        match = re.search('[gG]roup (\d+) [bB]ot', self.user.name)
        if match:
            self.group_num = match.group(1)
        else:
            raise Exception(
                "Group number not found in bot's name. Name format should be \"Group # Bot\".")

        for guild in self.guilds:
            for channel in guild.text_channels:
                if channel.name == f'group-{self.group_num}-mod':
                    self.mod_channels[guild.id] = channel

    async def on_message(self, message):
        if message.author.id == self.user.id:
            return

        if message.guild:
            await self.handle_channel_message(message)
        else:
            await self.handle_dm(message)

    async def handle_dm(self, message):
        if message.content == Report.HELP_KEYWORD:
            reply = "Use the `report` command to begin the reporting process.\n"
            reply += "Use the `block` command to begin the blocking process.\n"
            reply += "Use the `cancel` command to cancel the report process.\n"
            await message.channel.send(reply)
            return

        author_id = message.author.id
        responses = []

        # If we don't currently have an active report for this user, add one
        if author_id not in self.reports:
            self.reports[author_id] = Report(self)

        # Check command
        command = message.content.split()[0]
        if command == Report.START_KEYWORD:
            responses = await self.reports[author_id].handle_message(message)
        elif command == Report.BLOCK_KEYWORD:
            responses = await self.reports[author_id].handle_block(message)
        else:
            if author_id in self.reports:
                responses = await self.reports[author_id].handle_message(message)
                blocks = await self.reports[author_id].handle_block(message)
                responses.extend(blocks)

        # Send all responses
        if responses:
            for r in responses:
                await message.channel.send(r)

        # If the report/block is complete or cancelled, remove it from our map
        if self.reports[author_id].report_complete() or self.reports[author_id].block_complete():
            heapq.heappush(self.reports_to_review,
                           (self.reports[author_id].priority, self.reports[author_id]))
            self.reports.pop(author_id)

    async def handle_start_report(self, message):
        author_id = message.author.id
        report = Report(self)

        responses = await report.handle_message(message)
        report.save_report(self.db_cursor, self.db_connection)

        return responses

    async def handle_block_report(self, message):
        author_id = message.author.id
        report = Report(self)

        responses = await report.handle_block(message)
        report.save_report(self.db_cursor, self.db_connection)

        return responses

    async def handle_channel_message(self, message):
        if not (message.channel.name == f'group-{self.group_num}' or message.channel.name == f'group-{self.group_num}-mod'):
            return

        author_id = message.author.id
        responses = []

        if message.channel.name == f'group-{self.group_num}-mod':
            if message.content.split()[0] == Review.START_KEYWORD:
                if author_id not in self.reviews:
                    self.reviews[author_id] = Review(self)
                responses = await self.reviews[author_id].handle_review(message)
            elif author_id in self.reviews:
                responses = await self.reviews[author_id].handle_review(message)
        else:
            openai_flag_type = await self.evaluate_message_openai(message.content)
            perspective_flag_types = await self.evaluate_message_perspective(message.content)

            if openai_flag_type or perspective_flag_types:
                await self.handle_offensive_message(message, openai_flag_type, perspective_flag_types)
            else:
                mod_channel = self.mod_channels[message.guild.id]
                await mod_channel.send(f'Forwarded message:\n{message.author.name}: "{message.content}"')

        if responses:
            for r in responses:
                await message.channel.send(r)

    async def evaluate_message_openai(self, message_content):
        response = self.openai.moderations.create(input=message_content)
        output = response.results[0]

        if output.flagged:
            print(f"Flagged content: {message_content}")
            print(f"Output: {output}")

            flagged_categories = [
                category for category, flagged in output.categories.dict().items() if flagged]

            if flagged_categories:
                return flagged_categories[0]
        return None

    async def evaluate_message_perspective(self, message_content):
        client = discovery.build(
            "commentanalyzer",
            "v1alpha1",
            developerKey=google_key,
            discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
            static_discovery=False,
        )

        analyze_request = {
            'comment': {'text': message_content},
            'requestedAttributes': {
                "TOXICITY": {},
                "SEVERE_TOXICITY": {},
                "IDENTITY_ATTACK": {},
                "INSULT": {},
                "PROFANITY": {},
                "THREAT": {}
            }
        }

        response = client.comments().analyze(body=analyze_request).execute()
        threshold = 0.3  # Can change threshold
        exceeds_threshold, categories = self.check_evaluation_scores(response, threshold)
        if exceeds_threshold:
            print(f"Message exceeds threshold for: {categories}")
        else:
            print("No categories exceed the threshold.")
        return categories

    @staticmethod
    def check_evaluation_scores(response, threshold):
        categories_exceeding_threshold = []
        for attribute, details in response['attributeScores'].items():
            if details['summaryScore']['value'] > threshold:
                categories_exceeding_threshold.append(attribute)

        if categories_exceeding_threshold:
            return True, categories_exceeding_threshold
        else:
            return False, []

    async def generate_report(self, message, openai_flag_type, perspective_flag_types):
        report = Report(self)
        report.reported_user_id = message.author.id
        report.reportee = "System"
        report.reporter_user_id = self.user.id
        report.reported_user = message.author.name
        report.reported_message = message.content
        report.time_reported = datetime.now()
        
        additional_details = []
        if openai_flag_type:
            additional_details.append("Flagged by OpenAI")
        if perspective_flag_types:
            additional_details.append("Flagged by Google Perspective")

        report.additional_details = ", ".join(additional_details)
        report.report_category = openai_flag_type or (perspective_flag_types[0] if perspective_flag_types else "Unknown")
        report.report_subcategory = "N/A"  # Set as string
        report.report_status = "pending"

        # set priority based on flag type
        if openai_flag_type in ['hate/threatening', 'harassment/threatening', 'self-harm/intent', 'sexual/minors', 'violence/graphic'] or \
        any(pt in ['SEVERE_TOXICITY', 'THREAT', 'IDENTITY_ATTACK'] for pt in perspective_flag_types):
            report.priority = 1
        else:
            report.priority = 2

        report.save_report(self.db_cursor, self.db_connection)

        mod_channel = self.mod_channels.get(message.guild.id)
        if mod_channel:
            await mod_channel.send(
                f"🚩 **Report Generated** 🚩\n"
                f"**User:** {message.author.name}\n"
                f"**Reason:** {openai_flag_type or ', '.join(perspective_flag_types)}\n"
                f"**Message:** {message.content}\n"
                f"**Time:** {report.time_reported.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"**Details:** {report.additional_details}"
            )
        else:
            logger.warning("No mod channel found for the guild.")
        report.save_report(self.db_cursor, self.db_connection)


    async def handle_offensive_message(self, message, openai_flag_type, perspective_flag_types):
        try:
            await message.delete()
        except discord.errors.NotFound:
            logger.warning(f"Message {message.id} already deleted.")

        await message.author.send(
            f"Your message in {message.channel.name} was removed because it was flagged as "
            f"{openai_flag_type or ', '.join(perspective_flag_types)}. "
            "Please be mindful of the community guidelines."
        )

        await self.generate_report(message, openai_flag_type, perspective_flag_types)


client = ModBot()
client.run(discord_token)
