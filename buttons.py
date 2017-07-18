import ConfigParser, os, gc 

import RPi.GPIO as GPIO

import mysql.connector

import pyinotify

import wave
import contextlib

import time

# import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

class ModHandler(pyinotify.ProcessEvent) :
    # evt has useful properties, including pathname
    def process_IN_MODIFY( self, event ) :
        print "IN_MODIFY"
        os.system("sudo pkill -9 pocketsphinx")
        UI.notifier.stop()
    def process_IN_CLOSE_WRITE( self, event ) :
        print "IN_CLOSE_WRITE"
        os.system("sudo pkill -9 pocketsphinx")
        UI.notifier.stop()

class OLED_UI( object ) :

    # oled RST pin
    RST_pin = 24

    # Input pins:
    R_pin = 5
    L_pin = 13
    C_pin = 26
    D_pin = 19
    U_pin = 6

    # CONSTANTS   
    KEYPAD = [
    [1,2,3],
    [4,5,6],
    [7,8,9],
    ["*",0,"#"]
    ]

    soundboard = [
    './sound/0001.wav',
    './sound/0002.wav',
    './sound/0001.wav',
    './sound/0002.wav',
    './sound/0001.wav',
    './sound/0002.wav',
    './sound/0001.wav',
    './sound/0002.wav',
    './sound/0001.wav',
    './sound/0002.wav',
    './sound/0001.wav',
    './sound/0002.wav',
    ]

    ROW         = [18,23,25,12]
    COLUMN      = [21,20,16]

    ui_state = 'history'
    current_line = 0
    list_len = 0
    previous_text = ''
    content = ''

    def __init__( self ) :
        self.initialize_config()
        self.initialize_GPIO()
        self.setup_GPIO_events()
        self.initialize_db()
        self.initialize_screen()
        self.get_keypad_key()
        self.initialize_notifier()

    def initialize_config( self ) :
        self.config = ConfigParser.ConfigParser()
        self.config.read('settings.cfg')

    def initialize_notifier( self ) :
        self.wm = pyinotify.WatchManager()
        s1 = pyinotify.Stats()
        #self.notifier = pyinotify.ThreadedNotifier( self.wm )
        self.notifier = pyinotify.ThreadedNotifier( self.wm, default_proc_fun=ModHandler(s1) )
        #self.notifier.loop()
        #self.notifier.start()
        self.wm.add_watch('./words.log', pyinotify.ALL_EVENTS, rec=True, auto_add=True)

    def initialize_GPIO( self ) :

        GPIO.setmode( GPIO.BCM ) 

        GPIO.setup( self.L_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP ) # Input with pull-up
        GPIO.setup( self.R_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP ) # Input with pull-up
        GPIO.setup( self.U_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP ) # Input with pull-up
        GPIO.setup( self.D_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP ) # Input with pull-up
        GPIO.setup( self.C_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP ) # Input with pull-up

    def setup_GPIO_events( self ) :
        #GPIO.add_event_detect(U_pin, GPIO.FALLING, callback=count_up, bouncetime=300)
        #GPIO.add_event_detect(D_pin, GPIO.FALLING, callback=count_down, bouncetime=300)

        GPIO.add_event_detect( self.U_pin, GPIO.FALLING, callback=self.direction_event, bouncetime=300 )
        GPIO.add_event_detect( self.D_pin, GPIO.FALLING, callback=self.direction_event, bouncetime=300 )

        GPIO.add_event_detect( self.L_pin, GPIO.FALLING, callback=self.direction_event, bouncetime=300 )
        GPIO.add_event_detect( self.R_pin, GPIO.FALLING, callback=self.direction_event, bouncetime=300 )

        GPIO.add_event_detect( self.C_pin, GPIO.FALLING, callback=self.direction_event, bouncetime=300 )

    def initialize_screen( self ) :

        try :
            disp = Adafruit_SSD1306.SSD1306_128_32( rst=self.RST_pin )
            self.disp = disp

            # Initialize library.
            self.disp.begin()

            # Clear display.
            self.disp.clear()
            self.disp.display()

            # Create blank image for drawing.
            # Make sure to create image with mode '1' for 1-bit color.
            self.width = self.disp.width
            self.height = self.disp.height
            self.image = Image.new( '1', ( self.width, self.height ) )

            # Get drawing object to draw on image.
            self.draw = ImageDraw.Draw( self.image )

            # Draw a black filled box to clear the image.
            self.draw.rectangle( ( 0, 0, self.width, self.height ), outline=0, fill=0 )
            x = 0
            top = -2

            # Load default font.
            self.font = ImageFont.load_default()

            self.update_ui_state( self.ui_state )

        except : 
            self.screen_disconnected = 'disconnected'
            print "no screen connected in pin #" + str( self.RST_pin )

    def initialize_db( self ) :
        config = self.config
        db_host = config.get('MYSQL', 'db_host')
        db_user = config.get('MYSQL', 'db_user')
        db_password = config.get('MYSQL', 'db_password')
        db_port = config.get('MYSQL', 'db_port')
        db_name = config.get('MYSQL', 'db_name')

        self.db = mysql.connector.connect(
            host=db_host,    # your host, usually localhost
            user=db_user,         # your username
            passwd=db_password,  # your password
            db=db_name,
            port=db_port)

    def full_text_search( self, text ) :
        # you must create a Cursor object. It will let
        #  you execute all the queries you need
        cursor = self.db.cursor( buffered=True )

        query = ( 
            "SELECT id, body, "
            "MATCH (body) AGAINST (%s IN NATURAL LANGUAGE MODE) AS score "
            "FROM dictionary "
            "WHERE MATCH (body) AGAINST (%s IN NATURAL LANGUAGE MODE) "
            "ORDER BY score DESC")

        # Use all the SQL you like
        cursor.execute(query, ( text, text ) )
        # Iterate through the result of curA
        result = cursor.fetchall()

        #for (body) in cur :
            #print body[0]

            # Commit the changes
            #self.db.commit()

        return result


    def get_ui_state( self ) :
        return self.ui_state

    def update_ui_state( self, state ) :
        # File based directional UI

        #if self.screen_disconnected :
        #    return

        # define default
        file = './history.log'

        if( 'history' == state ) : # initial state is history
            file = './history.log'
        elif( 'results' == state ) : # ASR results
            file = './words.log'

        with open( file ) as f :
            content = f.readlines()

        # reset previous list related settings when ui changes
        self.current_line = 0
        self.previous_text = ''
        self.content = [x.strip() for x in content]
        self.list_len = len( self.content )

        self.get_text_from_line( 0 )

    def get_current_line( self ) :
        return self.current_line

    def set_current_line( self, line ) :
        list_len = self.list_len

        if( line >= list_len ) : # if we've reached the end of the list, loop back around
            line = 0

        if ( line < 0 ) : # if we're trying to go before the beginning of our list, jump to the end
            line = list_len - 1

        self.current_line = line
        return line

    def count_up( self ) :
        current_line = self.get_current_line()
        new_line = self.set_current_line( current_line + 1 )

        print 'count up: '
        print new_line

        self.get_text_from_line( new_line )

    def count_down( self ) :
        current_line = self.get_current_line()
        new_line = self.set_current_line( current_line - 1 )

        print 'count down: '
        print new_line

        self.get_text_from_line( new_line )

    def direction_event( self, obj ) :
        current_line = self.get_current_line()
        new_line = current_line
        ui_state = self.ui_state
        
        if self.U_pin == obj :
            print "up"
            new_line = current_line + 1
        elif self.D_pin == obj :
            print "down"
            new_line = current_line - 1
        
        if self.U_pin == obj or self.D_pin == obj :
            line = self.set_current_line( new_line )
            self.get_text_from_line( line )
            print line


        if self.R_pin == obj :
            print "right"

        if self.L_pin == obj :
            print "left"

        if self.L_pin == obj or self.R_pin == obj :
            if self.R_pin == obj : # clicked forward, regardless of UI state, play current line sound
                # @TODO: play sound
                self.update_ui_state( 'history' ) # reset interface
            elif 'result' == ui_state and self.L_pin == obj : # clicked back on result line, return to history
                self.update_ui_state( 'history' ) # reset interface

        if 'recording' != ui_state and self.C_pin == obj : # Pushed down on dpad, run ASR
            self.asr_event()

    def asr_event( self ) :
        self.update_ui_state( 'recording' )
        self.start_asr()

    def start_asr( self ) :
        # self.notifier.loop()
        os.system("sudo pocketsphinx_continuous -lm ./corpus/0720.lm -dict ./corpus/0720.dic -samprate 16000 -inmic yes -adcdev plughw:1,0 -logfn /dev/null | tee ./words.log &")
        self.notifier.start()

    def get_text_from_input( self, text, x=0, top=-2 ) :

        self.draw.rectangle( ( 0, 0, self.width, self.height ), outline=0, fill=0 )
        self.draw.text( (x, top), str( text ),  font=self.font, fill=255 )

        print text
        return text

    def get_text_from_line( self, line, x=0, top=-2 ) :
        new_line = self.set_current_line( line )

        draw = self.draw
        text = self.content[ new_line ]
        draw.rectangle( (0, 0, self.width, self.height ), outline=0, fill=0 )
        draw.text( (x, top ), str( text ),  font=self.font, fill=255 )

        print text
        return text

    def play_sound( self, path ) :
        os.system( 'play ' + path + ' &' )

    def play_sound_from_text( self, text ) :
        result = self.full_text_search( text )
        count = len( result )        
        print count
        print result[0][1]
        return

        for row in result :
            print body[0]
        #os.system( 'play ' + path + ' &' )
        print "done"
        return

    def get_sound_duration( self, path ) :
        with contextlib.closing( wave.open( path, 'r' ) ) as f :
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)
            return duration

    def get_keypad_key( self ) :

        # Set all columns as output low
        for j in range( len( self.COLUMN ) ) :
            GPIO.setup( self.COLUMN[j], GPIO.OUT )
            GPIO.output( self.COLUMN[j], GPIO.LOW )

        # Set all rows as input
        for i in range( len( self.ROW ) ) :
            GPIO.setup( self.ROW[i], GPIO.IN, pull_up_down=GPIO.PUD_UP )

        # Scan rows for pushed key/button
        # A valid key press should set "rowVal"  between 0 and 3.
        rowVal = -1
        for i in range( len( self.ROW ) ) :
            tmpRead = GPIO.input( self.ROW[i] )
            if tmpRead == 0:
                rowVal = i

        # if rowVal is not 0 thru 3 then no button was pressed and we can exit
        if rowVal < 0 or rowVal > 3:
            self.reinitialize_keypad()
            return

        # Convert columns to input
        for j in range( len( self.COLUMN ) ) :
                GPIO.setup( self.COLUMN[j], GPIO.IN, pull_up_down=GPIO.PUD_DOWN )

        # Switch the i-th row found from scan to output
        GPIO.setup( self.ROW[ rowVal ], GPIO.OUT )
        GPIO.output( self.ROW[ rowVal ], GPIO.HIGH )

        # Scan columns for still-pushed key/button
        # A valid key press should set "colVal"  between 0 and 2.
        colVal = -1
        for j in range( len( self.COLUMN ) ) :
            tmpRead = GPIO.input( self.COLUMN[j] )
            if tmpRead == 1 :
                colVal = j

        # if colVal is not 0 thru 2 then no button was pressed and we can exit
        if colVal <0 or colVal >2:
            self.reinitialize_keypad()
            return

        # Return the value of the key pressed
        self.reinitialize_keypad()
        return self.KEYPAD[ rowVal ][ colVal ]

    def reinitialize_keypad( self ) :
        # Reinitialize all rows and columns as input at exit
        for i in range( len( self.ROW ) ) :
            GPIO.setup( self.ROW[i], GPIO.IN, pull_up_down=GPIO.PUD_UP ) 
        for j in range( len( self.COLUMN ) ) :
            GPIO.setup( self.COLUMN[j], GPIO.IN, pull_up_down=GPIO.PUD_UP )

UI = OLED_UI()

UI.play_sound_from_text("MORTY")

try :
    digit = None
    while 1 :
        # Display image.
        UI.disp.image( UI.image )

        sleep = .25
        digit = UI.get_keypad_key()

        if digit != None :
            print digit
            UI.play_sound( UI.soundboard[digit] )
            UI.update_ui_state( 'history' ) # reset interface
            sleep = UI.get_sound_duration( UI.soundboard[digit] )
            digit = None

        UI.disp.display()
        time.sleep( sleep )

except KeyboardInterrupt: 
    GPIO.cleanup()
    UI.notifier.stop()
    UI.db.commit()
    gc.collect()
