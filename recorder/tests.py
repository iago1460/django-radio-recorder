import sys, signal, time, datetime, ConfigParser
import unittest

from schedules import SchedulesThread


class TestSequenceFunctions(unittest.TestCase):
    config = None

    def setUp(self):
        global config
        config = ConfigParser.RawConfigParser()
        config.add_section('SETTINGS')
        config.set('SETTINGS', 'schedule_file', 'test_schedules.txt')
        config.set('SETTINGS', 'update_time', '10')
        config.set('SETTINGS', 'retry_time', '3')
        config.set('SETTINGS', 'url', 'http://localhost:8000/api/1/recording_schedules/')

    def test_save_load_file(self):
        schedules = SchedulesThread(config = config, stop_event = None)
        now = datetime.datetime.now()
        now = now.replace(microsecond = 0)
        now_str = now.strftime('%Y-%m-%d %H:%M:%S')
        schedules.schedule_list = [{"start": "2014-03-29 10:30:00", "duration": "120", "id": "2", "title": "interview"}]
        self.assertEqual(None, schedules.is_time_to_record())

        schedules.schedule_list = [{"start": "2014-03-29 10:30:00", "duration": 120, "id": 2, "title": "interview"},
                                   {"start": now_str, "duration": 1, "id": 1, "title": "on-live"}]
        self.assertEqual({"start": now_str, "duration": 1, "id": 1, "title": "on-live"}, schedules.is_time_to_record(now))


if __name__ == '__main__':
    unittest.main()
