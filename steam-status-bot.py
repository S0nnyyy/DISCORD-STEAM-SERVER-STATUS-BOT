import discord
import requests
import json
import asyncio

# Replace with your bot's token
BOT_TOKEN = ''
# The channel IDs where you want to post updates
UPDATE_CHANNEL_ID = #
DATA_CENTER_CHANNEL_ID = # 

# List of game IDs and their names from Steam
games = {
    "413150": "Stardew Valley",
    "578080": "PUBG",
    "271590": "GTA:V",
    "1245620": "Elden Ring",
    "244390": "Rust"
}

# List of data center names from Steam API
data_centers = [
    "Peru", "EU Germany", "EU Austria", "EU Poland", "Hong Kong",
    "EU Spain", "Chile", "US California", "US Atlanta", "EU Sweden",
    "Emirates", "US Seattle", "South Africa", "Brazil", "US Virginia",
    "US Chicago", "Japan", "EU Finland", "India Mumbai", "India Chennai",
    "Argentina", "South Korea", "Singapore", "Australia", "China Chengdu",
    "China Shanghai", "China Tianjin", "China Guangzhou"
]

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# Dictionary to store message IDs for game updates and data center status
update_message_ids = {}
data_center_message_ids = {dc: None for dc in data_centers}

# Function to fetch game update news from Steam API


async def fetch_game_updates():
    update_messages = []
    for game_id, game_name in games.items():
        response = requests.get(
            f"http://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/?appid={game_id}&count=1&maxlength=300&format=json"
        )
        if response.status_code == 200:
            data = response.json()
            news_items = data.get('appnews', {}).get('newsitems', [])
            if news_items:
                latest_news = news_items[0]
                title = latest_news['title']
                url = latest_news['url']
                # Keep HTML for now, can be filtered if needed
                description = latest_news['contents']
                embed = discord.Embed(
                    title=title,
                    url=url,
                    description=description,
                    color=0xE74C3C
                )
                update_messages.append((game_name, embed))
        else:
            print(f"Failed to retrieve news for game ID {game_id}")

    return update_messages

# Function to fetch data center status from Steam API


async def fetch_data_center_status():
    url = 'https://api.steampowered.com/ICSGOServers_730/GetGameServersStatus/v1/'
    params = {
        'key': 'STEAM API KEY'
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get('result', {}).get('datacenters', {})
        else:
            print(
                f"Failed to fetch data center status. Status code: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Exception occurred while fetching data center status: {e}")
        return {}

# Function to update or send game update messages


async def update_game_update_messages(channel, game_name, embed):
    # Check if there's already an existing message for this game
    message_id = update_message_ids.get(game_name)
    if message_id:
        try:
            message = await channel.fetch_message(message_id)
            await message.edit(embed=embed)
        except discord.NotFound:
            print(
                f"Message with ID {message_id} not found in channel {channel.id}")
        except discord.HTTPException as e:
            print(f"Failed to edit message: {e}")
    else:
        try:
            sent_message = await channel.send(content=f"@everyone PRÁVĚ BYL VYDÁN NOVÝ UPDATE ZE HRY {game_name}!", embed=embed)
            update_message_ids[game_name] = sent_message.id
        except discord.HTTPException as e:
            print(f"Failed to send message: {e}")

# Function to update or send data center status message


async def update_data_center_messages(channel, datacenters):
    # Fetch all existing messages in the channel
    messages = []
    async for message in channel.history(limit=None):
        messages.append(message)

    # Delete existing data center messages
    for message in messages:
        for dc_name in datacenters:
            if dc_name in message.content:
                await message.delete()

    # Send or update messages for each data center
    for dc_name, dc_info in datacenters.items():
        capacity = dc_info.get('capacity', 'Unknown')
        load = dc_info.get('load', 'Unknown')

        # Determine color based on capacity
        if capacity == 'full':
            color = discord.Color.gold()
        elif capacity == 'medium':
            color = discord.Color.green()
        elif capacity == 'low':
            color = discord.Color.orange()
        else:
            color = discord.Color.red()

        embed = discord.Embed(
            title=f"{dc_name} Data Center",
            description=f"**Capacity:** {capacity}\n**Load:** {load}",
            color=color
        )

        # Check if there's already an existing message for this data center
        message_id = data_center_message_ids.get(dc_name)
        if message_id:
            try:
                message = await channel.fetch_message(message_id)
                await message.edit(embed=embed)
            except discord.NotFound:
                print(
                    f"Message with ID {message_id} not found in channel {channel.id}")
            except discord.HTTPException as e:
                print(f"Failed to edit message: {e}")
        else:
            try:
                sent_message = await channel.send(embed=embed)
                data_center_message_ids[dc_name] = sent_message.id
            except discord.HTTPException as e:
                print(f"Failed to send message: {e}")

# Background task to periodically update game updates and data center statuses


async def update_tasks():
    await client.wait_until_ready()

    update_channel = client.get_channel(UPDATE_CHANNEL_ID)
    if not update_channel:
        print(f"Update channel with ID {UPDATE_CHANNEL_ID} not found")
        return

    data_center_channel = client.get_channel(DATA_CENTER_CHANNEL_ID)
    if not data_center_channel:
        print(
            f"Data center channel with ID {DATA_CENTER_CHANNEL_ID} not found")
        return

    while not client.is_closed():
        # Fetch and send game updates
        update_messages = await fetch_game_updates()
        for game_name, embed in update_messages:
            await update_game_update_messages(update_channel, game_name, embed)

        # Fetch and update data center statuses
        datacenters = await fetch_data_center_status()
        if datacenters:
            await update_data_center_messages(data_center_channel, datacenters)

        await asyncio.sleep(30)  # Check every 30 seconds

# Event: When bot is ready


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    client.loop.create_task(update_tasks())

client.run(BOT_TOKEN)

