import discord
from discord.ui import Button, View
from discord import ButtonStyle
from datetime import datetime, timedelta
import asyncio
from configs.config import footer_text, footer_icon_url, embed_color, website_field_name, website_name, website_url

class CombinedView(discord.ui.View):

    def __init__(self, task, author_id, json_stats_path, task_manager, all_stats_dict):
        super().__init__(timeout=None)
        self.task = task
        self.author_id = author_id
        self.json_stats_path = json_stats_path

        self.fixture_json = 0
        
        self.all_stats_dict = all_stats_dict


        self.last_clicks_full_stats = {}
        self.last_clicks_15_analysis = {}

        self.task_manager = task_manager

    def update_dict(self, updated_minutes_15_dict):
        self.minute15_analysis = updated_minutes_15_dict

    def update_stats(self, updated_fixture_json):
        self.fixture_json = updated_fixture_json

    def update_all_stats_dict(self, updated_all_stats_dict):
        all_stats_dict = updated_all_stats_dict

    # Button to stop the task
    @discord.ui.button(label="Stop the Game!", style=discord.ButtonStyle.red)
    async def end_task_button(self, button, interaction):
        
        """
        Handles the "Stop Game" button interaction. Cancels the running task and updates game status.

        Parameters:
        - button: The button instance that triggered the interaction
        - interaction: The Discord interaction object

        Returns:
        - None. Sends response message to Discord.
        """
        
        if interaction.user.id != self.author_id:
            # Optionally, respond to the user letting them know they can't interact with this menu
            await interaction.response.send_message(
                "You are not authorized to use this button.", ephemeral=True
            )
            return

        # When button is pressed, cancel the task
        self.task.cancel()
        
        '''Use Data To retrieve Game Status'''
        game_status = self.fixture_json["response"][0]["fixture"]["status"]["short"]
        
        home_team = str(self.fixture_json["response"][0]["teams"]["home"]["name"])
        away_team = str(self.fixture_json["response"][0]["teams"]["away"]["name"])
        
        game_name = f"{home_team} vs {away_team}"
        
        if game_status != "FT":
            #Subtract from the counter
            self.task_manager.new_remove_task(self.author_id, game_name)

        # You can also send a confirmation message or update the current one

        await interaction.response.edit_message(
            content="Deactivated the game.", view=None
        )

    # Define the button, setting the style to blue 
    @discord.ui.button(label="Show Full Stats", style=discord.ButtonStyle.primary)
    async def show_full_stats(self, button, interaction):

        """
        Handles the "Show Full Stats" button interaction. Displays complete match statistics.
        Implements a 60-second cooldown per user.

        Parameters:
        - button: The button instance that triggered the interaction
        - interaction: The Discord interaction object

        Returns:
        - None. Sends embedded statistics message to Discord.
        """

        user_id = interaction.user.id
        now = datetime.now()

        # Check if the user has clicked the button in the last 60 seconds
        if user_id in self.last_clicks_full_stats:
            last_click = self.last_clicks_full_stats[user_id]
            cooldown_period = timedelta(seconds=60)
            if now - last_click < cooldown_period:
                remaining_time = (last_click + cooldown_period - now).total_seconds()

                embed1 = discord.Embed(
                    title="⌛ Time Out",
                    description=f"Please wait {int(remaining_time)} more seconds before clicking again.",
                    color=16776960,
                    timestamp=datetime.now(),
                )
                embed1.set_footer(text=footer_text, icon_url=footer_icon_url)

                await interaction.response.send_message(content = None, embed = embed1, view=None, ephemeral=True)
                return

        # Update the last click time for the user
        self.last_clicks_full_stats[user_id] = now


        '''Adionar Cooldown de 60 segundos ao user para poder clicar no botão denovo'''    

        '''Ler Dados Do Json do jogo em questão, Construtor precisa do nome do ficheiro como argumento de entrada'''
        
        specific_fixture = self.fixture_json

        '''Use Data To retrieve Full Data'''
        time_elapsed = specific_fixture["response"][0]["fixture"]["status"]["elapsed"]

        
        game_status = str(specific_fixture["response"][0]["fixture"]["status"]["short"])
        league_image = specific_fixture["response"][0]["league"]["logo"]

        if time_elapsed is None:
            embed1 = discord.Embed(
                title="Full Game Stats ⚠️",
                description=f"Game didn't start yet. No stats available",
                color=5763719,
                timestamp=datetime.now(),  # Fixed datetime call
            )

            embed1.set_thumbnail(url=league_image)
            embed1.set_footer(text="Scoring Returns", icon_url=footer_icon_url) 

            await interaction.response.send_message(
                #Send Full Stats here
                content=None, embed = embed1,view=None, ephemeral=True
            )
            return
        
        time_elapsed = int(time_elapsed)

        home_team = str(specific_fixture["response"][0]["teams"]["home"]["name"])
        away_team = str(specific_fixture["response"][0]["teams"]["away"]["name"])

        home_team_stats = {}
        away_team_stats = {}
        full_stats_string = ""

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

        for key in home_team_stats.keys():
            # Use the key to get values from both dictionaries
            home_value = home_team_stats.get(key) or 0
            away_value = away_team_stats.get(key) or 0
            
            #home_value = home_team_stats.get(key) or "NA"
            #away_value = away_team_stats.get(key) or "NA"

            full_stats_string += f"> **{key}** : {home_value} - {away_value}\n"

        embed1 = discord.Embed(
            title="⚽ Full Game Stats",
            description=f"**{home_team} vs {away_team}**\n> **Time Elapsed:** {time_elapsed} minutes\n> **Game Status:** {game_status}",
            color=embed_color,
            timestamp=datetime.now(),
        )
        
        if full_stats_string == "":
            full_stats_string = "> No Statistics Available"

        embed1.add_field(name="**Game Stats**",
                        value=full_stats_string,
                        inline=False)

        embed1.add_field(
            name=website_field_name,
            value=f"> [{website_name}]({website_url})",
            inline=False,
        )

        embed1.set_thumbnail(url=league_image)
        embed1.set_footer(text=footer_text, icon_url=footer_icon_url)

        await interaction.response.send_message(
            #Send Full Stats here
            content=None, embed = embed1,view=None, ephemeral=True
        ) 

