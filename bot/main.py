import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import os
from configs.config import IMAGES_HELPER_PATH

if not os.path.exists(IMAGES_HELPER_PATH):
    print("\n⚠️ Error: Required directory 'images_helper_files' not found!")
    print("\nPlease run the following scripts in order:")
    print("1. python scripts/setup_directories.py")
    print("2. python scripts/league_status_checker.py")
    sys.exit(1)

import discord
from discord.ext import commands, tasks
from discord.commands import Option, SlashCommandGroup
from common_utils.fixture_utils import get_team_names_from_fixture, get_thread_embed
import asyncio
from datetime import datetime, timezone
import time
from threading import current_thread

from bot.utils.task_manager import TaskManager
from bot.utils.teams_organizer import TeamsOrganizer

from bot.services.bot_backend import only_stats_main

from configs.config import (
    footer_icon_url, 
    embed_color, 
    footer_text,
    website_name,
    website_url,
    website_field_name,
    MAX_SIMULTANEOUS_GAMES,
    BOT_TOKEN
)

from common_utils.time_logging import configure_logging

intents = discord.Intents.default()
bot = commands.Bot(intents=intents)

# Create a logger for the bot
bot_logger = configure_logging("bot_main", "system")

#Teams Organizer
teams_organizer = TeamsOrganizer()

#Task Manager
task_manager = TaskManager()
  
  
#Ping command
@bot.slash_command(
    name="ping", 
    description="Check the bot's latency"
)
async def ping(ctx):
    bot_logger.info(f"Ping command used by {ctx.author} (ID: {ctx.author.id})")
    # Check if the command is used in a DM
    if ctx.guild is None:
        return
        
    # Record the time when the command was received to calculate initial latency
    initial_response_time = time.time()

    # Calculate the WebSocket latency in milliseconds
    latency = round(bot.latency * 1000, 2)

    # Send an initial response. This is required before editing the response.
    #await ctx.response.send_message(f"Calculating ping...")

    # Calculate the round-trip time in milliseconds
    round_trip_time = round((time.time() - initial_response_time) * 1000, 2)

    # To edit the original response, use the follow-up interface
    await ctx.respond(
        content=f"```Ping!\nInitial response: {latency}ms\nRound-trip: {round_trip_time}ms\n\nReady to follow live matches!```"
    )

# Autocomplete function
async def team_autocomplete(ctx: discord.AutocompleteContext):
    # Filter teams based on the user input
    return [
        team for team in teams_organizer.football_teams if team.lower().startswith(ctx.value.lower())
    ]

#Next game command
@bot.slash_command(
    name="next_game",
    description="Get the next game of a single team.",
)
async def team_schedule(
    ctx,
    team_name: Option(str, "Choose a football team", autocomplete=team_autocomplete),
):
    bot_logger.info(f"Next_game command used by {ctx.author} (ID: {ctx.author.id}) for team: {team_name}")
    def extract_datetime_european_format(date_str):
        # Parse the date string to a datetime object
        date_obj = datetime.fromisoformat(date_str)

        # Format the date part
        date_part = date_obj.strftime("%d/%m/%Y @ ")

        # Check if both the hour and minute are 0
        if date_obj.hour == 0 and date_obj.minute == 0:
            time_part = "Not Determined"
        else:
            # Format the time part in a 24-hour format
            time_part = date_obj.strftime("%H:%M")

        return date_part + time_part

    if ctx.guild is None:
        return

    # Verify if the selected team is in the list of football teams
    if team_name in teams_organizer.football_teams:
        # Respond with the selected team if it is in the list

        team_league = teams_organizer.find_team_id(team_name)
        fixture_id, fixture_date = teams_organizer.new_find_next_fixture(team_league)
        # Assuming fixture_id returns the (id, date)

        home_team, away_team = get_team_names_from_fixture(
            fixture_id
        ) 
        
        formatted_date = extract_datetime_european_format(fixture_date)

        game = {"teams": f"{home_team} vs {away_team}", "datetime": formatted_date}

        # Customizable embed color
        embed = discord.Embed(
            title=f"{home_team} vs {away_team}",
            description=f"**> 📅 {game['datetime']}**",
            color=embed_color,
            timestamp=datetime.now(),
        )
        embed.add_field(
            name=website_field_name,
            value=f"> [{website_name}]({website_url})",
            inline=False,
        )
                   
        embed.set_footer(text=footer_text, icon_url=footer_icon_url)

        await ctx.respond(content=None, embed=embed)

    else:
        # Respond with an error message if the team is not in the list
        await ctx.respond(
            f"{team_name} is not a valid team. Please select a team from the list."
        )

