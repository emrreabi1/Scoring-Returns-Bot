import requests
import logging
import os
import discord
from datetime import datetime
from . import banner_formatter
from configs.config import (
    footer_icon_url, 
    embed_color, 
    website_name,
    website_url,
    website_field_name,
    base_url,
    headers,
    VS_PATH,
    BANNERS_PATH
)

def get_team_names_from_fixture(fixture_id):
    """
    Retrieves the names of the home and away teams for a specific fixture.

    Parameters:
    - fixture_id (int): The unique identifier for the fixture.

    Returns:
    - tuple: (home_team_name, away_team_name)
    """
    try:
        response = requests.get(
            f"{base_url}/fixtures", headers=headers, params={"id": fixture_id}
        )
        response.raise_for_status()
        fixture_data = response.json()

        #print("\n\n", fixture_data)

        home_team_name = fixture_data["response"][0]["teams"]["home"]["name"]
        away_team_name = fixture_data["response"][0]["teams"]["away"]["name"]
        return home_team_name, away_team_name
    except requests.RequestException as e:
        logging.error(f"Failed to fetch team names for fixture ID {fixture_id}: {e}")
        return None, None  # Consider how you want to handle errors in your application


def get_thread_embed(fixture_id, usage_type=0):
    """
    Fetches data for a specific fixture by its ID from the football API.

    Parameters:
    - fixture_id (str): The unique identifier for the fixture.
    -usage_type : 0 for bet type, 1 for normal following

    Returns:
    - tuple: (embed, file)
    """


    params = {"id": fixture_id, 'timezone' : "Europe/London"}
    fixtures_url = base_url + "/fixtures"
    response = requests.get(fixtures_url, headers=headers, params=params)

    specific_fixture = response.json()

    home_team_logo = specific_fixture["response"][0]["teams"]["home"]["logo"]
    away_team_logo = specific_fixture["response"][0]["teams"]["away"]["logo"]
    league_image = specific_fixture["response"][0]["league"]["logo"]

    home_team = str(specific_fixture["response"][0]["teams"]["home"]["name"])
    away_team = str(specific_fixture["response"][0]["teams"]["away"]["name"])

    vs = str(VS_PATH)

    # Replace hardcoded banner path
    file_path = BANNERS_PATH / f"{home_team}vs{away_team}.png"

    # Check if the file already exists
    if not os.path.exists(file_path):
        # The file does not exist, so you can run your code to create the banner
        banner_formatter.combine_images(
            home_team_logo,
            vs,
            away_team_logo,
            file_path,
        )

    file = discord.File(
        str(file_path),  # Convert Path to string for discord.File
        filename="image.png",
    )

    date = str(specific_fixture["response"][0]["fixture"]["date"])
    date_obj = datetime.fromisoformat(date)

    # Reformat the datetime object to the desired format
    nice_date_format = date_obj.strftime("%B %d, %Y, %H:%M")

    if usage_type == 1:
        description=f"**{home_team} vs {away_team}** \n\nGame starting at: {nice_date_format}."
    else:
        description=f"**{home_team} vs {away_team}** \n\nGame starting at: {nice_date_format}.\nJoin this Thread to follow the tips in real time."

    embed = discord.Embed(
        title="⚽ Game Status",
        description=description,
        color=embed_color,
        timestamp=datetime.now(),
    )

    embed.add_field(
        name=website_field_name,
        value=f"> [{website_name}]({website_url})",
        inline=False,
    )

    # Set the image of the embed
    # Load your local image
    # Set the image in the embed to reference the uploaded file by using `attachment://filename`
    embed.set_image(url="attachment://image.png")

    # Set the thumbnail of the embed
    embed.set_thumbnail(url=league_image)

    # Set the footer of the embed
    embed.set_footer(text="Scoring Returns", icon_url=footer_icon_url)  # •

    return embed, file
