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
import threading


class UploadThread(threading.Thread):
    def __init__(self, config, stop_event):
        threading.Thread.__init__(self)
        self.stop_event = stop_event
        self.config = config

    def run(self):
        file = None
        session = None
        try:
            session = ftplib.FTP(self.config.get('FTP', 'server'), self.config.get('FTP', 'username'), self.config.get('FTP', 'password'))
            while (not self.stop_event.is_set()):
                file_name = self.get_file_to_upload()
                if file_name is not None:
                    file_path = self.config.get('SETTINGS', 'complete_folder') + file_name
                    file = open(file_path, 'rb')
                    print('Uploading ' + file_name + '...')
                    session.storbinary('STOR ' + file_name, file)
                    print('Upload finished.')
                    logging.info('Uploaded: ' + file_name)
                    file.close()

                    if self.config.getboolean('SETTINGS', 'delete_files_after_upload'):
                        os.remove(file_path)
                    else:
                        # move file
                        shutil.move(file_path, self.config.get('SETTINGS', 'uploaded_folder') + file_name)

                else:
                    self.stop_event.wait(self.config.getint('SETTINGS', 'upload_time'))

        except Exception as e:
            msg = 'Error at upload. Subsystem disconnected: ' + str(type(e)) + ' - ' + str(e)
            print msg
            logging.error(msg)
        finally:
            if file is not None:
                file.close()
            if session is not None:
                session.quit()


    def get_file_to_upload(self):
        for root, dirs, files in os.walk(self.config.get('SETTINGS', 'complete_folder')):
            for file_name in files:
                if file_name.endswith('.' + self.config.get('SETTINGS', 'file_extension')):
                    return file_name
        return None


'''
if __name__ == "__main__":
    CONFIG_FILE = 'settings.ini'
    global config
    config = ConfigParser.RawConfigParser()
    config.read(CONFIG_FILE)

    upload_stop = threading.Event()
    upload_thread = UploadThread(config = config, stop_event = upload_stop)
    upload_thread.run()
'''
