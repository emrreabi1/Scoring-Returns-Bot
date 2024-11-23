<div align="center">
  <h1>Scoring Returns Bot</h1>
  <br/>
  
  <p><i>A powerful Discord bot that tracks live football matches and provides real-time updates, statistics, and events, similar to popular sports platforms like FlashScore and LiveScore. <br/>Created by <a href="https://github.com/BernKing">@BernKing</a>.</i></p>
  <br />
</div>

## Overview

This Discord bot provides **comprehensive real-time football match tracking**, delivering instant updates just like major sports platforms. It monitors matches continuously, sending immediate notifications for key events and maintaining live statistics throughout the game. The bot is **fully open source** and designed to be easy to use with simple commands and beautiful formatting.

## Features
- **Live Match Tracking** with real-time updates (similar to FotMob/LiveScore)
- **Instant Event Notifications** for:
  - Goals
  - VAR decisions
  - Red/Yellow cards
  - Match events (kickoff, half-time, full-time, extra time)
- **Detailed Match Statistics** including:
  - Possession
  - Shots (on/off target)
  - Corner kicks
  - Fouls and offsides
  - And many more match stats
- **Team Schedules** and upcoming matches
- **Multiple Match Following** capability
- **Fully Customizable** appearance and behavior

## Commands
- **/follow** - Follow a live game with minute-by-minute updates showing:
  - Time elapsed
  - Game status
  - Goals & halftime scores
  - Corner kicks
  - Shots on goal
  - Ball possession
  - Live notifications for goals, VAR, cards
- **/next_game** - Get a team's next scheduled match with date and time
- **/current_games** - View your actively followed games and remaining slots
- **/ping** - Check if the bot is online

## Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/BernKing/Scoring-Returns-Bot.git
   cd Scoring-Returns-Bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and configure:
   - `BOT_TOKEN` - Your Discord bot token
   - `RAPIDAPI_KEY` - Your API-Football key
   - `FOOTER_ICON_URL` - URL for footer icon in messages
   - `THUMBNAIL_LOGO_URL` - URL for thumbnail in messages
   - `EMBED_COLOR` - Hex color for message sidebars (default: 5763719)
   - `FOOTER_TEXT` - Custom footer text
   - `WEBSITE_NAME` - Your website name for references
   - `WEBSITE_URL` - Your website URL
   - `MAX_SIMULTANEOUS_GAMES` - Max games per user (default: 3)
   - `LOOP_WAIT_TIME` - Update interval in seconds (default: 45)

4. Run setup scripts:
   ```bash
   python scripts/setup_directories.py
   python scripts/league_status_checker.py
   ```

5. Start the bot:
   ```bash
   python bot/main.py
   ```

## Executable Version
For non-technical users, download the executable from [Releases](https://github.com/BernKing/Scoring-Returns-Bot/releases) which provides a GUI for all setup and configuration options.

## Featured Images

<p align="center">
  <img src="assets/images/bot1.png" alt="Bot Preview 1" width="250"/>
  <img src="assets/images/bot2.png" alt="Bot Preview 2" width="250"/>
  <img src="assets/images/bot3.png" alt="Bot Preview 3" width="250"/>
</p>
<p align="center">
  <img src="assets/images/bot4.png" alt="Bot Preview 4" width="250"/>
  <img src="assets/images/bot5.png" alt="Bot Preview 5" width="250"/>
</p>

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements
- [API-Football](https://www.api-football.com/) for the football data API
- [Pycord](https://github.com/Pycord-Development/pycord) for Discord API wrapper

## Contact
- X (Twitter): [@bernKing20](https://x.com/bernKing20)
- Email: [bernardoalmeida2004@gmail.com](mailto:bernardoalmeida2004@gmail.com)
