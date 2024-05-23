import discord
from discord.ext import commands
import os
import json
import logging
import re
import requests
import heapq
from report import Report
from mod import Review
import pdb
import aiohttp

# Set up logging
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Load the tokens
token_path = 'tokens.json'
if not os.path.isfile(token_path):
    raise Exception(f"{token_path} not found!")
with open(token_path) as f:
    tokens = json.load(f)
    discord_token = tokens['discord']
    google_apikey = tokens['google']

class ModBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.group_num = None
        self.mod_channels = {}

    async def on_ready(self):
        print(f'{self.user.name} has connected to Discord!')
        for guild in self.guilds:
            print(f' - {guild.name}')
        print('Press Ctrl-C to quit.')
        match = re.search(r'Group (\d+)', self.user.name)
        if match:
            self.group_num = match.group(1)
        else:
            logger.error("Bot's name does not contain a group number.")

    async def on_message(self, message):
        if message.author.id == self.user.id:
            return
        if message.guild and message.channel.name.startswith(f'group-{self.group_num}'):
            await self.handle_channel_message(message)
        else:
            await self.handle_dm(message)

    async def handle_channel_message(self, message):
        urls = re.findall(r'(https?://\S+)', message.content)
        print('urls:', urls)
        result = await self.check_urls(urls)
        if len(result) > 0:
                print("Potentially harmful link detected by Google Safe Browsing API.")
                warning_message = f"Warning: Potentially harmful link detected in the message\n`{message.content}`\n\n"
                warning_message += "Please be cautious!"
                await message.channel.send(warning_message)

                if message.author.dm_channel is None:
                    await message.author.create_dm()
                author_warning_message = f"Warning: A potentially harmful link was detected in a message you sent.\n`{message.content}\n\n`"
                author_warning_message += "Please be mindful of platform policies when sharing links."
                await message.author.dm_channel.send(author_warning_message)

    async def check_urls(self, urls):
        url = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
        payload = {
            'client': {
                'clientId': "discord-bot",
                'clientVersion': "0.1"
            },
            'threatInfo': {
                'threatTypes': ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION", "THREAT_TYPE_UNSPECIFIED", "PHISHING"],
                'platformTypes': ["ANY_PLATFORM", "PLATFORM_TYPE_UNSPECIFIED", "WINDOWS", "LINUX", "ANDROID", "OSX", "IOS", "CHROME"],
                'threatEntryTypes': ["URL", "THREAT_ENTRY_TYPE_UNSPECIFIED", "EXECUTABLE"],
                'threatEntries': [{"url": u} for u in urls]
            }
        }
        params = {'key': google_apikey}  # Ensure you use self.google_apikey if it's stored in the class
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params, json=payload) as response:
                result = await response.json()
                print("result:", result)  # Print to debug
                return result

client = ModBot()
client.run(discord_token)
