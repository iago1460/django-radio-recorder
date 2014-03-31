#!/usr/bin/python

_version = ".1"



####################
# SET SOME VARIABLES
####################

# set the output directory for the audio files
output_directory = "streams/"

# encode to MP3 after recording each chunk?
encode_to_mp3 = True

# if encoding to MP3, delete the wav file afterwards?
delete_wav = False

# Length of recordings (choices are minute or hour).
# Set to "minute" if testing.
record_length = "hour"

# if using windows, where's lame.exe? If Linux, make sure lame is installed.
lame = "c:\\lame\\lame.exe"





import threading, time, os, sys, wave

import pyaudio

import process # a somewhat rare module that I use instead of subprocess. Can't find the download link, use radiovalencia.fm/dropbox/process.zip



# write to the log file and console
def write(message):

    # compose our time nice and purdy - January 3, 2010 - 3:52pm
    month = time.strftime("%B")
    day = time.strftime("%d").lstrip("0")
    year = time.strftime("%Y")
    hour = time.strftime("%I").lstrip("0")
    minute = time.strftime("%M")
    second = time.strftime("%S")
    ampm = time.strftime("%p").lower()
    timestamp = month + " " + day + ", " + year + " " + hour + ":" + minute + ":" + second + ampm
    
    if message == "SPACER": message = "\n"
    else: message = timestamp + ": " + message    

    print message

    # write it to a file
    fname = "sound_recorder_log.txt"

    try: contents = open(fname, "r").read()
    except: contents = ""

    # restrict the log file to X number of characters
    limit = 115000
    contents = contents[-limit:]

    message = contents + message + "\n"

    handle = open(fname, "w")
    handle.write(message)
    handle.close()





# get the filename of the wav file
def get_fname():

    # we want it to look like this: RadioValencia.11-06-06.0500.mp3    

    fname = time.strftime("RadioValencia.%y-%m-%d.%H%M") #%S
    fname = os.path.abspath(output_directory + "/" + fname + ".wav")

    try: os.makedirs( os.path.dirname(fname) )
    except: pass

    return fname




class MP3Encoder(threading.Thread):

    def __init__(self, wav_fname):
        self.wav_fname = wav_fname
        threading.Thread.__init__(self)

    def encode_to_mp3(self, wav_fname):

        wav_fname = os.path.abspath(wav_fname)

        options = "-b 192 -h --quiet" # add some more options for better quality? # ubuntu version doesn't support --priority 1 

        output_fname = os.path.splitext(wav_fname)[0] + ".mp3"

        options += " " + wav_fname + " " + output_fname

        if "linux" in sys.platform: command = "lame " + options
        else: command = lame + " " + options # Windows

        time.sleep(1)
        
        write("Starting to encode " + os.path.basename(wav_fname) + " to MP3...")

        start_time_local = time.time()
        
        try:
            p = process.ProcessOpen(command) # using the process module, somewhat rare, see comment up top for location
            p.wait(timeout=2100)
            output = p.stdout.read()
            total_time = time.time() - start_time_local
            total_time = round(total_time, 2)
            write("Done encoding to MP3 in " + str(total_time) + " seconds.")

            return output_fname

        except Exception, e:
            write("*** ERROR encoding " + os.path.basename(wav_fname) + " to mp3: " + str(e)) 

            return False
    

    def run(self):

        fname = self.encode_to_mp3(self.wav_fname)

        # delete the WAV file?
        if fname and delete_wav:
            try: os.unlink(self.wav_fname)
            except Exception, e:
                write("*** ERROR deleting " + os.path.basename(self.wav_fname) + ": " + str(e))




   
############################################################################
# START DOING STUFF
############################################################################


write("SPACER")
write("----- Sound Recorder launched -----")


##########################
# initialize our soundcard
##########################

p = pyaudio.PyAudio()

chunk = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100

# http://people.csail.mit.edu/hubert/pyaudio/docs/
# for non-default soundcard, set input_device_index
stream = p.open(format = FORMAT,
                channels = CHANNELS,
                rate = RATE,
                input = True,
                frames_per_buffer = chunk)




    
# keep track of all hours that have been recorded
all_recorded_hours = []
counter = 1

while True:

    # set the wave file's properties
    wav_fname = get_fname()

    #write("SPACER")
    write("Starting to record " + os.path.basename(wav_fname) + " (" + str(counter) + ")")
    wf = wave.open(wav_fname, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)

    # start recording
    start_time = time.time()

    error = False
    while True:

        try:
            data = stream.read(chunk)
            wf.writeframes(data)
        except Exception, e:
            write("*** ERROR writing wav chunk! " + str(e))
            error = True

        # for debugging, we can set "record_length" to a minute so we record smaller sections
        if record_length == "minute":
            current_minute = time.strftime("%S")
        else:
            current_minute = time.strftime("%M")
            
        #print current_minute

        unique_timestamp = time.strftime("%y-%m-%d %H:%M") # a unique timestamp for this hour (with seconds), so we can see if we've already recorded it

        # This is where we check to see if an hour has passed. If the minute is "00" and its the first time we've seen 00 for this hour, its safe to say its a new hour. Not the best method since there could be some microsecond overlap, but works for now. 

        # For testing, change the "00" to some approaching minute. For example if its 2:30, change it to "33" and it'll record until 2:33.

        # check to see if we should stop recording this file. 
        if (current_minute == "00" and unique_timestamp not in all_recorded_hours) or error:
            all_recorded_hours.append(unique_timestamp) # so we know we recorded this hour already
            break
        

    try: wf.close() # close the wav file
    except Exception, e: write("*** ERROR closing the wav file! " + str(e))
    
    write("Done recording " + os.path.basename(wav_fname))

    # send it to be encoded to MP3
    if encode_to_mp3:
        MP3Encoder(wav_fname).start()

    counter += 1


stream.close()
p.terminate()

write("Gar, we shouldn't have reached this point...")