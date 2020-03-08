import asyncio
import logging
import shlex
import subprocess
from enum import auto, Enum
from radioco_recorder.const import LAME_MP3, OGGENC, JACK_CAPTURE, ARECORD, MIN_WAIT_TIME, ATTRIBUTION
from radioco_recorder.utils import datetime_now_tz, radioco_str_to_dt


class RecorderError(Exception):

    def __init__(self, error_code):
        self.error_code = error_code


class RecordingFormat(Enum):
    MP3 = auto()
    OGG = auto()

    @property
    def extension(self):
        if self == RecordingFormat.MP3:
            return 'mp3'
        return 'ogg'

    @property
    def command(self):
        if self == RecordingFormat.MP3:
            return LAME_MP3
        return OGGENC


class RecordingInput(Enum):
    JACK = auto()
    ALSA = auto()

    @property
    def command(self):
        if self == RecordingInput.JACK:
            return JACK_CAPTURE
        return ARECORD


async def record(episode, recording_file_path, recording_input, recording_format, tz):
    episode_start_dt = radioco_str_to_dt(episode["start"], tz)
    seconds_missed = int((datetime_now_tz() - episode_start_dt).total_seconds())
    episode_duration = int(episode['duration']) - seconds_missed
    if seconds_missed:
        logging.warning(f'Recording started {seconds_missed} seconds late, will record now for {episode_duration} seconds')

    command_args = {
        **episode,
        'file_path': recording_file_path,
        'duration': episode_duration,
    }
    recorder_command = prepare_comand(
        command=recording_input.command, **command_args
    )
    encoder_command = prepare_comand(
        command=recording_format.command, **command_args
    )
    recorder_process = subprocess.Popen(recorder_command, stdout=subprocess.PIPE)
    encoder_process = subprocess.Popen(encoder_command, stdin=recorder_process.stdout)

    try:
        while True:
            encoder_return_code = encoder_process.poll()
            recorder_return_code = recorder_process.poll()

            if recorder_return_code is not None:
                if recorder_return_code != 0:
                    logging.error(f'Recorded failed with error code {recorder_return_code}')
                    raise RecorderError(-recorder_return_code)
                logging.info(f'Recorded process ended successfully')
                encoder_process.wait()
                break
            elif encoder_command is not None:
                logging.error(f'Encoder process failed with error code {encoder_return_code}')
                recorder_process.terminate()
                raise RecorderError(-encoder_return_code)

            await asyncio.sleep(MIN_WAIT_TIME)
    except asyncio.CancelledError:
        logging.info('Terminating recording')
        recorder_process.terminate()
        encoder_process.terminate()
        raise


def prepare_comand(command, **format_params):
    return [
        row.format(
            attribution=ATTRIBUTION,
            **format_params
        )
        for row in shlex.split(command)
    ]
