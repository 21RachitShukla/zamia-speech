#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Copyright 2014, 2018 Guenter Bartsch
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import sys
import os
import codecs
import traceback
import random
import datetime
import logging
import wave, struct, array

import numpy as np

from optparse           import OptionParser
# from speech_transcripts import Transcripts
# from speech_lexicon     import Lexicon
from nltools            import misc
from nltools.vad        import VAD, BUFFER_DURATION

#
# - convert audio to wav
# - segment 
#

random.seed (42)

# silence: anything < 20% of avg volume
SILENCE_THRESH     = 0.2

SAMPLE_RATE        = 16000
AGGRESSIVENESS     = 2
FRAMES_PER_BUFFER  = SAMPLE_RATE * BUFFER_DURATION / 1000

MIN_UTT_LENGTH     = 1   # seconds
MAX_UTT_LENGTH     = 25  # seconds
MAX_UTT_GAP        = 0.2 # seconds

# debug purposes only, set to 0 to disable debug limit
#DEBUG_LENGTH       = 5000000
DEBUG_LENGTH       = 0

def gen_dirname (rstr):

    global speaker

    today = datetime.date.today()
   
    # rstr = '%c%c%c' % (random.randint(97,122),random.randint(97,122),random.randint(97,122))
 
    ds = today.strftime ('%Y%m%d')

    dir_name = '%s-%s-%s' % (speaker, ds, rstr)

    #print 'dir_name: %s' % dir_name

    return dir_name

PROC_TITLE = 'abook-segment'

#
# init terminal
#

misc.init_app (PROC_TITLE)

#
# config
#

config = misc.load_config('.speechrc')

vf_login    = config.get("speech", "vf_login")

#
# command line
#

parser = OptionParser("usage: %prog [options] foo.wav")

parser.add_option("-s", "--speaker", dest="speaker", type = "str", default=vf_login,
                   help="speaker (default: %s)" % vf_login)
parser.add_option("-v", "--verbose", action="store_true", dest="verbose", 
                  help="enable debug output")

(options, args) = parser.parse_args()

if options.verbose:
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.WARNING)
else:
    logging.basicConfig(level=logging.INFO)

if len(args) != 1:
    parser.print_usage()
    sys.exit(1)

inputfn    = args[0]
speaker    = options.speaker
tmpwav16fn = '/tmp/tmp16_%08x.wav' % os.getpid()

#
# segment audio
#

#
# VAD
#

vad = VAD(aggressiveness = AGGRESSIVENESS, 
          sample_rate    = SAMPLE_RATE,
          min_utt_length = MIN_UTT_LENGTH,
          max_utt_length = MAX_UTT_LENGTH,
          max_utt_gap    = MAX_UTT_GAP)

# generate dir name

rstr = inputfn[0:len(inputfn)-4]
dir_path = gen_dirname(rstr)

logging.info ('dir_path: %s' % dir_path)

#
# generate skeleton
#

os.system ('rm -rf %s' % (dir_path))
os.system ('mkdir %s' % (dir_path))
os.system ('mkdir %s/etc' % (dir_path))
os.system ('mkdir %s/wav' % (dir_path))

#
# convert audio to 16kHz mono
#

cmd = "sox %s -r 16000 -c 1 %s" % (inputfn, tmpwav16fn)
logging.info(cmd)

os.system (cmd)

#
# read all samples into memory so we have random access to them
# when we're looking for cut-points
#

wavf = wave.open(tmpwav16fn, 'r')
length = wavf.getnframes()

if DEBUG_LENGTH>0 and length >DEBUG_LENGTH:
    length = DEBUG_LENGTH

samples = []
avg = 0.0

# print "Reading %6d/%6d samples from %s..." % (len(samples), length, tmpwav16fn),

i          = 0
offset     = 0
cur_buffer = []
wavoutcnt  = 0

