# bot.py
import aiohttp
import discord
from discord.ext import commands
import os
import json
import logging
import re
import heapq
from report import Report
from mod import Review

# Set up logging to the console
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# There should be a file called 'tokens.json' inside the same folder as this file
token_path = 'tokens.json'
if not os.path.isfile(token_path):
    raise Exception(f"{token_path} not found!")
with open(token_path) as f:
    # If you get an error here, it means your token is formatted incorrectly. Did you put it in quotes?
    tokens = json.load(f)
    discord_token = tokens['discord']
    google_apikey = tokens['google']

class ModBot(discord.Client):
    def __init__(self): 
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='.', intents=intents)
        self.group_num = None
        self.mod_channels = {} # Map from guild to the mod channel id for that guild
        self.reports = {} # Map from user IDs to the state of their report
        self.reviews = {}
        self.reports_to_review = []

    async def on_ready(self):
        print(f'{self.user.name} has connected to Discord! It is these guilds:')
        for guild in self.guilds:
            print(f' - {guild.name}')
        print('Press Ctrl-C to quit.')

        # Parse the group number out of the bot's name
        match = re.search('[gG]roup (\d+) [bB]ot', self.user.name)
        if match:
            self.group_num = match.group(1)
        else:
            raise Exception("Group number not found in bot's name. Name format should be \"Group # Bot\".")

        # Find the mod channel in each guild that this bot should report to
        for guild in self.guilds:
            for channel in guild.text_channels:
                if channel.name == f'group-{self.group_num}-mod':
                    self.mod_channels[guild.id] = channel
        

    async def on_message(self, message):
        '''
        This function is called whenever a message is sent in a channel that the bot can see (including DMs). 
        Currently the bot is configured to only handle messages that are sent over DMs or in your group's "group-#" channel. 
        '''
        # Ignore messages from the bot 
        if message.author.id == self.user.id:
            return

        # Check if this message was sent in a server ("guild") or if it's a DM
        if message.guild:
            await self.handle_channel_message(message)
        else:
            await self.handle_dm(message)

    async def handle_dm(self, message):
        # Handle a help message
        if message.content == Report.HELP_KEYWORD:
            reply =  "Use the `report` command to begin the reporting process.\n"
            reply += "Use the `block` command to begin the blocking process.\n"
            reply += "Use the `cancel` command to cancel the report process.\n"
            await message.channel.send(reply)
            return

        author_id = message.author.id
        responses = []
        blocks = []

        # If we don't currently have an active report for this user, add one
        if author_id not in self.reports:
            self.reports[author_id] = Report(self)

        # Check command
        command = message.content.split()[0]
        if command == Report.START_KEYWORD:
            responses = await self.reports[author_id].handle_message(message)
        elif command == Report.BLOCK_KEYWORD:
            blocks = await self.reports[author_id].handle_block(message)
        else:
            # If it's neither, it might still be in the middle of an ongoing report/block process
            if author_id in self.reports:
                responses = await self.reports[author_id].handle_message(message)
                blocks = await self.reports[author_id].handle_block(message)

        if responses: 
            for r in responses:
                await message.channel.send(r)
        if blocks:
            for b in blocks:
                await message.channel.send(b)

        # If the report/block is complete or cancelled, remove it from our map
        if self.reports[author_id].report_complete() or self.reports[author_id].block_complete():
            heapq.heappush(self.reports_to_review, (self.reports[author_id].priority, self.reports[author_id]))
            self.reports.pop(author_id)
        

    async def handle_channel_message(self, message):
        # Only handle messages sent in the "group-#" or "group-#-mod" channel
        if not message.channel.name == f'group-{self.group_num}' and not message.channel.name == f'group-{self.group_num}-mod':
            return
                
        author_id = message.author.id
        responses = []

        if author_id not in self.reviews:
            self.reviews[author_id] = Review(self)
            
        if message.channel.name == f'group-{self.group_num}-mod':
            if message.content.split()[0] == Review.START_KEYWORD:
                responses = await self.reviews[author_id].handle_review(message)
            else: 
                if author_id in self.reviews:
                    responses = await self.reviews[author_id].handle_review(message)
        else:
            urls = re.findall(r'(https?://\S+)', message.content)
            result = await self.check_urls(urls)
            if len(result) > 0:
                print("result:", result)
                warning_message = f"Warning: Potentially harmful link detected in the message\n`{message.content}`\n\n"
                warning_message += "Please be cautious!"
                await message.channel.send(warning_message)

                if message.author.dm_channel is None:
                    await message.author.create_dm()
                author_warning_message = f"Warning: A potentially harmful link was detected in a message you sent.\n`{message.content}\n\n`"
                author_warning_message += "Please be mindful of platform policies when sharing links."
                await message.author.dm_channel.send(author_warning_message)


        if responses: 
            for r in responses:
                await message.channel.send(r)

        # Forward the message to the mod channel
        # mod_channel = self.mod_channels[message.guild.id]
        # await mod_channel.send(f'Forwarded message:\n{message.author.name}: "{message.content}"')
        # scores = self.eval_text(message.content)
        # await mod_channel.send(self.code_format(scores))
    
    def eval_text(self, message):
        ''''
        TODO: Once you know how you want to evaluate messages in your channel, 
        insert your code here! This will primarily be used in Milestone 3. 
        '''
        return message

    
    def code_format(self, text):
        ''''
        TODO: Once you know how you want to show that a message has been 
        evaluated, insert your code here for formatting the string to be 
        shown in the mod channel. 
        '''
        return "Evaluated: '" + text+ "'"
    
    async def check_urls(self, urls):
        url = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
        payload = {
            'client': {
                'clientId': "discord-bot",
                'clientVersion': "0.1"
            },
            'threatInfo': {
                'threatTypes': ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION", "THREAT_TYPE_UNSPECIFIED"],
                'platformTypes': ["ANY_PLATFORM", "PLATFORM_TYPE_UNSPECIFIED", "WINDOWS", "LINUX", "ANDROID", "OSX", "IOS", "CHROME"],
                'threatEntryTypes': ["URL", "THREAT_ENTRY_TYPE_UNSPECIFIED", "EXECUTABLE"],
                'threatEntries': [{"url": u} for u in urls]
            }
        }
        params = {'key': google_apikey} 
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params, json=payload) as response:
                result = await response.json()
                return result


client = ModBot()
client.run(discord_token)