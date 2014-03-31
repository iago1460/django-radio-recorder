
import errno
import logging
import os
import sys, signal, time, datetime, ConfigParser
import threading

from recorder import Recorder
import schedules


recorder_thread = None
schedules_stop = None
schedules_thread = None
config = None

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

    for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT]:
        signal.signal(sig, handler)

    make_sure_path_exists(config.get('SETTINGS', 'recording_folder'))
    make_sure_path_exists(config.get('SETTINGS', 'complete_folder'))


    logging.info('Starting system')

    global schedules_stop
    global schedules_thread
    schedules_stop = threading.Event()
    schedules_thread = schedules.SchedulesThread(config = config, offline = config.getboolean('SETTINGS', 'offline_mode'), stop_event = schedules_stop)
    schedules_thread.start()
    while True:
        info = schedules_thread.is_time_to_record()
        if info:
            global recorder_thread
            name = info['start'].strftime('%Y-%m-%d %H:%M:%S ') + info['title']
            recorder_thread = RecorderThread(file_name = name, seconds = info['duration'])
            recorder_thread.start()
            logging.debug('Starting recording: ' + name)
            recorder_thread.join()
            recorder_thread = None
        time.sleep(0.3)


class RecorderThread(threading.Thread):
    def __init__(self, file_name, seconds):
        threading.Thread.__init__(self)
        self.seconds = seconds
        self.file_name = file_name

    def run(self):
        try:
            rec = Recorder(channels = 2)
            with rec.open(config.get('SETTINGS', 'recording_folder') + self.file_name + '.wav', 'wb') as recfile:
                recfile.record(duration = self.seconds)
            logging.info('Recorder finished: ' + self.file_name)
        except Exception as e:
            logging.error('Recorder aborted: ' + self.file_name + ', reason: ' + e)

def handler(signum = None, frame = None):
    logging.debug('Signal handler called with signal:' + str(signum))
    schedules_stop.set()
    schedules_thread.join()
    if recorder_thread is not None:
        logging.error('Recorder aborted, signal:' + str(signum))
        recorder_thread.terminate()
    else:
        logging.debug('Program closed, signal:' + str(signum))
    # time.sleep(1)  #here check if process is done
    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv)