while offset < length:

    wd = wavf.readframes(FRAMES_PER_BUFFER)
    i += 1
    offset = i * FRAMES_PER_BUFFER

    try:

        samples = np.fromstring(wd, dtype=np.int16)

        # A = array.array('h')
        # A.fromstring(wd)
        # samples = A.tolist()

        # samples = struct.unpack("<h", wd)

        audio, finalize = vad.process_audio(samples)

        # logging.info ('len(cur_buffer)=%5d finalize: %s' % (len(cur_buffer), finalize))

        # logging.info ('audio: %s' % audio)
        # import pdb; pdb.set_trace()

        if audio:
            cur_buffer.extend(audio)

        if finalize:

            wavoutfn  = "%s/wav/de10-%03d.wav" % (dir_path, wavoutcnt)

            wavoutf   = wave.open(wavoutfn, 'w')
            wavoutf.setparams((1, 2, 16000, 0, "NONE", "not compressed"))

            A = array.array('h', cur_buffer)
            wd = A.tostring()

            # for sample in cur_buffer:
            #     wd = struct.pack("<h", sample)
            #     wavoutf.writeframes(wd)
            wavoutf.writeframes(wd)
            wavoutf.close()
            wavoutcnt += 1

            seconds = float(len(cur_buffer)) / float(SAMPLE_RATE)
            logging.info ('segment %s written, %5.1fs.' % (wavoutfn, seconds))

            cur_buffer = []

        # if i % 1000 == 0:
        #     p = offset * 100 / length
        #     print "\rReading %9d/%9d %3d%% samples from %s..." % (offset, length, p, tmpwav16fn),

    except:
        logging.error('EXCEPTION CAUGHT %s' % traceback.format_exc())

sys.exit(0)

avg = int(avg/length)

print "\ndone. Read %d samples, avg: %d" % (len(samples), avg)

silence_thresh = int(SILENCE_THRESH * avg + 1)

cur_pos   = 0
wavoutcnt = 0

while cur_pos < length:

    cut_pos             = cur_pos + MIN_SEGMENT_LENGTH
    best_silence_pos    = cut_pos 
    best_silence_length = 0

    cur_silence_pos     = cut_pos
    cur_silence_length  = 0

    max_pos             = cur_pos + MAX_SEGMENT_LENGTH
    if max_pos > length:
        max_pos = length

    #print "cur_pos: %d, max_pos: %d, best_silence_pos: %d" % (cur_pos, max_pos, best_silence_pos)

    while cut_pos < max_pos:

        sample  = samples[cut_pos]
        cut_pos += 1

        if sample < silence_thresh:
            cur_silence_length += 1
    
        else:

            if cur_silence_length > best_silence_length:
                best_silence_length = cur_silence_length
                best_silence_pos    = cur_silence_pos

            cur_silence_length = 0
            cur_silence_pos    = cut_pos

    print "Segment detected: %5ds -> %5ds (len: %2ds, silence: %5d samples)" % (cur_pos / SAMPLE_RATE, best_silence_pos / SAMPLE_RATE, (best_silence_pos - cur_pos) / SAMPLE_RATE, best_silence_length)

    #print "best_silence_pos: %d" % (best_silence_pos)


    csp = best_silence_pos if best_silence_pos < length else length

    cur_voice_len = 0
    for i in range (cur_pos, csp):
        if samples[i] >= silence_thresh:
            cur_voice_len += 1

    if cur_voice_len >= MIN_VOICE_LENGTH:
        wavoutfn  = "%s/wav/de10-%03d.wav" % (dir_path, wavoutcnt)
        #wavoutfn  = "/tmp/de10-%03d.wav" % (wavoutcnt)

        wavoutf   = wave.open(wavoutfn, 'w')
        wavoutf.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        for i in range (cur_pos, csp):
            wd = struct.pack("<h", samples[i])
            wavoutf.writeframes(wd)
        wavoutf.close()
        wavoutcnt += 1

        print "%s written." % wavoutfn
    else:
        print "Voice content too short (%5d samples), wav file not written." % (cur_voice_len)

    cur_pos = best_silence_pos + 1


# cleanup
#
os.system ('rm %s' % tmpwavfn)
os.system ('rm %s' % tmpwav16fn)

