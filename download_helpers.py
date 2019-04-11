import re
import time
from subprocess import call, check_output, Popen, PIPE
from subprocess import CalledProcessError
from shows import shows_dict, base_url


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


def download_episode(show, episode):
    '''
        Returns true if episode downloaded correctly, false otherwise
    '''
    # The replacing probably no longer needs to happen based on an update to yt-downloader.
    url = base_url + episode['url'].replace("ondemand", "vod")

    try:
        path = get_episode_name_and_path_from_url(show, url)

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

            print("There was an error, pausing for a moment before contiuing...")
            time.sleep(2)
            print("Redownloading ", episode['title'])
            return download_episode(show, episode)

        return True

    except CalledProcessError:
        print("\n!!!!!Error Happened Here !!!!!!!\n")
        print("Redownloading ", episode['title'])
        time.sleep(2)
        return download_episode(show, episode)


