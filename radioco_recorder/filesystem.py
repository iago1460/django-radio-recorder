import os
import shutil
from pathlib import Path

from radioco_recorder.utils import radioco_str_to_dt


def generate_file_path(file_path_format, file_extension, tz, **episode):
    issue_dt = radioco_str_to_dt(episode['issue_date'], tz)
    strftime_format = file_path_format.format(
        file_extension=file_extension,
        **episode
    )
    return Path(issue_dt.strftime(strftime_format))


def create_folder(path):
    if not path.exists():
        os.makedirs(path)


def move_file(src_file, dst_file):
    create_folder(dst_file.parent)
    shutil.move(src_file, dst_file)