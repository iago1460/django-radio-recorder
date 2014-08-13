"""
mutex = threading.Lock()
mutex.acquire()
mutex.release()
"""

import json, requests, datetime, time
import logging
import threading

from requests.exceptions import RequestException, ConnectionError, HTTPError, URLRequired, TooManyRedirects


class SchedulesThread(threading.Thread):
    def __init__(self, config, stop_event, offline = False):
        threading.Thread.__init__(self)
        self.schedule_list = []
        self.offline = offline
        self.stop_event = stop_event
        self.config = config

    def run(self):
        while (not self.stop_event.is_set()):
            try:
                if self.offline == False:
                    self.update_recoder_list()
                self.load_recorder_list()
                # time.sleep(int(self.config.get('SETTINGS', 'update_time')))
                self.stop_event.wait(self.config.getint('SETTINGS', 'update_time'))
            except Exception as e:
                msg = 'Error at schedules ' + str(type(e)) + ' - ' + str(e)
                print msg
                logging.error(msg)
                self.stop_event.wait(self.config.getint('SETTINGS', 'retry_time'))

    def update_recoder_list(self):
        params = dict(
            start = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        )
        headers = {'content-type' : 'application/json',
                   'Accept-Language': self.config.get('SETTINGS', 'metadata_language'),
                   'Authorization': 'Token ' + self.config.get('SETTINGS', 'token')}

        resp = requests.get(url = self.config.get('SETTINGS', 'url') + 'recording_schedules/', params = params,
                            headers = headers)

        if resp.status_code != 200:
            resp.raise_for_status()

        # except (HTTPError, RequestException, ConnectionError, HTTPError, URLRequired, TooManyRedirects) as e:
        data = json.loads(resp.content)
        with open(self.config.get('SETTINGS', 'schedule_file'), 'w') as outfile:
            json.dump(obj = data, fp = outfile, sort_keys = True, indent = 4)


    def load_recorder_list(self):
        with open(self.config.get('SETTINGS', 'schedule_file'), 'r') as json_file:
            self.schedule_list = json.load(json_file)

    def is_time_to_record(self, now = None):
        if now is None:
            now = datetime.datetime.now()
            now = now.replace(microsecond = 0)
        for row in self.schedule_list:  # TODO: dictionary
            schedule = datetime.datetime.strptime(row["start"], '%Y-%m-%d %H-%M-%S')
            if now == schedule:
                return row
                # {"id": int(row["id"]), "duration": int(row["duration"]), "title": row["title"], "start": schedule}
        return None

