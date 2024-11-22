import json
from datetime import datetime, timezone, timedelta
import os
from configs.config import FIXTURES_PATH, STANDINGS_PATH, FIXTURES_BY_LEAGUE_PATH, INFORMATION_PATH, TEAMS_PATH
from common_utils.time_logging import configure_logging

class TeamsOrganizer:
    def __init__(self):
        """
        Initializes TeamsOrganizer with empty dictionaries for leagues, teams, and fixtures.
        Loads team data on instantiation.
        """
        # Initialize the needed dicts
        self.leagues = {}
        self.teams_dict = {}
        self.football_teams = []

        self.teams_fixtures_dict = {}
        self.fixtures_by_league  = {}  # New structure to hold fixtures by league
        self.logger = configure_logging("teams_organizer", "system")
        
        self.load_fixtures()  # Load first since new_load_teams depends on it
        self.new_load_teams()
        

    def load_fixtures(self):
        """
        Loads and organizes all fixture data from JSON files by league ID.
        
        Reads from ./Images_HelperFiles/AllFixtures directory.
        Updates self.fixtures_by_league with structure:
        {league_id: [fixture_data, ...]}
        """
        fixtures_path = FIXTURES_PATH

        """
        Load all fixtures from files and organize them by league ID.
        """
        for filename in os.listdir(fixtures_path):
            file_path = os.path.join(fixtures_path, filename)
            with open(file_path, 'r', encoding='utf-8') as league_fixtures_file:
                fixtures = json.load(league_fixtures_file)
                for fixture in fixtures.get("response", []):
                    league_id = fixture["league"]["id"]
                    if league_id not in self.fixtures_by_league:
                        self.fixtures_by_league[league_id] = []
                    self.fixtures_by_league[league_id].append(fixture)


    def new_load_teams(self):
        """
        Processes team standings and matches them with fixtures.
        
        Reads from ./Images_HelperFiles/AllStandings directory.
        Updates:
        - self.teams_dict: {team_name: [team_id, league_id]}
        - self.football_teams: [team_names]
        - self.teams_fixtures_dict: {team_id: [{date, fixture_id}, ...]}
        
        Saves processed data to:
        - fixtures_by_league.json
        - information.json
        - teams.json
        """
        standings_path = STANDINGS_PATH
        
        
        with open(
            FIXTURES_BY_LEAGUE_PATH,
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(self.fixtures_by_league, f, ensure_ascii=False, indent=4)
        
        
        for filename in os.listdir(standings_path):
            file_path = os.path.join(standings_path, filename)
            with open(file_path, 'r', encoding='utf-8') as teams_file:
                standings = json.load(teams_file)

                if not standings.get("response"):
                    continue

                league_id = standings["response"][0]["league"]["id"]
                for standing in standings["response"][0]["league"]["standings"]:
                    for team in standing:
                        team_id = team["team"]["id"]
                        team_name = team["team"]["name"]
                        
                        '''Append teams to the teams list'''
                        self.teams_dict[team_name] = [team_id, league_id]
                        
                        
                        if team_name not in self.football_teams:
                            self.football_teams.append(team_name)
  
                        self.teams_fixtures_dict[team_id] = []

                        # Now, match teams with fixtures
                        #for fixture in self.fixtures_by_league.get(league_id, []):
                        for key_league_id in self.fixtures_by_league.keys():

                            league = self.fixtures_by_league.get(key_league_id)
                            
                            for individual_fixture in league:
                                    home_id = int(individual_fixture["teams"]["home"]["id"])
                                    away_id = int(individual_fixture["teams"]["away"]["id"])             
                                

                                    if team_id in [home_id, away_id]:
                                        self.logger.info(f"Team Found: {team_name}")
                                        
                                        fixture_id = int(individual_fixture["fixture"]["id"])
                                        date = individual_fixture["fixture"]["date"]


                                        # Parse the JSON date string into a datetime object
                                        json_date = datetime.fromisoformat(
                                            date.replace("Z", "+00:00")
                                        )
                                        current_date = datetime.now(timezone.utc)
                                        # 5 Days Ago
                                        five_days_ago = current_date - timedelta(days=5)

                                        # Check if the game happened in the last two days or is scheduled for the future

                                        if json_date > five_days_ago:  # two_days_agor

                                            self.teams_fixtures_dict[team_id].append(
                                                {
                                                    "date": date,  # Use the formatted date
                                                    "fixture_id": fixture_id,
                                                }
                                            )
                  
                  
        for team_id in self.teams_fixtures_dict.keys():
        
            self.logger.info(f"Team Sorted: {team_id}")
                        
            self.teams_fixtures_dict[team_id] = sorted(
            
                    self.teams_fixtures_dict[team_id],
                    key=lambda x: datetime.fromisoformat(x["date"]),
                )       
                     
            
        self.fixtures_by_league = None    
        
        with open(
            INFORMATION_PATH,
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(self.teams_fixtures_dict, f, ensure_ascii=False, indent=4)

        with open(
            TEAMS_PATH,
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(self.teams_dict, f, ensure_ascii=False, indent=4)


    def new_find_next_fixture(self, team_league):
        """
        Finds the next scheduled fixture for a team.
        
        Parameters:
        - team_league (list): [team_id, league_id]
        
        Returns:
        - tuple: (fixture_id, date) for the next game
        - None: if no fixtures found or team not found
        
        Note: Uses UTC-4 timezone and includes 4-hour delay buffer
        """
        """Find the team's next game."""
        '''team_league = [team_id, league_id];; Only need team_id in this new organization format'''
        if not team_league:
            self.logger.warning("Team or league not found.")
            return None, None

        team_id, league_id = team_league

        team_fixtures = self.teams_fixtures_dict.get(team_id, [])
        if not team_fixtures:
            self.logger.warning("No fixtures found for this team or Team ID not found in the specified league.")
            return None, None
        
        '''Add a loop  to iterate the list and grab the future game based on date, add 4 hours delay'''

        # Current date in UTC and additional 4-hour delay
        current_date_with_delay = datetime.now(timezone.utc) - timedelta(hours=4)

        # Find next game
        next_game = None
        for fixture in team_fixtures:
            fixture_date = datetime.fromisoformat(fixture["date"])
            if fixture_date >= current_date_with_delay:
                next_game = fixture
                break
        
        # Add null check before returning
        if next_game is None:
            self.logger.info("No future games found for this team.")
            return None, None
        
        return next_game["fixture_id"], next_game["date"]

    # Querying the data to grab the team fixture id
    def find_team_id(self, team_name):
        """
        Retrieves team ID and league ID for a given team name.
        
        Parameters:
        - team_name (str): Name of the team to look up
        
        Returns:
        - list: [team_id, league_id]
        - empty list: if team not found
        """
        self.logger.debug(f"Looking up team ID for: {team_name}")
        """Find the team ID given the name input."""
        '''return [team_id , league_id]'''
        # Directly return the result or 0 if not found
        return self.teams_dict.get(team_name, [])
    