#Follow command
@bot.slash_command(
    name="follow",
    description="Follow any live match and get its stats and events!"
)
async def team_following(
    ctx,
    team_name: Option(str, "Choose a football team", autocomplete=team_autocomplete),
    events_id: Option(str, "Enter the announcements channel id:", required=False, default=0)
):
    bot_logger.info(f"Follow command used by {ctx.author} (ID: {ctx.author.id}) for team: {team_name}")
    if ctx.guild is None:
        return

    # Check bot permissions in the channel
    permissions = ctx.channel.permissions_for(ctx.guild.me)
    if not (permissions.send_messages and permissions.embed_links and permissions.attach_files):
        await ctx.respond(
            "❌ I don't have the required permissions in this channel. Please make sure I have permissions to:\n> • Send Messages\n> • Embed Links\n> • Attach Files", 
            ephemeral=True
        )
        return

    if team_name not in teams_organizer.football_teams:
        await ctx.respond("Invalid team selected. Please try again.")
        return

    await ctx.defer()

    team_league = teams_organizer.find_team_id(team_name)
    fixture_id, fixture_date = teams_organizer.new_find_next_fixture(team_league)

    # Add check for no future fixtures
    if fixture_id is None or fixture_date is None:
        await ctx.respond(f"❌ No upcoming matches found for **{team_name}**.")
        return

    home_team, away_team = get_team_names_from_fixture(fixture_id)

    user_id = ctx.author.id

    task_manager_string = f"{home_team} vs {away_team}"

    if task_manager.new_get_task_count(user_id) < MAX_SIMULTANEOUS_GAMES:
        # Move task addition after successful message send
        thread_opening_embed, team_logos = get_thread_embed(fixture_id, 1)

        await ctx.respond(
            f"✅ **{team_name}** chosen successfully and the task is being processed!"
        )

        channel = ctx.channel 
        channel_id = channel.id

        try:
            initial_message = await channel.send(
                content=None, embed=thread_opening_embed, file=team_logos
            )
            # Only add the task if message was sent successfully
            task_manager.new_add_task(user_id, task_manager_string)
            
            previous_attachments = initial_message.attachments

            # Start the main function as a background task
            task = asyncio.create_task(
                only_stats_main(
                    bot, 
                    initial_message, 
                    fixture_id, 
                    user_id, 
                    task_manager, 
                    previous_attachments, 
                    int(events_id), 
                    channel_id
                )
            )
        except discord.Forbidden:
            await ctx.respond(
                "❌ I couldn't send a message in this channel. Please check my permissions.", 
                ephemeral=True
            )
            return
    else:
        await ctx.respond(
            f"❌ You have reached the maximum number of concurrent tasks ({MAX_SIMULTANEOUS_GAMES}). Please wait for some to end."
        )

#Current games command
@bot.slash_command(
    name="current_games", 
    description="Check how many games you are following!"
)
async def current_games(ctx):
    bot_logger.info(f"Current_games command used by {ctx.author} (ID: {ctx.author.id})")
    if ctx.guild is None:
        return
    
    # Get the user ID and username
    user_id = ctx.author.id
    current_tasks = task_manager.new_get_task_count(user_id)  # Assuming this function needs the user_id
    available_games = MAX_SIMULTANEOUS_GAMES - current_tasks
    
    games_list = task_manager.get_task_games_list(user_id)
   
    games_text = ""
    if not games_list:
        games_text = "> No active games"
    else:
        for game in games_list:
            
            print(game)
            
            game_str = str(game)
            games_text += f"> {game_str}\n"
    

    embed = discord.Embed(
        title=f"Games: {current_tasks}/{MAX_SIMULTANEOUS_GAMES}",
        description=f"**> Available: {available_games}**",
        color=embed_color,
        timestamp=datetime.now(),
    )
    
    embed.add_field(
        name=f"Active games:",
        value=f"{games_text}",
        inline=False,
    )
      
    embed.add_field(
        name=website_field_name,
        value=f"> [{website_name}]({website_url})",
        inline=False,
    )
                
    embed.set_footer(text=footer_text, icon_url=footer_icon_url)
    # Include the user's mention in the response
    await ctx.respond(content = f"{ctx.author.mention}", embed = embed)

#Bot ready event
@bot.event
async def on_ready():
    game = discord.Game("with Football Live Games!")
    await bot.change_presence(status=discord.Status.online, activity=game)
    bot_logger.info(f"{bot.user} is ready and online!")

async def close_bot():
    await bot.close()

async def start_bot():
    try:
        await bot.start(BOT_TOKEN)
    except Exception as e:
        bot_logger.error(f"Bot encountered an error: {e}")
        raise

if __name__ == "__main__":
    # asyncio.run(start_bot())
    bot.run(BOT_TOKEN)
