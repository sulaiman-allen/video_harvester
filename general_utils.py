import sqlite3
import os
from subprocess import call

#SELECTED_PARSER = 'nhk'

SELECTED_PARSER = os.getenv('SELECTED_PARSER')

#DEFAULT_PATH = os.path.join(os.path.dirname(__file__), 'episode_db.sqlite3')
DEFAULT_PATH = os.getcwd() + '/parsers/' + SELECTED_PARSER + '/episode_db.sqlite3'

def db_connect(db_path=DEFAULT_PATH):
    return sqlite3.connect(db_path)

def force_quit_browser_silently():
    FNULL = open(os.devnull, 'w')

    call([
        "ps", "aux", "|",
        "grep", "chromium", "|",
        "grep", "-v", "grep", "|",
        "kill", "$(awk", "'{print $2}'", "&>", "/dev/null"
    ], shell=True, stdout=FNULL)

    print("Force Quitting Browser...")


