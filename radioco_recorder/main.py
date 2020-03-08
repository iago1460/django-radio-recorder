# Radioco - Broadcasting Radio Recording Scheduling system.
# Copyright (C) 2020  Iago Veloso Abalo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import argparse
import asyncio
import datetime
import logging
import sys
from argparse import RawTextHelpFormatter
from pathlib import Path

from radioco_recorder.app import RecorderApp
from radioco_recorder.const import LOG_FORMAT, LOG_DATEFMT
from radioco_recorder.recorder import RecordingInput, RecordingFormat
from radioco_recorder import __version__


from dateutil import tz as dateutil_tz


def PathType(path):
    if path:
        return Path(path).resolve(strict=True)
    return None


def TimezoneType(timezone):
    if timezone:
        return dateutil_tz.gettz(timezone)
    return None


# async def run():
async def main():
    parser = argparse.ArgumentParser(
        formatter_class=RawTextHelpFormatter,
        description=
        "RadioCo utility for recording podcasts.\n"
        "By default it will use arecord (recorder for ALSA soundcard driver) and oggenc to encode audio into the Ogg Vorbis format."
        "Example usage:\n"
        "python3 -m recorder --flag ..."
    )
    parser.add_argument(
        '--jack-input',
        help="Records audio signal from jack",
        dest='jack',
        action='store_true',
        default=False
    )
    parser.add_argument(
        '--mp3',
        help="Generates mp3",
        dest='mp3',
        action='store_true',
        default=False
    )
    parser.add_argument(
        '--radioco-endpoint',
        help="RadioCo Endpoint, e.g. https://radioco.org/",
        dest='radioco_endpoint',
        type=str,
        required=True,
    )
    parser.add_argument(
        '--radioco-token',
        help="RadioCo Token",
        dest='radioco_token',
        type=str,
        required=True,
    )
    parser.add_argument(
        '--radioco-tz',
        help="Timezone (needs to match RadioCo server) e.g. Europe/Madrid",
        dest='tz',
        type=TimezoneType,
        required=False,
        default=dateutil_tz.gettz(),
    )
    parser.add_argument(
        '--tmp',
        help="Path to the temporal directory where recording will be in in progress.",
        dest='tmp_path',
        type=PathType,
        required=True,
    )
    parser.add_argument(
        '--language',
        help="Metadata language e.g. es",
        dest='language',
        type=str,
        required=False,
        default='en'
    )
    parser.add_argument(
        '--output',
        help="Path to the output directory where recorders will appear once are completed.",
        dest='output_path',
        type=PathType,
        required=True,
    )
    parser.add_argument(
        '--verbose',
        help='Makes verbose during the operation. Useful for debugging and seeing what is going on "under the hood".',
        dest='verbose',
        action='store_true',
        default=False
    )
    parser.add_argument(
        '--format',
        help=
        "Customize how to structure the recorded files e.g: '%%Y/%%m/%%d/%%Y-%%m-%%d_%%H-%%M-%%S_{programme_name}.{file_extension}'\n"
        "All python strftime format codes are supported as well as {file_extension}, {programme_name}, {album}, {author}, {genre}, {id}",
        dest='file_path_format',
        type=str,
        required=False,
        default='%Y-%m-%d_%H-%M-%S_{programme_name}.{file_extension}'
    )
    args = parser.parse_args()

    logging_level = logging.INFO
    if args.verbose:
        logging_level = logging.DEBUG
    logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATEFMT, stream=sys.stdout, level=logging_level)

    logging.debug(f'Input args: {vars(args)}')

    recording_input = RecordingInput.ALSA
    if args.jack:
        recording_input = RecordingInput.JACK

    recording_format = RecordingFormat.OGG
    if args.mp3:
        recording_format = RecordingFormat.MP3

    radioco_endpoint = args.radioco_endpoint.rstrip('/')

    from dateutil.tz import tzlocal
    local_dt = datetime.datetime.now(tzlocal())
    logging.info(
        '\n'.join(
            (
                f'Starting RadioCo recorder version {__version__}',
                f'Current TZ: {local_dt.tzname()}',
                f'Current date: {local_dt.isoformat()}',
                f'RadioCo Server: {radioco_endpoint}',
                f'RadioCo TZ: {args.tz}',
                f'Store location: {args.output_path}',
                f'Temporal Store location: {args.tmp_path}',
                f'Recorder format: {recording_format.extension}',
                '------------------------------------------------',
            )
        )
    )

    recorder_app = RecorderApp(
        radioco_endpoint=radioco_endpoint,
        radioco_token=args.radioco_token,
        tz=args.tz,
        language=args.language,
        file_path_format=args.file_path_format,
        tmp_path=args.tmp_path,
        output_path=args.output_path,
        recording_format=recording_format,
        recording_input=recording_input
    )

    await recorder_app.run()


if __name__ == "__main__":
    asyncio.run(main())

