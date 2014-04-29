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
    def __init__(self, config, file_name, seconds, stop_event, exceptions):
        threading.Thread.__init__(self)
        self.config = config
        self.seconds = seconds
        self.file_name = file_name
        self.file_path = config.get('SETTINGS', 'recording_folder') + file_name
        self.stop_event = stop_event
        self.exceptions = exceptions
        self.command = []
        for row in shlex.split(str(config.get('SETTINGS', 'recorder_command'))):
            self.command.append(row.replace ("[OUTPUT]", self.file_path))

    def run(self):
        try:
            start = datetime.datetime.now()
            process = subprocess.Popen(self.command)
            return_code = process.poll()
            if return_code is not None:
                raise RecorderException('An exception occurred while starting your command: command exited with code ' + str(-return_code))
            while not self.stop_event.is_set() and datetime.datetime.now() - start < datetime.timedelta(seconds = self.seconds):

                return_code = process.poll()
                if return_code is not None:
                    raise RecorderException('An exception occurred while executing your command: command exited with code ' + str(-return_code))

                self.stop_event.wait(0.1)
            process.terminate()

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
