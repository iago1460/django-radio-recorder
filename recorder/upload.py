"""
mutex = threading.Lock()
mutex.acquire()
mutex.release()
"""

import ConfigParser
import ftplib
import logging
import os
import shutil
import socket
import threading


class UploadThread(threading.Thread):
    def __init__(self, config, stop_event):
        threading.Thread.__init__(self)
        self.stop_event = stop_event
        self.config = config
        socket.setdefaulttimeout(self.config.getint('SETTINGS', 'socket_timeout'))

    def run(self):
        file = None
        session = None
        while (not self.stop_event.is_set()):
            try:
                file_name = self.get_file_to_upload()
                if file_name is not None:
                    session = ftplib.FTP(self.config.get('FTP', 'server'), self.config.get('FTP', 'username'), self.config.get('FTP', 'password'))
                    file_path = self.config.get('SETTINGS', 'complete_folder') + file_name
                    file = open(file_path, 'rb')
                    print('Uploading ' + file_name + '...')
                    session.storbinary('STOR ' + file_name, file)
                    print('Upload finished.')
                    logging.info('Uploaded: ' + file_name)
                    file.close()
                    session.quit()
                    if self.config.getboolean('SETTINGS', 'delete_files_after_upload'):
                        os.remove(file_path)
                    else:
                        # move file
                        shutil.move(file_path, self.config.get('SETTINGS', 'uploaded_folder') + file_name)
                else:
                    self.stop_event.wait(self.config.getint('SETTINGS', 'upload_time'))

            except ftplib.all_errors as e:
                msg = 'Error at upload: ' + str(type(e)) + ' - ' + str(e)
                print msg
                logging.error(msg)
                self.stop_event.wait(self.config.getint('SETTINGS', 'retry_time'))
                try:
                    file.close()
                except Exception:
                    pass
                try:
                    session.quit()
                except Exception:
                    pass

    def get_file_to_upload(self):
        for root, dirs, files in os.walk(self.config.get('SETTINGS', 'complete_folder')):
            for file_name in files:
                if file_name.endswith('.' + self.config.get('SETTINGS', 'file_extension')):
                    return file_name
        return None
