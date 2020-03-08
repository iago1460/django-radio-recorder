
import asyncio
import functools
import logging
import mimetypes
import signal

from radioco_recorder.const import RETRY_TIME, MIN_WAIT_TIME
from radioco_recorder.filesystem import create_folder, generate_file_path, move_file
from radioco_recorder.radioco import submit_episode, get_episodes
from radioco_recorder.recorder import record
from radioco_recorder.utils import datetime_now_tz, index_episodes


class SignalHandler:

    def __init__(self):
        event_loop = asyncio.get_event_loop()

        event_loop.add_signal_handler(
            signal.SIGINT,
            functools.partial(self.signal_handler, name='SIGINT'),
        )
        event_loop.add_signal_handler(
            signal.SIGTERM,
            functools.partial(self.signal_handler, name='SIGTERM'),
        )
        event_loop.add_signal_handler(
            signal.SIGQUIT,
            functools.partial(self.signal_handler, name='SIGQUIT'),
        )

    def terminate(self):
        raise RuntimeError('terminate method not implemented')

    def signal_handler(self, name):
        logging.info(f'Signal {name} received')
        self.terminate()


class RecorderApp(SignalHandler):

    def __init__(self, radioco_endpoint, radioco_token, file_path_format, tmp_path, output_path, tz, language,
                 recording_input, recording_format):
        super().__init__()
        self.radioco_endpoint = radioco_endpoint
        self.radioco_token = radioco_token
        self.file_path_format = file_path_format
        self.tmp_path = tmp_path
        self.output_path = output_path
        self.tz = tz
        self.language = language
        self.recording_input = recording_input
        self.recording_format = recording_format

        loop = asyncio.get_event_loop()

        self.episodes = []
        self.episodes_to_submit = asyncio.Queue(loop=loop)

        self.update_episodes_task = loop.create_task(self.update_episodes())
        self.record_task = loop.create_task(self.record())
        self.submit_episodes_task = loop.create_task(self.submit_episodes())

    async def submit_episodes(self):
        while True:
            episode_data = await self.episodes_to_submit.get()
            logging.debug(f"Submitting episode: \"{episode_data['file_name']}\"")
            try:
                await submit_episode(self.radioco_endpoint, self.radioco_token, params=episode_data)
            except Exception as exception:
                logging.error(f'Error submitting episode: "{type(exception)} - {exception}"')
                self.episodes_to_submit.put_nowait(episode_data)
                await asyncio.sleep(RETRY_TIME)
            else:
                logging.info(f"Episode \"{episode_data['file_name']}\" was submitted")

    async def update_episodes(self):
        while True:
            logging.debug(f'Getting episodes')
            params = {
                'start': datetime_now_tz().astimezone(self.tz).strftime('%Y-%m-%d %H:%M:%S')
            }
            try:
                episodes = await get_episodes(self.radioco_endpoint, self.radioco_token, language=self.language, params=params)
            except Exception as exception:
                logging.error(f'Error getting episodes: "{type(exception)} - {exception}"')
            else:
                self.episodes = index_episodes(episodes, tz=self.tz)
                logging.info(f'Episodes updated from server')
            await asyncio.sleep(RETRY_TIME)

    async def next_episode_to_record(self):
        while True:
            for (start_dt, end_dt), episode in self.episodes:
                now = datetime_now_tz()
                if now < start_dt:
                    # if the episodes are order by start date we can avoid checking the rest
                    break
                if start_dt <= now < end_dt:
                    yield episode
            await asyncio.sleep(MIN_WAIT_TIME)

    async def record(self):
        async for episode in self.next_episode_to_record():
            relative_file_path = generate_file_path(
                file_path_format=self.file_path_format,
                file_extension=self.recording_format.extension,
                tz=self.tz,
                **episode
            )
            recording_file_path = self.tmp_path.joinpath(relative_file_path)
            create_folder(recording_file_path.parent)

            logging.info(f'Starting recording of "{relative_file_path}"')
            try:
                await record(
                    episode=episode,
                    recording_file_path=recording_file_path,
                    recording_input=self.recording_input,
                    recording_format=self.recording_format,
                    tz=self.tz
                )
            except Exception as exception:
                logging.error(f'Recorded of "{type(exception)} - {exception}" failed')
                continue
            logging.info(f'Recorded of "{relative_file_path}" completed')

            output_file_path = self.output_path.joinpath(relative_file_path)

            logging.debug(f'Moving file "{relative_file_path}" into output folder')
            move_file(recording_file_path, output_file_path)
            logging.debug(f'File "{relative_file_path}" was moved')

            logging.debug(f'Queueing episode submission: "{relative_file_path}"')
            file_type, file_encoding =  mimetypes.guess_type(output_file_path)
            file_lenght = output_file_path.stat().st_size
            data_to_submit = {
                'date': episode['issue_date'],
                'programme_id': episode['id'],
                'file_name': str(relative_file_path),
                'mime_type': file_type,
                'length': file_lenght,
            }
            self.episodes_to_submit.put_nowait(data_to_submit)

    async def run(self):
        try:
            await asyncio.gather(
                self.update_episodes_task,
                self.record_task,
                self.submit_episodes_task,
                # return_exceptions=True
            )
        except Exception as exception:
            logging.fatal(f'Execution finished due to: "{type(exception)} - {exception}"')
            self.terminate()

    def terminate(self):
        self.update_episodes_task.cancel()
        self.record_task.cancel()
        self.submit_episodes_task.cancel()
