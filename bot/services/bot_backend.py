import sys
import requests
import json
import pandas as pd
import emoji
from datetime import datetime
import asyncio
import discord
import logging

from views.button import CombinedView
from common_utils.fixture_utils import get_team_names_from_fixture
from common_utils.time_logging import configure_logging, calculate_time_remaining

from configs.config import (
    base_url,
    headers,
    footer_icon_url,
    thumbnail_logo, 
    embed_color,
    footer_text,
    website_name,
    website_url,
    website_field_name,
    LIVE_JSON_PATH,
    BANNERS_PATH,
    LOOP_WAIT_TIME
)
async def get_fixtures_statistics(fixture_id):
    """
    Retrieves fixture statistics from the API for a specific match.
    
    Parameters:
    - fixture_id (int): The unique identifier for the fixture
    
    Returns:
    - list: Contains:
        [0] int: 0 if game not started, 1 if in progress 
        [1] dict: Match statistics and data
        [2] file: Discord file object or 0
        [3] embed: Discord embed object or file
        [4] dict: Raw fixture API response
    """

    params = {"id": fixture_id, 'timezone' : "Europe/London"}
    fixtures_url = base_url + "/fixtures"
    response = requests.get(fixtures_url, headers=headers, params=params)

    specific_fixture = response.json()

    for item in specific_fixture["response"]:
        del item["lineups"]
        del item["players"]

    home_team = str(specific_fixture["response"][0]["teams"]["home"]["name"])
    away_team = str(specific_fixture["response"][0]["teams"]["away"]["name"])

    with open(
        f"{LIVE_JSON_PATH}/{home_team}vs{away_team}.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(specific_fixture, f, ensure_ascii=False, indent=4)

    data_dict = {}

    time_elapsed = specific_fixture["response"][0]["fixture"]["status"]["elapsed"]

    file = 0

    # Checking if the elapsed time is not None. If the game is yet to start it is None
    if time_elapsed is not None:
        time_elapsed = int(time_elapsed)
    else:

        home_team = str(specific_fixture["response"][0]["teams"]["home"]["name"])
        away_team = str(specific_fixture["response"][0]["teams"]["away"]["name"])


        date = str(specific_fixture["response"][0]["fixture"]["date"])

        date_obj = datetime.fromisoformat(date)

        # Reformat the datetime object to the desired format
        nice_date_format = date_obj.strftime("%B %d, %Y, %H:%M")
             
        league_image = specific_fixture["response"][0]["league"]["logo"]

        # Create an instance of the Embed class

        embed = discord.Embed(
            title="⚽ Game Status",
            description=f"**{home_team} vs {away_team}** \n\nGame starting at: {nice_date_format}.",
            color=embed_color,
            timestamp=datetime.now(),
        )
        
        embed.add_field(
            name=website_field_name,
            value=f"> [{website_name}]({website_url})",
            inline=False,
        )

        # Set the thumbnail of the embed
        embed.set_thumbnail(url=league_image)

        # Set the footer of the embed
        embed.set_footer(text=footer_text, icon_url=footer_icon_url)  # •
        
        """Also Return the embed containing the bets"""
        # Copy of the data dict used in the call made to the function during the game. Here we can assume the values as 0 cause the game didnt start.
        fake_data_dict = {
            "Time Elapsed": 0,
            "Game Status": "1H",  # used 1H to overpass the checks in the bets checker This way, the one of the half bets related will always be yellow
            "Home Team": home_team,
            "Away Team": away_team,
            "First to Score": 0,
            "Home Ball Possession" : 0,
            "Away Ball Possession" : 0,
            home_team + " Goals": 0,
            away_team + " Goals": 0,
            home_team + " Halftime Goals": 0,
            away_team + " Halftime Goals": 0,
            home_team + " Shots on Goal": 0,
            away_team + " Shots on Goal": 0,
            home_team + " Corner Kicks": 0,
            away_team + " Corner Kicks": 0,
        }
        
        return [0, fake_data_dict, file, embed, specific_fixture]

    game_status = str(specific_fixture["response"][0]["fixture"]["status"]["short"])
    home_team = str(specific_fixture["response"][0]["teams"]["home"]["name"])
    away_team = str(specific_fixture["response"][0]["teams"]["away"]["name"])

    home_goals = int(specific_fixture["response"][0]["goals"]["home"])
    away_goals = int(specific_fixture["response"][0]["goals"]["away"])

    home_halftime = int(specific_fixture["response"][0]["score"]["halftime"]["home"])
    away_halftime = int(specific_fixture["response"][0]["score"]["halftime"]["away"])

    home_team_stats = {}
    away_team_stats = {}

    # Loop through the response to extract statistics for both teams
    for team_stats in specific_fixture["response"][0]["statistics"]:
        team_name = team_stats["team"]["name"]
        statistics = team_stats["statistics"]

        # Initialize variables for each statistic type
        for stat in statistics:
            stat_type = stat["type"]
            stat_value = stat["value"]

            # Store statistics in the respective team"s dictionary
            if team_name == home_team:
                home_team_stats[stat_type] = stat_value
            elif team_name == away_team:
                away_team_stats[stat_type] = stat_value

    # Loop through the response to extract events goals related

    '''There are games that do not have events!!'''

    if not specific_fixture["response"][0]["events"]:  # if list is empty. No events
        first_scorer = "none"
    else:  # if list is not empty. There is events
        for event in specific_fixture["response"][0]["events"]:
            if event["type"] == "Goal" and event["detail"] != "Missed Penalty":
                # If the goal is valid
                first_scorer = str(event["team"]["name"])
                break
            else:
                first_scorer = "none"

    # Now you can access the statistics for the home and away teams
    home_shots_on_goal = int(home_team_stats.get("Shots on Goal", 0)) if home_team_stats.get("Shots on Goal") is not None else 0
    away_shots_on_goal = int(away_team_stats.get("Shots on Goal", 0)) if away_team_stats.get("Shots on Goal") is not None else 0

    home_corner_kicks = int(home_team_stats.get("Corner Kicks", 0)) if home_team_stats.get("Corner Kicks") is not None else 0
    away_corner_kicks = int(away_team_stats.get("Corner Kicks", 0)) if away_team_stats.get("Corner Kicks") is not None else 0

    temp_home_poss = (home_team_stats.get("Ball Possession", "0%")) 
    temp_away_poss = (away_team_stats.get("Ball Possession", "0%")) 

    home_ball_possession = int(temp_home_poss.strip('%')) if temp_home_poss is not None else 0
    away_ball_possession = int(temp_away_poss.strip('%')) if temp_away_poss is not None else 0


    data_dict = {
        "Time Elapsed": time_elapsed,
        "Game Status": game_status,
        "Home Team": home_team,
        "Away Team": away_team,
        "First to Score": first_scorer,
        "Home Ball Possession" : home_ball_possession,
        "Away Ball Possession" : away_ball_possession,
        home_team + " Goals": home_goals,
        away_team + " Goals": away_goals,
        home_team + " Halftime Goals": home_halftime,
        away_team + " Halftime Goals": away_halftime,
        home_team + " Shots on Goal": home_shots_on_goal,
        away_team + " Shots on Goal": away_shots_on_goal,
        home_team + " Corner Kicks": home_corner_kicks,
        away_team + " Corner Kicks": away_corner_kicks,
    }


    return [1, data_dict, 0, file, specific_fixture]

async def information_presenter(live_stats_dict, bot, previous_size, specific_fixture, task_manager, author_id, announcment_id, logger):
    """
    Creates and updates Discord embeds with match information and events.
    
    Parameters:
    - live_stats_dict (dict): Current match statistics
    - bot (discord.Client): Bot instance
    - previous_size (int): Previous number of events
    - specific_fixture (dict): Raw fixture data
    - task_manager (TaskManager): Task management instance
    - author_id (int): Discord user ID who initiated
    - announcment_id (int): Channel ID for announcements
    - logger (logging.Logger): Logger instance
    
    Returns:
    - tuple: (discord.Embed, int) Contains updated embed and new event count
    """

    # Game Status Section
    home_team = live_stats_dict["Home Team"]
    away_team = live_stats_dict["Away Team"]

    league_image = specific_fixture["response"][0]["league"]["logo"]


    team_stats = {
        home_team + " Goals": 0,
        away_team + " Goals": 0,
        home_team + " Halftime Goals": 0,
        away_team + " Halftime Goals": 0,
        home_team + " Shots on Goal": 0,
        away_team + " Shots on Goal": 0,
        home_team + " Corner Kicks": 0,
        away_team + " Corner Kicks": 0,
        "Home Ball Possession" : live_stats_dict["Home Ball Possession"],
        "Away Ball Possession" : live_stats_dict["Away Ball Possession"]
    }

    for key, value in live_stats_dict.items():
        if home_team in key or away_team in key:
            team_stats[key] = value
            

    events = specific_fixture["response"][0]["events"]

    current_size = 0
    
    current_size = len(events) if events else previous_size
            
    if current_size > previous_size:
        # There are new events, process them.
        new_events = events[previous_size:]  # Get only the new events.
        
        for event in new_events:
            # Check if the event type is 'Goal' or 'Var'
            
            if (event['type'].lower() in ('goal', 'var')) or (event['type'].lower() in ('card') and event['detail'].lower() in ('red card')):
                

                bet_hit_channel = bot.get_channel(announcment_id)


                if event['type'] == "Card" and event['detail'] == "Red Card":
                    custom_title = f"**🟥 {event['team']['name']} Red Card! 🟥**"


                # Define the embed title and color
                if event['type'] == "Var":
                    custom_title = f"**📢 Var Decision! 📢**"      
                           
                if event['type'] == "Goal":
                    custom_title = f"**⚽ {event['team']['name']} {event['type']}! ⚽**"

                if event['detail'] == "Missed Penalty":
                    custom_title = f"**⭕ Missed Penalty! ⭕**"
                
                
                if event['comments'] == "Penalty Shootout":
                    
                    if event['detail'] == "Missed Penalty":
  
                        custom_title = f"**⭕ Missed Penalty! ⭕**"
                        
                    elif event['detail'] == "Penalty":

                        custom_title = f"**⚽ Goal Penalty! ⚽**"


                                
                event_embed = discord.Embed(
                    title=custom_title,
                    color=embed_color,
                    timestamp=datetime.now(),
                )

                player_name = event['player']['name'] if event['player']['name'] is not None else "Unknown"
                time_elapsed = event['time']['elapsed']

                if event['time']['extra'] == None:
                    value_embed=f"> **Time Elapsed:** {time_elapsed} minutes\n> **Game Status:** {live_stats_dict.get('Game Status')}\n> **Details:** {event['detail']}\n> **Player:** {player_name}"
                else:
                    value_embed=f"> **Time Elapsed:** {time_elapsed} minutes\n> **Extra:** {event['time']['extra']}\n> **Game Status:** {live_stats_dict.get('Game Status')}\n> **Details:** {event['detail']}\n> **Player:** {player_name}"

                
                if event['type'] == "Card" and event['detail'] == "Red Card" and event['time']['extra'] == None:
                    value_embed=f"> **Time Elapsed:** {time_elapsed} minutes\n> **Game Status:** {live_stats_dict.get('Game Status')}\n> **Details:** {event['comments']}\n> **Player:** {player_name}"
                elif event['type'] == "Card" and event['detail'] == "Red Card" and event['time']['extra'] != None:
                    value_embed=f"> **Time Elapsed:** {time_elapsed} minutes\n> **Extra:** {event['time']['extra']}\n> **Game Status:** {live_stats_dict.get('Game Status')}\n> **Details:** {event['comments']}\n> **Player:** {player_name}"


                if event['type'] == "Goal" and event['time']['extra'] == None:
                    value_embed=f"> **Result:** {team_stats.get(f'{home_team} Goals')} - {team_stats.get(f'{away_team} Goals')}\n> **Time Elapsed:** {time_elapsed} minutes\n> **Game Status:** {live_stats_dict.get('Game Status')}\n> **Player:** {player_name}"
                elif event['type'] == "Goal" and event['time']['extra'] != None:
                    value_embed=f"> **Result:** {team_stats.get(f'{home_team} Goals')} - {team_stats.get(f'{away_team} Goals')}\n> **Time Elapsed:** {time_elapsed} minutes\n> **Extra:** {event['time']['extra']}\n> **Game Status:** {live_stats_dict.get('Game Status')}\n> **Player:** {player_name}"


                if event['type'] == "Var" and event['time']['extra'] == None:
                    value_embed=f"> **Result:** {team_stats.get(f'{home_team} Goals')} - {team_stats.get(f'{away_team} Goals')}\n> **Time Elapsed:** {time_elapsed} minutes\n> **Game Status:** {live_stats_dict.get('Game Status')}\n> **Details:** {event['detail']}\n> **Player:** {player_name}"
                elif event['type'] == "Var" and event['time']['extra'] != None:
                    value_embed=f"> **Result:** {team_stats.get(f'{home_team} Goals')} - {team_stats.get(f'{away_team} Goals')}\n> **Time Elapsed:** {time_elapsed} minutes\n> **Extra:** {event['time']['extra']}\n> **Game Status:** {live_stats_dict.get('Game Status')}\n> **Details:** {event['detail']}\n> **Player:** {player_name}"

                '''Add de Penalty json part here'''
                if event['comments'] == "Penalty Shootout":
                    
                    home_penalty = 0 if specific_fixture["response"][0]["score"]["penalty"]["home"] is None else specific_fixture["response"][0]["score"]["penalty"]["home"]
                    away_penalty = 0 if specific_fixture["response"][0]["score"]["penalty"]["away"] is None else specific_fixture["response"][0]["score"]["penalty"]["away"]

                    value_embed=f"> **Penalty:** {home_penalty} - {away_penalty}\n> **Time Elapsed:** {time_elapsed} minutes\n> **Game Status:** {live_stats_dict.get('Game Status')}\n> **Details:** {event['detail']}\n> **Player:** {player_name}"
                
                # Add the game information
                event_embed.add_field(
                    name=f"**{home_team} vs {away_team}**\n",
                    value = value_embed,
                    inline=False,
                )
                
                event_embed.add_field(
                    name=website_field_name,
                    value=f"> [{website_name}]({website_url})",
                    inline=False,
                )

                '''Add related team logo to these kind of messages'''
                team_logo = event['team']['logo']

                event_embed.set_thumbnail(url=team_logo)
                
                event_embed.set_footer(
                    text=footer_text, icon_url=footer_icon_url 
                )


                if bet_hit_channel is None:
                    logger.warning(f"Channel {announcment_id} not found")
                    continue

                try:
                    await bet_hit_channel.send(content=None, embed=event_embed)
                except discord.Forbidden:
                    logger.warning(f"Missing permissions to send messages in channel {announcment_id}")
                except discord.HTTPException as e:
                    logger.error(f"Failed to send event message: {e}")

    # Create the first embed
    embed1 = discord.Embed(
        title="⚽ Game Status",
        description=f"**{home_team} vs {away_team}**\n> **Time Elapsed:** {live_stats_dict.get('Time Elapsed')} minutes\n> **Game Status:** {live_stats_dict.get('Game Status')}",
        color=embed_color,
        timestamp=datetime.now(),
    )
    
    embed1.add_field(name="**Team Stats**",
                    value = (
                        f"> **Result:** {team_stats.get(f'{home_team} Goals')} - "
                        f"{team_stats.get(f'{away_team} Goals')} \n"
                        f"> **Halftime Goals:** {team_stats.get(f'{home_team} Halftime Goals')} - "
                        f"{team_stats.get(f'{away_team} Halftime Goals')} \n"
                        f"> **Corner Kicks:** {team_stats.get(f'{home_team} Corner Kicks')} - "
                        f"{team_stats.get(f'{away_team} Corner Kicks')} \n"
                        f"> **Shots on Goal:** {team_stats.get(f'{home_team} Shots on Goal')} - "
                        f"{team_stats.get(f'{away_team} Shots on Goal')} \n"
                        f"> **Ball Possession:** {team_stats.get('Home Ball Possession')}% - "
                        f"{team_stats.get('Away Ball Possession')}%"
                    ),
                    inline=False)
    
    embed1.add_field(
        name=website_field_name,
        value=f"> [{website_name}]({website_url})",
        inline=False,
    )

    embed1.set_thumbnail(url=league_image)
    embed1.set_footer(text=footer_text, icon_url=footer_icon_url)  # •
     
    file = discord.File(
        f"{BANNERS_PATH}/{home_team}vs{away_team}.png",
        filename="image.png",
    )
    # Set the image in the embed to reference the uploaded file by using `attachment://filename`
    embed1.set_image(url="attachment://image.png")
    
    return embed1, current_size

async def game_status_func(bot, specific_fixture, live_stats_dict, announcment_id, game_moment, logger):
    """
    Sends game status announcements to specified channel.
    
    Parameters:
    - bot (discord.Client): Bot instance
    - specific_fixture (dict): Raw fixture data
    - live_stats_dict (dict): Current match statistics
    - announcment_id (int): Channel ID for announcements
    - game_moment (str): Current game state (e.g. "Game Started", "Halftime")
    - logger (logging.Logger): Logger instance
    """

    # Game Status Section
    home_team = live_stats_dict["Home Team"]
    away_team = live_stats_dict["Away Team"]
   
    team_stats = {
        home_team + " Goals": 0,
        away_team + " Goals": 0,
        home_team + " Halftime Goals": 0,
        away_team + " Halftime Goals": 0,
        home_team + " Shots on Goal": 0,
        away_team + " Shots on Goal": 0,
        home_team + " Corner Kicks": 0,
        away_team + " Corner Kicks": 0,
        "Home Ball Possession" : live_stats_dict["Home Ball Possession"],
        "Away Ball Possession" : live_stats_dict["Away Ball Possession"]
    }

    for key, value in live_stats_dict.items():
        if home_team in key or away_team in key:
            team_stats[key] = value
   
    try:
        announcements_channel = bot.get_channel(announcment_id)
        if announcements_channel is None:
            logger.warning(f"Channel {announcment_id} not found")
            return

        title_embed = ""

        if game_moment == "Game Started":
            title_embed = "🎉 Game Started 🎉"
        
        elif game_moment == "Halftime Reached":
            title_embed = "⏳ Halftime Reached ⏳"
        
        elif game_moment == "Second Half Started":
            title_embed = "🎉 Second Half Started 🎉"
        
        elif game_moment == "Game Ended":
            title_embed = "🏁 Game Ended 🏁"
        
        elif game_moment == "Break Time Reached":
            title_embed = "⏳ Break Time Reached ⏳"
        
        elif game_moment == "Extra Time Started":
            title_embed = "🎉 Second Half Started 🎉"

        elif game_moment == "Penalty Started":
            title_embed = "🎉 Penalty Started 🎉"

        game_status = discord.Embed(
            title=title_embed,
            color=embed_color,
            timestamp=datetime.now(),
        )

        # Add the game information
        game_status.add_field(
            name=f"**{home_team} vs {away_team}**\n",
            value = f"> **Result:** {team_stats.get(f'{home_team} Goals')} - {team_stats.get(f'{away_team} Goals')}",
            inline=False,
        )
        
        league_image = specific_fixture["response"][0]["league"]["logo"]

        
        game_status.set_thumbnail(url=league_image)
        game_status.set_footer(
            text=footer_text, icon_url=footer_icon_url 
        )

        file = discord.File(
            f"{BANNERS_PATH}/{home_team}vs{away_team}.png",
            filename="image.png",
        )
        # Set the image in the embed to reference the uploaded file by using `attachment://filename`
        game_status.set_image(url="attachment://image.png")

        await announcements_channel.send(content=None, embed=game_status, file=file)
        
    except discord.Forbidden:
        logger.warning(f"Missing permissions to send messages in channel {announcment_id}")
    except discord.HTTPException as e:
        logger.error(f"Failed to send game status message: {e}")
    except Exception as e:
        logger.error(f"Unexpected error sending game status: {e}")

async def only_stats_main(bot, initial_message, fixture_id, author_id, task_manager, previous_attachments, announcment_id, channel_id):
    """
    Main function to monitor and update match statistics.
    
    Parameters:
    - bot (discord.Client): Bot instance
    - initial_message (discord.Message): Original command message
    - fixture_id (int): Match identifier
    - author_id (int): Discord user ID who initiated
    - task_manager (TaskManager): Task management instance
    - previous_attachments (list): Previous message attachments
    - announcment_id (int): Channel ID for announcements
    - channel_id (int): Channel ID where command was used
    """

    if announcment_id == 0:
        announcment_id = channel_id
            

    '''CHANGE THIS TO BE BASED ON THE HOME TEAM AND AWAY TEAM AND NOT THE XLSX FILE NAME'''
    home_team, away_team = get_team_names_from_fixture(
        fixture_id
    ) 
    
    logger_name = home_team + away_team
    
    logger = configure_logging(logger_name, author_id)

    live_stats_dict = await get_fixtures_statistics(
        fixture_id
    )
    specific_fixture = live_stats_dict[4]
     
    data_dict = live_stats_dict[1]
    
    home_team = data_dict["Home Team"]
    away_team = data_dict["Away Team"]
    
    all_stats_dict = {}
   
    task = asyncio.current_task()
    all_buttons = CombinedView(task, author_id, task_manager, all_stats_dict)
        
    all_buttons.update_stats(specific_fixture)

    logger.info("Game monitoring started message sent.")
    previous_size = 0
    
    task_manager_string = f"{home_team} vs {away_team}"
    
    while True:

        live_stats_dict = await get_fixtures_statistics(fixture_id)  

        specific_fixture = live_stats_dict[4]
        all_buttons.update_stats(specific_fixture)
        
        # Game Not started halt

        if 0 == live_stats_dict[0]:


            embed_before_game = live_stats_dict[3]
            
            embed_before_game.set_image(url="attachment://image.png")  # Use the same attachment filename
            file = live_stats_dict[2]

            retry_count = 0
            max_retries = 3
                      
            while retry_count < max_retries:
                try:
                    await initial_message.edit(
                        content=None,
                        embed=embed_before_game,
                        view=all_buttons,
                    )
                    logger.debug("Initial message edited for game not started.")
                    break  # Break out of the loop if successful
                except discord.NotFound as e:
                    logger.info(f"An error occurred: {e}. Exiting the function.")
                    task_manager.new_remove_task(author_id, task_manager_string)
                    return  # Exiting due to NotFound or Forbidden
                except discord.Forbidden as e:
                    logger.info(f"An error occurred: {e}. Exiting the function.")
                    task_manager.new_remove_task(author_id, task_manager_string)
                    return  # Exiting due to NotFound or Forbidden
                except discord.HTTPException as e:
                    logger.info(f"HTTPException occurred: {e}. Retrying...")
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.info("Maximum retries reached. Exiting the function.")
                        task_manager.new_remove_task(author_id, task_manager_string)
                        return  # Exiting after max retries
            
            logger.info("Initial message edited for game not started.")

            # Instead of sleeping for 5 minutes straight, check more frequently
            not_started_wait_time = 54000  # 15 hours of total wait time
            check_interval_long = 3600  # Interval to re-check the game status when it's more than 1 hour until game start
            check_interval_short = LOOP_WAIT_TIME  # Changed from 45
            
            elapsed_time = 0
            starting_date_str = specific_fixture["response"][0]["fixture"]["date"]
            starting_date = datetime.strptime(starting_date_str, "%Y-%m-%dT%H:%M:%S%z")

            while elapsed_time < not_started_wait_time:

                """Logging Purposes"""
                now = datetime.now(starting_date.tzinfo)
                time_until_game = starting_date - now
                if time_until_game.total_seconds() > 36000:
                    sleep_interval = check_interval_long * 10
                elif time_until_game.total_seconds() > 18000:
                    sleep_interval = 18000             
                elif time_until_game.total_seconds() > 3600:
                    sleep_interval = check_interval_long
                elif time_until_game.total_seconds() > 1800:
                    sleep_interval = 1800    
                elif time_until_game.total_seconds() > 600:
                    sleep_interval = 600
                elif time_until_game.total_seconds() > 300:
                    sleep_interval = 300
                else:
                    sleep_interval = check_interval_short
                

                # dd/mm/YY H:M:S
                dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
                logger.debug(f"Game Not Started.{live_stats_dict[0]} Last check at: {dt_string}")
                logger.info(f"Game Not Started.{live_stats_dict[0]}\nWaiting: {sleep_interval} seconds.")

                """-------"""
                await asyncio.sleep(sleep_interval)
                
                elapsed_time += sleep_interval
                
                # Re-fetch the game status to see if it has changed
                
                live_stats_dict = await get_fixtures_statistics(
                    fixture_id
                )
                
                specific_fixture = live_stats_dict[4]
                all_buttons.update_stats(specific_fixture)


                while retry_count < max_retries:
                    try:
                        await initial_message.edit(
                            content=None,
                            embed=embed_before_game,
                            view=all_buttons,
                        )
                        logger.debug("Initial message edited for game not started.")
                        break  # Break out of the loop if successful
                    except discord.NotFound as e:
                        logger.info(f"An error occurred: {e}. Exiting the function.")
                        task_manager.new_remove_task(author_id, task_manager_string)
                        return  # Exiting due to NotFound or Forbidden
                    except discord.Forbidden as e:
                        logger.info(f"An error occurred: {e}. Exiting the function.")
                        task_manager.new_remove_task(author_id, task_manager_string)
                        return  # Exiting due to NotFound or Forbidden
                    except discord.HTTPException as e:
                        logger.info(f"HTTPException occurred: {e}. Retrying...")
                        retry_count += 1
                        if retry_count >= max_retries:
                            logger.info("Maximum retries reached. Exiting the function.")
                            task_manager.new_remove_task(author_id, task_manager_string)
                            return  # Exiting after max retries


                logger.debug(f"Current game status: {live_stats_dict[0]}")
                if 1 == live_stats_dict[0]:
                    
                    '''Send 1H Start Here!'''
                    await game_status_func(bot, specific_fixture, live_stats_dict[1],announcment_id, "Game Started", logger)
                    
                    
                    break  # Exit the loop if game status is no longer "Game Not Started!"
            # Check if we exited the loop because the wait time was exhausted
            
            if elapsed_time >= not_started_wait_time:
                # Log the timeout or perform any necessary cleanup
                logger.info("The game did not start within the expected time window. Exiting the function.")
                task_manager.new_remove_task(author_id, task_manager_string)
                
                # Exiting the functiong
                return

        embed1, previous_size = await information_presenter(
            live_stats_dict[1], bot, previous_size, specific_fixture, task_manager, author_id, announcment_id, logger
        )
        
        # Game Halftime Halt
        if live_stats_dict[1].get("Game Status") in ("HT", "BT"):
            
            '''Send HalfTime Reached here!'''
            
            
            if live_stats_dict[1].get("Game Status") == "HT":
                await game_status_func(bot, specific_fixture, live_stats_dict[1],announcment_id, "Halftime Reached", logger)
            elif live_stats_dict[1].get("Game Status") == "BT":
                await game_status_func(bot, specific_fixture, live_stats_dict[1],announcment_id, "Break Time Reached", logger)
            
            
            retry_count = 0
            max_retries = 3
                        
            while retry_count < max_retries:
                try:
                    await initial_message.edit(
                        content=None,
                        embed=embed1,
                        view=all_buttons,
                    )
                    logger.debug("Initial message edited for game not started.")
                    break  # Break out of the loop if successful
                except discord.NotFound as e:
                    logger.info(f"An error occurred: {e}. Exiting the function.")
                    task_manager.new_remove_task(author_id, task_manager_string)
                    return  # Exiting due to NotFound or Forbidden
                except discord.Forbidden as e:
                    logger.info(f"An error occurred: {e}. Exiting the function.")
                    task_manager.new_remove_task(author_id, task_manager_string)
                    return  # Exiting due to NotFound or Forbidden
                except discord.HTTPException as e:
                    logger.info(f"HTTPException occurred: {e}. Retrying...")
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.info("Maximum retries reached. Exiting the function.")
                        task_manager.new_remove_task(author_id, task_manager_string)
                        return  # Exiting after max retries
                
            logger.info(
                f"Half Time Reached Last check at: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
            )

            # Shorten the sleep duration and re-check the game status more frequently
            halftime_wait_time = 1800  # 30 minutes total maximum wait
            elapsed_time = 0

            while elapsed_time < halftime_wait_time:
                await asyncio.sleep(LOOP_WAIT_TIME)   # Use configurable wait time
                elapsed_time += LOOP_WAIT_TIME
                
                # Re-fetch the game status
                live_stats_dict = await get_fixtures_statistics(fixture_id)
                specific_fixture = live_stats_dict[4]
                all_buttons.update_stats(specific_fixture)

                if live_stats_dict[1].get("Game Status") != "HT" and live_stats_dict[1].get("Game Status") != "BT":
                    
                    '''Send 2H Start Here!'''
                    if live_stats_dict[1].get("Game Status") == "2H":    
                        await game_status_func(bot, specific_fixture, live_stats_dict[1],announcment_id, "Second Half Started", logger)
                    elif live_stats_dict[1].get("Game Status") == "ET":
                        await game_status_func(bot, specific_fixture, live_stats_dict[1],announcment_id, "Extra Time Started", logger)
                    elif live_stats_dict[1].get("Game Status") == "P":
                        await game_status_func(bot, specific_fixture, live_stats_dict[1],announcment_id, "Penalty Started", logger)
                    
                    break  # Exit the loop if game status is no longer "HT"

        elif live_stats_dict[1].get("Game Status") in ("FT", "AET", "PEN", "ABD"):
            
            retry_count = 0
            max_retries = 3
                      
            while retry_count < max_retries:
                try:
                    await initial_message.edit(
                        content=None,
                        embed=embed1,
                        view=all_buttons,
                    )
                    logger.debug("Initial message edited for game not started.")
                    break  # Break out of the loop if successful
                except discord.NotFound as e:
                    logger.info(f"An error occurred: {e}. Exiting the function.")
                    task_manager.new_remove_task(author_id, task_manager_string)
                    return  # Exiting due to NotFound or Forbidden
                except discord.Forbidden as e:
                    logger.info(f"An error occurred: {e}. Exiting the function.")
                    task_manager.new_remove_task(author_id, task_manager_string)
                    return  # Exiting due to NotFound or Forbidden
                except discord.HTTPException as e:
                    logger.info(f"HTTPException occurred: {e}. Retrying...")
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.info("Maximum retries reached. Exiting the function.")
                        task_manager.new_remove_task(author_id, task_manager_string)
                        return  # Exiting after max retries
            
            
            '''Send Final  Game here!'''
            await game_status_func(bot, specific_fixture, live_stats_dict[1],announcment_id, "Game Ended", logger)
            
            logger.info(
                f"Game Ended Last check at: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
            )
            task_manager.new_remove_task(author_id, task_manager_string)
            return

        else:
            
            retry_count = 0
            max_retries = 3
                      
            while retry_count < max_retries:
                try:
                    await initial_message.edit(
                        content=None,
                        embed=embed1,
                        view=all_buttons,
                    )
                    logger.debug("Initial message edited for game not started.")
                    break  # Break out of the loop if successful
                except discord.NotFound as e:
                    logger.info(f"An error occurred: {e}. Exiting the function.")
                    task_manager.new_remove_task(author_id, task_manager_string)
                    return  # Exiting due to NotFound or Forbidden
                except discord.Forbidden as e:
                    logger.info(f"An error occurred: {e}. Exiting the function.")
                    task_manager.new_remove_task(author_id, task_manager_string)
                    return  # Exiting due to NotFound or Forbidden
                except discord.HTTPException as e:
                    logger.info(f"HTTPException occurred: {e}. Retrying...")
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.info("Maximum retries reached. Exiting the function.")
                        task_manager.new_remove_task(author_id, task_manager_string)
                        return  # Exiting after max retries
            
            logger.info(
                f"Game in Progress: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
            )

        await asyncio.sleep(LOOP_WAIT_TIME)  # Changed from 45

