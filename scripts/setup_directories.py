import os
import sys

def get_executable_dir():
    # Get the directory containing the executable
    if getattr(sys, 'frozen', False):
        # Running as executable
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def create_directories():
    # Get base directory (where executable is)
    base_dir = get_executable_dir()
    
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
    create_directories()