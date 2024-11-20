import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from configs.config import PROJECT_ROOT

def get_executable_dir():
    if getattr(sys, 'frozen', False):
        # When frozen, use the directory where the executable is located
        return os.path.dirname(os.path.realpath(sys.argv[0]))
    
    else:
        # When not frozen, use the script's parent directory
            
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def create_directories():
    #base_dir = get_executable_dir()
    base_dir = PROJECT_ROOT
    
    directories = [
        'images_helper_files',
        'images_helper_files/GameBanners',
        'images_helper_files/AllFixtures',
        'images_helper_files/AllStandings',
        'images_helper_files/League_Status',
        'images_helper_files/15MinuteAnalysis',
        'images_helper_files/Logging',
        'images_helper_files/LiveJson'
    ]
    
    for directory in directories:
        full_path = os.path.join(base_dir, directory)
        os.makedirs(full_path, exist_ok=True)
        print(f"Created directory: {full_path}")

if __name__ == "__main__":
    print(f"Base Directory: {PROJECT_ROOT}")
    create_directories()