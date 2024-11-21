import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QMessageBox, QTabWidget,
    QTextEdit, QCheckBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import subprocess
from pathlib import Path
import asyncio
import logging
from datetime import datetime, timedelta
from scripts.setup_directories import create_directories, get_executable_dir
import json
from configs.config import LEAGUES_JSON_PATH

def load_available_leagues():
    try:
        with open(LEAGUES_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {str(league['id']): league['name'] for league in data['leagues']}
    except:
        return {}  # Return empty dict if file doesn't exist yet

AVAILABLE_LEAGUES = load_available_leagues()

class QtLogHandler(logging.Handler):
    def __init__(self, signal):
        super().__init__()
        self.signal = signal

    def emit(self, record):
        log_entry = self.format(record)
        self.signal.emit(log_entry)

class BotThread(QThread):
    log_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.loop = None
    
    def run(self):
        try:
            root_dir = Path(__file__).parent
            sys.path.append(str(root_dir))
            bot_dir = root_dir / 'bot'
            sys.path.append(str(bot_dir))
            
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            from bot.main import start_bot
            sys.stdout = LogCapture(self.log_signal)
            
            self.loop.create_task(start_bot())
            self.loop.run_forever()
        except Exception as e:
            self.log_signal.emit(f"Error: {str(e)}")
            import traceback
            self.log_signal.emit(traceback.format_exc())
        finally:
            if self.loop and self.loop.is_running():
                self.loop.close()
    
    def stop(self):
        if self.loop and self.loop.is_running():
            try:
                from bot.main import bot
                future = asyncio.run_coroutine_threadsafe(bot.close(), self.loop)
                future.result(timeout=5)
                self.loop.call_soon_threadsafe(self.loop.stop)
                self.loop.call_soon_threadsafe(self.loop.close)
            except Exception as e:
                self.log_signal.emit(f"Error during shutdown: {str(e)}")
                self.loop.stop()
                self.loop.close()

class LogCapture:
    def __init__(self, signal):
        self.signal = signal

    def write(self, text):
        if text.strip():
            self.signal.emit(text.strip())

    def flush(self):
        pass

class SetupWindow(QMainWindow):
    VERSION = "1.0.0"  # Add version tracking
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Scoring Returns Bot Setup v{self.VERSION}")
        self.setMinimumSize(800, 600)
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Initialize tabs
        self.init_env_tab()
        self.init_setup_tab()
        self.init_bot_tab()
        
        self.bot_thread = None
        self.load_env_vars()

    def init_env_tab(self):
        env_tab = QWidget()
        layout = QVBoxLayout(env_tab)
        
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Environment variables (without leagues section initially)
        self.env_inputs = {}
        env_vars = {
            'BOT_TOKEN': 'Discord Bot Token',
            'RAPIDAPI_KEY': 'RapidAPI Key',
            'FOOTER_ICON_URL': 'Footer Icon URL',
            'THUMBNAIL_LOGO': 'Thumbnail Logo URL',
            'EMBED_COLOR': 'Embed Color (default: 5763719)',
            'FOOTER_TEXT': 'Footer Text',
            'WEBSITE_NAME': 'Website Name',
            'WEBSITE_URL': 'Website URL',
            'MAX_SIMULTANEOUS_GAMES': 'Max Simultaneous Games (default: 3)',
            'LOOP_WAIT_TIME': 'Loop Wait Time (default: 45)'
        }
        
        for var, desc in env_vars.items():
            input_group = QWidget()
            input_layout = QHBoxLayout(input_group)
            
            label = QLabel(desc)
            label.setMinimumWidth(200)
            input_field = QLineEdit()
            input_field.setPlaceholderText(f"Enter {desc}")
            
            input_layout.addWidget(label)
            input_layout.addWidget(input_field)
            
            self.env_inputs[var] = input_field
            scroll_layout.addWidget(input_group)
        
        # Add fetch leagues button (disabled by default)
        self.fetch_leagues_btn = QPushButton("Fetch Available Leagues")
        self.fetch_leagues_btn.setEnabled(False)
        self.fetch_leagues_btn.clicked.connect(self.fetch_leagues)
        scroll_layout.addWidget(self.fetch_leagues_btn)
        
        # Connect text changed signals to validate configs
        for input_field in self.env_inputs.values():
            input_field.textChanged.connect(self.validate_configs)
        
        # League frame (hidden initially)
        self.league_frame = QFrame()
        self.league_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        self.league_frame.hide()
        league_layout = QVBoxLayout(self.league_frame)
        
        league_label = QLabel("Select Important Leagues:")
        league_layout.addWidget(league_label)
        
        self.league_search = QLineEdit()
        self.league_search.setPlaceholderText("Search leagues...")
        self.league_search.textChanged.connect(self.filter_leagues)
        league_layout.addWidget(self.league_search)
        
        league_scroll = QScrollArea()
        league_scroll.setWidgetResizable(True)
        league_scroll.setMinimumHeight(200)
        
        checkbox_container = QWidget()
        self.league_layout = QVBoxLayout(checkbox_container)
        self.league_checkboxes = {}
        
        league_scroll.setWidget(checkbox_container)
        league_layout.addWidget(league_scroll)
        scroll_layout.addWidget(self.league_frame)
        
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        
        layout.addWidget(scroll)
        
        # Save button
        save_btn = QPushButton("Save Environment Variables")
        save_btn.clicked.connect(self.save_env)
        layout.addWidget(save_btn)
        
        self.tabs.addTab(env_tab, "Environment Variables")

    def init_setup_tab(self):
        setup_tab = QWidget()
        layout = QVBoxLayout(setup_tab)
        
        # Status display
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)
        
        # Setup buttons
        setup_btn = QPushButton("1. Setup Directories")
        setup_btn.clicked.connect(self.run_setup)
        layout.addWidget(setup_btn)
        
        status_btn = QPushButton("2. Check League Status")
        status_btn.clicked.connect(self.check_status)
        layout.addWidget(status_btn)
        
        check_btn = QPushButton("Check Current Setup Status")
        check_btn.clicked.connect(self.check_setup_status)
        layout.addWidget(check_btn)
        
        self.tabs.addTab(setup_tab, "Setup")

    def init_bot_tab(self):
        bot_tab = QWidget()
        layout = QVBoxLayout(bot_tab)
        
        # Add logging path info
        log_path = os.path.join(get_executable_dir(), 'images_helper_files', 'Logging', 'systembot_main.log')
        log_info = QLabel(f"Full logs available at:\n{log_path}")
        log_info.setWordWrap(True)
        log_info.setStyleSheet("color: gray;")
        layout.addWidget(log_info)
        
        # Bot controls
        controls_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start Bot")
        self.start_btn.clicked.connect(self.start_bot)
        controls_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop Bot")
        self.stop_btn.clicked.connect(self.stop_bot)
        self.stop_btn.setEnabled(False)
        controls_layout.addWidget(self.stop_btn)
        
        layout.addLayout(controls_layout)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        layout.addWidget(self.log_display)
        
        self.tabs.addTab(bot_tab, "Bot Control")

    def load_env_vars(self):
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                for line in f:
                    if "=" in line:
                        key, value = line.strip().split("=", 1)
                        if key in self.env_inputs:
                            self.env_inputs[key].setText(value)
                        elif key == "IMPORTANT_LEAGUES":
                            league_ids = value.split(",")
                            for league_id in league_ids:
                                if league_id.strip() in self.league_checkboxes:
                                    self.league_checkboxes[league_id.strip()].setChecked(True)

    def save_env(self):
        env_content = ""
        for var, input_field in self.env_inputs.items():
            value = input_field.text()
            if value:
                env_content += f"{var}={value}\n"
        
        # Add selected leagues
        selected_leagues = []
        for league_id, checkbox in self.league_checkboxes.items():
            if checkbox.isChecked():
                selected_leagues.append(league_id)
        
        if selected_leagues:
            env_content += f"IMPORTANT_LEAGUES={','.join(selected_leagues)}\n"
        
        try:
            with open(".env", "w") as f:
                f.write(env_content)
            QMessageBox.information(self, "Success", "Environment variables saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save environment variables: {str(e)}")

    def run_setup(self):
        try:
            create_directories()
            self.status_text.append("✅ Directories created successfully!")
        except Exception as e:
            self.status_text.append(f"❌ Failed to create directories: {str(e)}")

    def check_status(self):
        try:
            # Import required functions
            from scripts.league_status_checker import (
                get_league_status, 
                parse_status_fixtures_available,
                get_league_standings,
                get_fixtures_file
            )
            
            # Get selected leagues from checkboxes
            important_leagues = [
                int(league_id) for league_id, checkbox in self.league_checkboxes.items() 
                if checkbox.isChecked()
            ]
            
            # Run the functions sequentially
            get_league_status()
            stats_availables = parse_status_fixtures_available()
            get_league_standings(stats_availables, important_leagues)
            get_fixtures_file(stats_availables, important_leagues)
            
            self.status_text.append("✅ League status checked successfully!")
        except Exception as e:
            self.status_text.append(f"❌ Failed to check league status: {str(e)}")

    def check_setup_status(self):
        self.status_text.clear()
        base_dir = get_executable_dir()
        
        # Check directories
        required_dirs = [
            'images_helper_files',
            'images_helper_files/GameBanners',
            'images_helper_files/AllFixtures',
            'images_helper_files/AllStandings',
            'images_helper_files/League_Status',
            'images_helper_files/15MinuteAnalysis',
            'images_helper_files/Logging',
            'images_helper_files/LiveJson'
        ]
        
        self.status_text.append("Checking directory structure...")
        for dir_path in required_dirs:
            full_path = os.path.join(base_dir, dir_path)
            if os.path.exists(full_path):
                self.status_text.append(f"✅ {dir_path} exists")
            else:
                self.status_text.append(f"❌ {dir_path} missing")
        
        # Check .env file
        self.status_text.append("\nChecking environment variables...")
        env_path = os.path.join(base_dir, ".env")
        if os.path.exists(env_path):
            self.status_text.append("✅ .env file exists")
        else:
            self.status_text.append("❌ .env file missing")

    def check_setup_requirements(self):
        base_dir = get_executable_dir()
        required_dirs = [
            'images_helper_files',
            'images_helper_files/GameBanners',
            'images_helper_files/AllFixtures',
            'images_helper_files/AllStandings',
            'images_helper_files/League_Status',
            'images_helper_files/15MinuteAnalysis',
            'images_helper_files/Logging',
            'images_helper_files/LiveJson'
        ]
        
        for dir_path in required_dirs:
            full_path = os.path.join(base_dir, dir_path)
            if not os.path.exists(full_path):
                return False, f"Directory missing: {dir_path}"
        
        # Check league status file and its age
        league_status_file = Path(os.path.join(base_dir, 'images_helper_files/League_Status/league_status.json'))
        if not league_status_file.exists():
            return False, "League status file missing. Please run League Status Checker."
            
        file_age = datetime.now() - datetime.fromtimestamp(league_status_file.stat().st_mtime)
        if file_age > timedelta(days=5):
            return False, "League status data is over 5 days old. Please run League Status Checker."
            
        return True, "All requirements met"

    def start_bot(self):
        if hasattr(self, 'bot_stopped') and self.bot_stopped:
            QMessageBox.warning(self, "Restart Required", 
                "Please restart the executable to start the bot again.")
            return
            
        if not self.bot_thread or not self.bot_thread.isRunning():
            # Check requirements before starting
            requirements_met, message = self.check_setup_requirements()
            if not requirements_met:
                QMessageBox.warning(self, "Setup Required", message)
                self.log_display.append(f"⚠️ {message}")
                return
                
            self.bot_thread = BotThread()
            self.bot_thread.log_signal.connect(self.update_log)
            self.bot_thread.start()
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.log_display.append("Bot started...")
        else:
            QMessageBox.information(self, "Bot Running", "The bot is already running.")
    
    def stop_bot(self):
        if self.bot_thread and self.bot_thread.isRunning():
            self.bot_thread.stop()
            self.bot_thread.wait()
            self.bot_thread = None
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.log_display.append("Bot stopped.")
            self.bot_stopped = True  # Add flag to track if bot was stopped
        else:
            QMessageBox.information(self, "Bot Not Running", "The bot is not running.")

    def update_log(self, message):
        self.log_display.append(message)

    def filter_leagues(self, search_text):
        """Filter leagues based on search text"""
        search_text = search_text.lower()
        
        for league_id, checkbox in self.league_checkboxes.items():
            league_info = AVAILABLE_LEAGUES[league_id]
            league_name = league_info['name'].lower()
            country_name = league_info['country'].lower()
            # Show checkbox if search text is in league name, country, or ID
            checkbox.setVisible(
                search_text in league_name or 
                search_text in country_name or
                search_text in league_id
            )

    def validate_configs(self):
        """Enable fetch leagues button only when all configs are set"""
        all_filled = all(input_field.text().strip() for input_field in self.env_inputs.values())
        self.fetch_leagues_btn.setEnabled(all_filled)

    def fetch_leagues(self):
        """Fetch and display available leagues"""
        try:
            temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)
            
            try:
                from scripts.league_status_checker import get_league_status
                get_league_status(temp_dir=temp_dir)
                
                with open(temp_dir / "league_status.json", 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    leagues_data = {
                        "leagues": [
                            {
                                "id": league['league']['id'], 
                                "name": league['league']['name'],
                                "country": league['country']['name']
                            }
                            for league in data['response']
                            if any(s['year'] == 2024 and 
                                  s['coverage']['fixtures']['events'] and
                                  s['coverage']['standings']
                                  for s in league['seasons'])
                        ]
                    }
                    
                    # Update available leagues with country info
                    global AVAILABLE_LEAGUES
                    AVAILABLE_LEAGUES = {
                        str(league['id']): {
                            'name': league['name'],
                            'country': league['country']
                        }
                        for league in leagues_data['leagues']
                    }
                    
                    self.populate_leagues(leagues_data)
                    self.league_frame.show()
                    
            finally:
                # Cleanup temp directory
                if temp_dir.exists():
                    for file in temp_dir.iterdir():
                        file.unlink()
                    temp_dir.rmdir()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch leagues: {str(e)}")

    def populate_leagues(self, data):
        """Populate league checkboxes from saved data"""
        # Clear existing checkboxes
        for checkbox in self.league_checkboxes.values():
            self.league_layout.removeWidget(checkbox)
            checkbox.deleteLater()
        self.league_checkboxes.clear()
        
        # Sort leagues by country, then name
        leagues = sorted(data['leagues'], key=lambda x: (x['country'], x['name']))
        
        # Create checkboxes with country info
        for league in leagues:
            league_id = str(league['id'])
            checkbox = QCheckBox(f"{league['country']} - {league['name']} ({league_id})")
            self.league_checkboxes[league_id] = checkbox
            self.league_layout.addWidget(checkbox)
        
        # Load selected leagues from .env
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                for line in f:
                    if line.startswith("IMPORTANT_LEAGUES="):
                        _, value = line.strip().split("=", 1)
                        selected_leagues = value.split(",")
                        for league_id in selected_leagues:
                            if league_id.strip() in self.league_checkboxes:
                                self.league_checkboxes[league_id.strip()].setChecked(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SetupWindow()
    window.show()
    sys.exit(app.exec())