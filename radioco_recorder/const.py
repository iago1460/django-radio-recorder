ATTRIBUTION = 'Made by RadioCo www.RadioCo.org'

LOG_FORMAT = '%(asctime)s %(levelname)s : %(message)s'

LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'


MIN_WAIT_TIME = 0.01

RETRY_TIME = 45

REQUEST_TIMEOUT = 15


# RadioCo
RADIOCO_DATEFMT='%Y-%m-%d %H-%M-%S'

# Recording
# https://github.com/kmatheussen/jack_capture
JACK_CAPTURE = 'jack_capture --daemon --channels 2 --port stereo_tool:out_* --write-to-stdout --recording-time {duration}'

# https://linux.die.net/man/1/arecord
ARECORD = 'arecord -q --buffer-size=192000 -f S16_LE -c 2 -r 48000 -t raw -d {duration}'

# https://svn.code.sf.net/p/lame/svn/trunk/lame/USAGE
LAME_MP3 = 'lame -r -b 192 --cbr --bitwidth 16 -s 44.1 --tt "{author}" --ta "{author}" --tl "{album}" --tn "{track}" --tg "{genre}" --tc "{attribution}" - "{file_path}'

# https://linux.die.net/man/1/oggenc
OGGENC = 'oggenc - -r -B 16 -C 2 -R 48000 -q 3 -o "{file_path}"'
# OGGENC = 'oggenc - -r -B 16 -C 2 -R 48000 -q 3 --title {title} --artist {author} --album {album} --tracknum {track} --genre {genre} -c comment={attribution} -o "{file_path}"'

