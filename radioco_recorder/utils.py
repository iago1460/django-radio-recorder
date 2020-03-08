import datetime

from radioco_recorder.const import RADIOCO_DATEFMT


def index_episodes(episodes, tz):
    """
    Prepare episodes for easier time checking in next_episode_to_record()
    :param episodes:
    :return: [ ((start_dt, end_dt), episode) ]
    """
    offset_seconds = 5  # just in case the recorder command finish earlier
    return [
        (
            (
                radioco_str_to_dt(episode["start"], tz),
                radioco_str_to_dt(episode["start"], tz) + datetime.timedelta(
                    seconds=max(int(episode["duration"]) - offset_seconds, 0)
                )
            ),
            episode
        )
        for episode in episodes
    ]


def datetime_now_tz():
    # https://docs.python.org/3/library/datetime.html#datetime.datetime.utcnow
    return datetime.datetime.now(datetime.timezone.utc)


def radioco_str_to_dt(dt_str, tz):
    return datetime.datetime.strptime(dt_str, RADIOCO_DATEFMT).replace(tzinfo=tz)
