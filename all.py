#!/usr/bin/python

import os, subprocess, time

#import RPi.GPIO as GPIO
#OUT_PIN = 17
#GPIO.setmode(GPIO.BCM)
#GPIO.setup(OUT_PIN, GPIO.OUT)

#os.system("rm ./words.log")

#os.system("./shut.py &")
os.system("sudo pocketsphinx_continuous -lm ./corpus/0720.lm -dict ./corpus/0720.dic -samprate 16000/8000/48000 -inmic yes -adcdev plughw:1,0 2>./debug.log | tee ./words.log &")
#os.system("sudo pocketsphinx_continuous -lm ./corpus/0720.lm -dict ./corpus/0720.dic -samprate 16000/8000/48000 -inmic yes 2>./debug.log | tee ./words.log &")
#os.system("sudo pocketsphinx_continuous -lm 3906.lm -dict 3906.dic > capture.txt -samprate 16000/8000/48000 &")
os.system("./read.py &")

import signal
import sys
def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    os.system("sudo pkill -9 pocketsphinx")
    os.system("sudo pkill -9 read.py")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.pause()
