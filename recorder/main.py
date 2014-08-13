
import errno
import logging
import os
import sys, signal, time, datetime, ConfigParser, Queue
import threading

from recorder import RecorderException, RecorderThread, PostRecorderThread
from schedules import SchedulesThread
from upload import UploadThread


recorder_thread = None
schedules_stop = None
upload_stop = None
recorder_stop = None
main_stop = None
schedules_thread = None
upload_thread = None
config = None

post_actions_threads_list = []

def join_post_actions():
    global post_actions_threads_list
    for thread in post_actions_threads_list:
        if not thread.is_alive():
            thread.join(1)
            post_actions_threads_list.remove(thread)
            return True
    return False

def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def minutes_to_timedelta(minutes):
    return datetime.timedelta(minutes = minutes)


def main(argv):

    try:
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


        logging.info('Starting system')
        offline_mode = config.getboolean('SETTINGS', 'offline_mode')

        make_sure_path_exists(config.get('SETTINGS', 'recording_folder'))
        make_sure_path_exists(config.get('SETTINGS', 'complete_folder'))
        if not offline_mode:
            if config.get('SETTINGS', 'token') == None or config.get('SETTINGS', 'token') == '':
                raise ConfigParser.NoOptionError('token', 'SETTINGS')
            make_sure_path_exists(config.get('SETTINGS', 'uploaded_folder'))
            global upload_stop
            upload_stop = threading.Event()
            global upload_thread
            upload_thread = UploadThread(config = config, stop_event = upload_stop)
            upload_thread.start()

        global schedules_stop
        schedules_stop = threading.Event()
        global schedules_thread
        schedules_thread = SchedulesThread(config = config, offline = offline_mode, stop_event = schedules_stop)
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

            if recorder_thread is not None and not recorder_thread.is_alive():
                    global post_actions_threads_list
                    # Do post actions
                    post_actions_thread = PostRecorderThread(config = config, file_path = recorder_thread.file_path, file_name = recorder_thread.file_name)
                    post_actions_thread.start()
                    post_actions_threads_list.append(post_actions_thread)
                    # join dead thread
                    recorder_thread.join(1)
                    recorder_thread = None


            if info and recorder_thread is None:
                name = info['issue_date'] + ' ' + str(info['id']) + ' ' + info['programme_name'] + '.' + config.get('SETTINGS', 'file_extension')
                file_path = config.get('SETTINGS', 'recording_folder') + name
                recorder_thread = RecorderThread(config = config, file_name = name, file_path = file_path, exceptions = exceptions, info = info,
                                                 stop_event = recorder_stop)
                logging.debug('Starting recording: ' + name)
                recorder_thread.start()

            join_post_actions()
            time.sleep(0.3)
    except RecorderException as e:
        print e
        logging.error(e)
    except Exception as e:
        print ('Error ' + str(type(e)) + ' - ' + str(e))
        logging.error('Error ' + str(type(e)) + ' - ' + str(e))
    finally:
        close_all()





def close_all():
    if main_stop:
        main_stop.set()
    if schedules_stop:
        schedules_stop.set()
    if schedules_thread:
        schedules_thread.join()
    if recorder_thread is not None and recorder_thread.is_alive():
        logging.error('Recorder of ' + str(recorder_thread.file_name) + ' aborted')
        recorder_stop.set()
        recorder_thread.join()
    if upload_thread is not None:
        upload_stop.set()
        upload_thread.join()
    logging.info('Programm closed')
    # time.sleep(1.5)
    sys.exit(0)


def handler(signum = None, frame = None):
    logging.debug('Signal handler called with signal:' + str(signum))
    close_all()

if __name__ == "__main__":
    main(sys.argv)
