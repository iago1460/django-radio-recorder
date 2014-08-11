import datetime
import logging
import os
from pprint import pprint
import shlex
import shutil
import subprocess
import threading

class RecorderException(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class RecorderThread(threading.Thread):
    def __init__(self, config, file_name, info, stop_event, exceptions):
        threading.Thread.__init__(self)
        self.config = config
        self.seconds = int(info['duration'])

        self.title = ''
        self.author = ''
        self.album = ''
        self.track = ''
        self.genre = ''
        self.comment = 'Made by RadioCo www.RadioCo.org'
        if 'title' in info and info['title']:
            self.title = str(info['title'])
        if 'author' in info and info['author']:
            self.author = str(info['author'])
        if 'album' in info and info['album']:
            self.album = str(info['album'])
        if 'track' in info and info['track']:
            self.track = str(info['track'])
        if 'genre' in info and info['genre']:
            self.genre = str(info['genre'])

        self.file_name = file_name
        self.file_path = config.get('SETTINGS', 'recording_folder') + file_name
        self.stop_event = stop_event
        self.exceptions = exceptions
        self.command_1 = []
        for row in shlex.split(str(config.get('SETTINGS', 'recorder_command'))):
            self.command_1.append(self.replace(row))

        self.command_2 = []
        for row in shlex.split(str(config.get('SETTINGS', 'recorder_command_2'))):
            self.command_2.append(self.replace(row))

    def replace(self, string):
        line = string.replace ("[OUTPUT]", self.file_path)
        line = line.replace ("[TITLE]", self.title)
        line = line.replace ("[AUTHOR]", self.author)
        line = line.replace ("[ALBUM]", self.album)
        line = line.replace ("[TRACK]", self.track)
        line = line.replace ("[GENRE]", self.genre)
        line = line.replace ("[COMMENT]", self.comment)
        return line

    def run(self):
        try:
            start = datetime.datetime.now()
            process_1 = subprocess.Popen(self.command_1, stdout = subprocess.PIPE)
            process_2 = subprocess.Popen(self.command_2, stdin = process_1.stdout)
            return_code = process_1.poll()
            return_code_2 = process_2.poll()
            if return_code is not None or return_code_2 is not None:
                if return_code_2:
                    return_code = return_code_2
                raise RecorderException('An exception occurred while starting your command: command exited with code ' + str(-return_code))
            while not self.stop_event.is_set() and datetime.datetime.now() - start < datetime.timedelta(seconds = self.seconds):

                return_code = process_1.poll()
                return_code_2 = process_2.poll()
                if return_code is not None or return_code_2 is not None:
                    if return_code_2:
                        return_code = return_code_2
                    raise RecorderException('An exception occurred while executing your command: command exited with code ' + str(-return_code))

                self.stop_event.wait(0.1)
            process_1.terminate()

            post_actions_thread = PostRecorderThread(config = self.config, file_path = self.file_path, file_name = self.file_name)
            post_actions_thread.start()

        except OSError:
            e = RecorderException(msg = 'Recorder failed: Please check your libraries and your command in settings.ini')
            self.exceptions.put(e)
        except RecorderException as e:
            self.exceptions.put(e)
        except Exception as e:
            self.exceptions.put(e)



class PostRecorderThread(threading.Thread):
    def __init__(self, config, file_path, file_name):
        threading.Thread.__init__(self)
        self.config = config
        self.file_path = file_path
        self.file_name = file_name

    def run(self):
        shutil.move(self.file_path, self.config.get('SETTINGS', 'complete_folder') + self.file_name)
