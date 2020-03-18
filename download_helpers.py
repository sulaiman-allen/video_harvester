import re
import os
import time
from subprocess import Popen, PIPE
from subprocess import CalledProcessError
from rq.timeouts import JobTimeoutException

from shows import shows_dict, base_url
from write_nfo import write_nfo
from general_utils import db_connect, force_quit_browser_silently

def check_if_show_is_needed(show, episode):
    '''
        Returns true if episode exists already in database, false otherwise.
    '''
    con = db_connect()
    cur = con.cursor()

    cur.execute("SELECT * FROM episodes WHERE show_name = ? AND episode_name = ?",\
        (show, episode['title']))

    if not cur.fetchone():
        return True
    else:
        return False


def add_entry_to_db(show, episode):
    con = db_connect()
    cur = con.cursor()
    show_sql = "INSERT INTO episodes (show_name, url, episode_name, date) VALUES (?, ?, ?, ?)"
    cur.execute(show_sql, (show, episode['url'], episode['title'], episode['date']))
    con.commit()

def get_episode_name_and_path_from_url(show, url):

    try:
        process = Popen([ "youtube-dl", "--get-title", url], stdout=PIPE, stderr=PIPE)
        result, error = process.communicate()
        error = error.decode('utf-8')
        result = result.decode('utf-8')
        if process.returncode != 0:
            print(error)
            time.sleep(2)
            return get_episode_name_and_path_from_url(show, url)

        filename = re.sub('[^0-9a-zA-Z\-\_\.\']+', " ", re.sub('[:]+', "-", result))
        filename = filename.strip()
        directory = shows_dict[show].strip()
        return directory + '/' + filename

    except CalledProcessError as error:
        print("Getting the episode name threw an error. Retrying...")
        time.sleep(2)
        return get_episode_name_and_path_from_url(show, url)


def download_episode(show, episode, path):
    '''
        Returns true if episode downloaded correctly, false otherwise
    '''

    try:
        if not path:
            return None

        process = Popen([\
            "youtube-dl", \
            #"--verbose", #Temp
            "--write-thumbnail", \
            "--external-downloader", "axel", \
            "--external-downloader-args", "'-n 15 -a -k'", \
            "--format", "best", \
            "-o", './downloaded/' + path + '.%(ext)s', episode['url'] \
        ], stderr=PIPE, stdout=PIPE)


        while True:
            output = process.stdout.readline().decode("utf-8")
            if output == "" and process.poll() is not None:
                break
            if output and ("Writing thumbnail" in output or "Destination" in output or "Fixing" in output):
                print(output)
        
        #if process.returncode != 0:
        if process.poll() != 0:
            error =  process.stderr.readline().decode("utf-8")
            if "ERROR: Unable to find episode" in error:
                print("###########Epsisode couldn't be downloaded")
                return False

            print("There was an error, pausing for a moment before continuing...")
            print(error)
            time.sleep(2)
            print("Redownloading ", episode['title'])
            return download_episode(show, episode, path)

        return True

    except CalledProcessError:
        print("\n!!!!!Error Happened Here !!!!!!!\n")
        print("Redownloading ", episode['title'])
        time.sleep(2)
        return download_episode(show, episode, path)

def async_logic(show, episode):
    try:
        if not check_if_show_is_needed(show, episode):
            return False

        path = get_episode_name_and_path_from_url(show, url=episode['url'])
        if not download_episode(show, episode, path):
           return False

        air_date = write_nfo(show, episode, path)
        episode['date'] = air_date
        add_entry_to_db(show, episode)
        return True

    except JobTimeoutException:
        #force_quit_browser_silently()
        raise JobTimeoutException
        return False
