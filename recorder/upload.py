"""
mutex = threading.Lock()
mutex.acquire()
mutex.release()
"""

import ConfigParser
import ftplib
import logging
import os
import re
import shutil
import socket
import threading
import magic
import requests

class UploadException(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class UploadThread(threading.Thread):
    def __init__(self, config, stop_event):
        threading.Thread.__init__(self)
        self.stop_event = stop_event
        self.config = config
        socket.setdefaulttimeout(self.config.getint('SETTINGS', 'socket_timeout'))

    def notify_server(self, programme_id, date, file_name, mime_type, length):
        not_sended = True

        data = {
            'date' : date,
            'programme_id' : programme_id,
            'file_name' : file_name,
            'mime_type' : mime_type,
            'length' : length,
        }
        headers = {'content-type' : 'application/json', 'Authorization': 'Token ' + self.config.get('SETTINGS', 'token')}

        while not_sended:
            try:
                resp = requests.get(url = self.config.get('SETTINGS', 'url') + 'submit_recorder/', params = data,
                    headers = headers)
                if resp.status_code != 200:
                    resp.raise_for_status()

                not_sended = False
            except Exception as e:
                msg = 'Error notifying server: ' + str(type(e)) + ' - ' + str(e)
                print msg
                logging.error(msg)
                self.stop_event.wait(self.config.getint('SETTINGS', 'retry_time'))

    def ftp_upload(self, file, new_file_name):
        session = None
        try:
            session = ftplib.FTP(self.config.get('FTP', 'server'), self.config.get('FTP', 'username'), self.config.get('FTP', 'password'))
            print('Uploading ' + new_file_name + '...')
            session.storbinary('STOR ' + new_file_name, file)
            print('Upload finished.')
            logging.info('Uploaded: ' + new_file_name)
        except Exception:
            try:
                if session:
                    session.quit()
                raise
            except Exception:
                raise

    def run(self):
        file = None

        while (not self.stop_event.is_set()):
            try:
                file_name = self.get_file_to_upload()
                if file_name is not None:
                    file_path = self.config.get('SETTINGS', 'complete_folder') + file_name
                    file = open(file_path, 'rb')

                    try:
                        # get id and change name
                        m = re.match("(?P<DATE>[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}-[0-9]{2}-[0-9]{2}) (?P<ID>[0-9]*)(?P<NEX>.*)", file_name)
                        if not m:
                            raise ValueError()
                        date = m.group('DATE')
                        programme_id = int(m.group('ID'))
                        new_file_name = m.group('DATE') + m.group('NEX')
                    except ValueError, AttributeError:
                        raise UploadException('The name pattern \"' + file_name + '\" it\'s incorrect')

                    # get mime_type
                    mymagic = magic.Magic(mime = True)
                    mime_type = mymagic.from_file(file_path)
                    # get length in bytes
                    length = os.path.getsize(file_path)

                    # notify server
                    self.notify_server(programme_id, date, new_file_name, mime_type, length)

                    # upload file
                    if self.config.getboolean('FTP', 'enable'):
                        self.ftp_upload(file, new_file_name)

                    file.close()

                    if self.config.getboolean('SETTINGS', 'delete_files_after_upload'):
                        os.remove(file_path)
                    else:
                        shutil.move(file_path, self.config.get('SETTINGS', 'uploaded_folder') + new_file_name)
                else:
                    self.stop_event.wait(self.config.getint('SETTINGS', 'upload_time'))

            except ftplib.all_errors as e:
                msg = 'Error at ftp upload: ' + str(type(e)) + ' - ' + str(e)
                print msg
                logging.error(msg)
                try:
                    file.close()
                except Exception:
                    pass
                self.stop_event.wait(self.config.getint('SETTINGS', 'retry_time'))
            except Exception as e:
                logging.error('Error at upload ' + str(type(e)) + ' - ' + str(e))
                self.stop_event.wait(self.config.getint('SETTINGS', 'retry_time'))
                try:
                    file.close()
                except Exception:
                    pass
                self.stop_event.wait(self.config.getint('SETTINGS', 'retry_time'))

    def get_file_to_upload(self):
        for root, dirs, files in os.walk(self.config.get('SETTINGS', 'complete_folder')):
            for file_name in files:
                if file_name.endswith('.' + self.config.get('SETTINGS', 'file_extension')):
                    return file_name
        return None
