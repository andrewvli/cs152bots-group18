import discord
from discord.ext import commands, tasks
import json
import asyncio
from sklearn.metrics import confusion_matrix, classification_report

# Load your bot token securely from the `tokens.json` file
with open('tokens.json') as f:
    tokens = json.load(f)
    discord_token = tokens['discord']

# Configuration
CHANNEL_NAME = 'group-18'  # Replace with the actual channel name
INTERVAL_SECONDS = 10  # Adjust as needed
TEST_CASES = [
    ("https://www.google.com", False),
    ("https://www.wikipedia.org", False),
    ("https://www.github.com", False),
    ("https://www.stackoverflow.com", False),
    ("https://www.python.org", False),
    ("https://www.gooogle.com", True),
    ("https://www.wikipeedia.org", True),
    ("https://www.gihub.com", True),
    ("https://www.stakoverflow.com", True),
    ("https://www.pyhton.org", True)
]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents)

# Collect results
true_labels = []
predicted_labels = []
flagged_messages = set()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    send_test_messages.start()  # Start the message sending loop

@tasks.loop(seconds=INTERVAL_SECONDS)
async def send_test_messages():
    for guild in bot.guilds:
        channel = discord.utils.get(guild.channels, name=CHANNEL_NAME)
        if channel:
            for url, expected in TEST_CASES:
                try:
                    message = await channel.send(url)
                    true_labels.append(expected)
                    # Store message.id to check for moderation response
                    flagged_messages.add(message.id)
                    await asyncio.sleep(INTERVAL_SECONDS)  # Wait before sending the next message
                except discord.Forbidden:
                    print(f"Don't have permission to send messages in '{CHANNEL_NAME}' in server '{guild.name}'.")
                except Exception as e:
                    print(f"Error sending message: {e}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.name == CHANNEL_NAME and message.id in flagged_messages:
        # Check if the bot's response indicates the message was flagged
        flagged = 'Warning: Potentially harmful link detected' in message.content
        predicted_labels.append(flagged)
        flagged_messages.remove(message.id)

        # If all messages have been processed, compute the confusion matrix and classification report
        if not flagged_messages:
            conf_matrix = confusion_matrix(true_labels, predicted_labels)
            report = classification_report(true_labels, predicted_labels, target_names=["Not Flagged", "Flagged"])
            print("Confusion Matrix:")
            print(conf_matrix)
            print("\nClassification Report:")
            print(report)
            await bot.close()

bot.run(discord_token)
