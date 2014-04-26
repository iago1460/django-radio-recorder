
import errno
import logging
import os
from pprint import pprint
import shlex
import sys, signal, time, datetime, ConfigParser, Queue
import threading

import schedules, subprocess


recorder_thread = None
schedules_stop = None
recorder_stop = None
main_stop = None
schedules_thread = None
config = None

class RecorderException(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def minutes_to_timedelta(minutes):
    return datetime.timedelta(minutes = minutes)


def main(argv):
    CONFIG_FILE = 'settings.ini'
    global config
    config = ConfigParser.RawConfigParser()
    config.read(CONFIG_FILE)

    requests_log = logging.getLogger("requests")
    requests_log.setLevel(logging.WARNING)
    # logging.basicConfig(filename = config.get('SETTINGS', 'log_file'), level = logging.DEBUG)
    logging.basicConfig(filename = config.get('SETTINGS', 'log_file'), level = logging.DEBUG, format = '%(asctime)s %(message)s', datefmt = '%Y-%m-%d %H:%M:%S')

    if sys.platform == 'win32':
        signals = [signal.SIGTERM, signal.SIGINT]
    else:
        signals = [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT]
    for sig in signals:
        signal.signal(sig, handler)

    make_sure_path_exists(config.get('SETTINGS', 'recording_folder'))
    make_sure_path_exists(config.get('SETTINGS', 'complete_folder'))


    logging.info('Starting system')

    try:
        global schedules_stop
        global schedules_thread
        schedules_stop = threading.Event()
        schedules_thread = schedules.SchedulesThread(config = config, offline = config.getboolean('SETTINGS', 'offline_mode'), stop_event = schedules_stop)
        schedules_thread.start()

        global recorder_stop
        recorder_stop = threading.Event()

        global main_stop
        main_stop = threading.Event()

        global recorder_thread
        exceptions = Queue.Queue()

        while not main_stop.is_set():
            info = schedules_thread.is_time_to_record()
            if recorder_thread is not None:
                try:
                    exception = exceptions.get(block = False)
                except Queue.Empty:
                    pass
                else:
                    # exc_type, exc_obj, exc_trace = exc
                    raise exception

            if info and (recorder_thread is None or (recorder_thread is not None and not recorder_thread.is_alive())):
                name = info['start'].strftime('%Y-%m-%d %H-%M-%S ') + info['title']
                file_path = config.get('SETTINGS', 'recording_folder') + name + '.' + config.get('SETTINGS', 'file_extension')

                recorder_thread = RecorderThread(file_name = name, file_path = file_path, exceptions = exceptions, seconds = info['duration'],
                                                 stop_event = recorder_stop, command = str(config.get('SETTINGS', 'recorder_command')))
                logging.debug('Starting recording: ' + name)
                recorder_thread.start()

            time.sleep(0.3)
    except RecorderException as e:
        print e
        logging.error(e)
    except Exception as e:
        print ('Error ' + str(type(e)) + ' - ' + str(e))
        logging.error('Error ' + str(type(e)) + ' - ' + str(e))
    finally:
        close_all()


class RecorderThread(threading.Thread):
    def __init__(self, file_name, file_path, command, seconds, stop_event, exceptions):
        threading.Thread.__init__(self)
        self.seconds = seconds
        self.file_name = file_name
        self.file_path = file_path
        self.stop_event = stop_event
        self.exceptions = exceptions
        self.command = []
        for row in shlex.split(command):
            self.command.append(row.replace ("[OUTPUT]", file_path))

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
        except OSError:
            e = RecorderException(msg = 'Recorder failed: Please check your libraries and your command in settings.ini')
            self.exceptions.put(e)
        except RecorderException as e:
            self.exceptions.put(e)
        except Exception as e:
            self.exceptions.put(e)



def close_all():
    main_stop.set()
    schedules_stop.set()
    schedules_thread.join()
    if recorder_thread is not None and recorder_thread.is_alive():
        logging.error('Recorder of ' + str(recorder_stop.file_name) + ' aborted')
        recorder_stop.set()
        recorder_thread.join()
    logging.info('Programm closed')
    # time.sleep(1.5)
    sys.exit(0)


def handler(signum = None, frame = None):
    logging.debug('Signal handler called with signal:' + str(signum))
    close_all()

if __name__ == "__main__":
    main(sys.argv)
