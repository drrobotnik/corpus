# PocketSphinx ASR Corpus Database Utility

### Background

PocketSphinx is an Automatic Speech Recognition (ASR) software similar to Google Voice, Alexa, Siri, etc.. ASR's in general require you to build out a corpus which includes your phoneme dictionary of words, a language model, sentences and vocab. Generally speaking the bigger the dictionary source of words, the better. The corpus provided was generated via open subtites from Rick and Morty. You can replace the default dictionary by generating your own corpus. Carnegie Mellon University provides a tool to generate these required files:
http://www.speech.cs.cmu.edu/tools/lmtool-new.html


### What?

This project is a proof of concept showing ASR being used to say a target phrase and have the closest matching audio played back. Consider it an ASR soundboard. The ASR does not know which soundfile has the matching phrase, so this utility provides the last step to automate this association.

### How?

Once you have generated your corpus you'll need to create a mysql database. `corpus.sql` is provided to get this off the ground. Next you'll run the command line utility `php ./corpus.php`.

There are two options. First you'll need to run `[1] Update Corpus`, just type 1 and hit enter to run through your audio files. You'll hear the audio play, the ASR will make it's best attempt to understand the audio and generate the text. If the text is correct, hit enter to move to the next file. If it's not correct, type the correct text and hit enter to move on to the next file. Once you're done Ctrl-C out of the utility, and re-run. This time you can hit Enter for the default option `[0] Dictate`.

In order to recognize speech automatically pocketsphinx must be running in a separate process. The following command runs using the included corpus writing the result to words.log.

`pocketsphinx_continuous -hmm /usr/local/share/pocketsphinx/model/en-us/en-us/ -lm ./corpus/0720.lm -dict ./corpus/0720.dic -samprate 16000/8000/48000 -inmic yes 2>./debug.log | tee ./words.log`


### Requirements / Dependencies

Sox, CMU PocketSphinx, PHP, MYSQL