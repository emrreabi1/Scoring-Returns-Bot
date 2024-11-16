# Football Live Score Discord Bot

A Discord bot that tracks live football matches and provides real-time updates, statistics, and events.

## Features
- Live match tracking
- Real-time goal notifications
- Match statistics
- Team schedules
- Multiple match following

## Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in your tokens
4. Run setup scripts:
   ```bash
   python scripts/setup_directories.py
   python scripts/league_status_checker.py
   ```
5. Start the bot: `python bot/main.py`

## Commands
- `/follow` - Follow a live match
- `/next_game` - Get team's next scheduled game
- `/current_games` - View your followed games

## Configuration
Edit `configs/config.py` to customize:
- Max simultaneous games
- League IDs to track
- Bot appearance settings

## Contributing
Pull requests welcome! See CONTRIBUTING.md for guidelines.

## License
MIT License - See LICENSE file