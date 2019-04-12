import re
import os
import time
from subprocess import Popen, PIPE
from subprocess import CalledProcessError
from rq.timeouts import JobTimeoutException

from write_nfo import write_nfo
from shows import shows_dict, base_url
from general_utils import db_connect, force_quit_browser_silently


def add_entry_to_db(show, episode):
    con = db_connect()
    cur = con.cursor()
    show_sql = "INSERT INTO episodes (show_name, url, episode_name, date) VALUES (?, ?, ?, ?)"
    cur.execute(show_sql, (show, episode['url'], episode['title'], episode['date']))
    con.commit()

def get_episode_name_and_path_from_url(show, url):

    try:
        p = Popen([ "youtube-dl", "--get-title", url], stdout=PIPE, stderr=PIPE)
        result, error = p.communicate()
        error = error.decode('utf-8')
        result = result.decode('utf-8')
        if p.returncode != 0:
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
    # The replacing probably no longer needs to happen based on an update to yt-downloader.
    url = base_url + episode['url'].replace("ondemand", "vod")

    try:
        #path = get_episode_name_and_path_from_url(show, url)

        if not path:
            return None

        p = Popen([\
            "youtube-dl", \
            "--write-thumbnail", \
            "--external-downloader", "axel", \
            "--external-downloader-args", "'-n 15 -a -k'", \
            "--format", "best", \
            "-o", './downloaded/' + path + '.%(ext)s', url \
        ], stderr=PIPE)

        error = p.communicate()

        if p.returncode != 0:
            error =  error[1].decode("utf-8")
            if "ERROR: Unable to find episode" in error:
                print("###########Epsisode couldn't be downloaded")
                return False

            print("There was an error, pausing for a moment before continuing...")
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
        path = get_episode_name_and_path_from_url(show, url=base_url + episode['url'].replace("ondemand", "vod"))
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
