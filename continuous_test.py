#!/usr/bin/python

# pocketsphinx_continuous -lm ./corpus/0720.lm -dict ./corpus/0720.dic -samprate 16000/8000/48000 -adcdev plughw:1,0 -inmic yes 2> ./debug.log | tee ./words.log &

from os import environ, path

from pocketsphinx.pocketsphinx import *
from sphinxbase.sphinxbase import *

MODELDIR = "../../../model"
DATADIR = "./"

config = Decoder.default_config()

config.set_string('-lm', './corpus/0720.lm')
config.set_string('-dict', './corpus/0720.dic')
config.set_string('-logfn', '/dev/null')
#config.set_string('-adcdev', 'plughw:1,0')
#config.set_string('-inmic', 'yes')
decoder = Decoder(config)

stream = open(path.join(DATADIR, 'goforward.raw'), 'rb')
#stream = open('10001-90210-01803.wav', 'rb')

in_speech_bf = False
decoder.start_utt()
while True:
    buf = stream.read(1024)
    if buf:
        decoder.process_raw(buf, False, False)
        if decoder.get_in_speech() != in_speech_bf:
            in_speech_bf = decoder.get_in_speech()
            if not in_speech_bf:
                decoder.end_utt()
                print 'Result:', decoder.hyp().hypstr
                decoder.start_utt()
    else:
        break
decoder.end_utt()
