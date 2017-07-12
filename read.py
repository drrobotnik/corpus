#!/usr/bin/python

import os
import time
 
i=0

print "listening"
 
while i != 1 :
    infile = open('./words.log', 'r')
 
    for line in infile:
	if line.find("SHE'S AN IDIOT") != -1 :
            #os.system("echo 0 > /sys/class/gpio/gpio17/value")
            os.system("true > ./words.log")
            print "rick is calling the lady who walks her cat on a leash an idiot"
            #os.system("festival -b '(SayText "Green led off")'")
	if line.find("BREED") != -1 :
            #os.system("echo 1 > /sys/class/gpio/gpio17/value")
            os.system("true > ./words.log")
            print "green on"
            #os.system("festival -b '(SayText "Green led ON")'")
	if line.find("RED OFF") != -1 :
            #os.system("echo 0 > /sys/class/gpio/gpio2/value")
            os.system("true > ./words.log")
            print "red off"
            #os.system("festival -b '(SayText "Red led Off")'")
	if line.find("RED OK") != -1 :
            #os.system("echo 1 > /sys/class/gpio/gpio2/value")
            os.system("true > ./words.log")
            print "red on"
            #os.system("festival -b '(SayText "Red led ON")'")
	if line.find("TEXTING") != -1 :
            #os.system("echo 1 > /sys/class/gpio/gpio2/value")
            #os.system("echo 1 > /sys/class/gpio/gpio17/value")
            print "testing"
            os.system("true > ./words.log")
            #os.system("festival -b '(SayText "Green and red led ON")'")
	if line.find("EXIT") != -1 :
            os.system("sudo pkill -9 pocketsphinx")
            os.system("sudo pkill -9 read.py")
            os.system("true > ./words.log")
            #os.system("festival -b '(SayText "Goodbye!")'")
            i=1
 
            infile.close()
            time.sleep(.25)
