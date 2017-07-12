import os
import RPi.GPIO as GPIO

import time

# import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

class OLED_UI( object ) :

    # oled RST pin
    RST_pin = 24

    # Input pins:
    L_pin = 5
    R_pin = 13
    C_pin = 26
    U_pin = 19
    D_pin = 6

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

    def __init__( self) :
        self.initialize_GPIO()
        self.setup_GPIO_events()
        self.initialize_screen()
        self.get_keypad_key()

        ui_state = self.ui_state
        self.update_ui_state( ui_state )

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

    def initialize_screen( self ) :

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

    def get_ui_state( self ) :
        return self.ui_state

    def update_ui_state( self, state ) :
        # File based directional UI

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

    def get_current_line( self ) :
        return self.current_line

    def set_current_line( self, line ) :
        list_len = self.list_len

        if( line >= list_len ) :
            line = list_len

        if ( line <= 0 ) :
            line = 0

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
        
        if self.U_pin == obj :
            new_line = current_line + 1
        elif self.D_pin == obj :
            new_line = current_line - 1
        
        if self.U_pin == obj or self.D_pin == obj :
            new_line = self.set_current_line( new_line )
            self.get_text_from_line( new_line )
            print new_line

        if self.L_pin == obj or self.R_pin == obj :
            ui_state = self.ui_state
            if self.R_pin : # clicked forward, regardless of UI state, play current line sound
                # @TODO: play sound
                self.update_ui_state( 'history' ) # reset interface
            elif 'result' == ui_state and self.L_Pin : # clicked back on result line, return to history
                self.update_ui_state( 'history' ) # reset interface


    def get_text_from_input( text, x=0, top=-2 ) :

        self.draw.rectangle( ( 0, 0, self.width, self.height ), outline=0, fill=0 )
        self.draw.text( (x, top), str( text ),  font=font, fill=255 )

        print text
        return text

    def get_text_from_line( self, line, x=0, top=-2 ) :
        draw = self.draw
        text = self.content[ line ]
        draw.rectangle( (0, 0, self.width, self.height ), outline=0, fill=0 )
        draw.text( (x, top ), str( text ),  font=self.font, fill=255 )

        print text
        return text

    def play_sound( self, path ) :
        os.system('play ' + path + ' &')

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

try :
    digit = None
    while 1 :
        if not GPIO.input( UI.C_pin ) :
            catImage = Image.open( './happycat_oled_32.ppm' ).convert( '1' )
            UI.disp.image( catImage )
        else :
            # Display image.
            UI.disp.image( UI.image )

        
        digit = UI.get_keypad_key()

        if digit != None :
            print digit
            UI.play_sound( UI.sound[digit] )
            UI.update_ui_state( 'history' ) # reset interface
            digit = None


        UI.disp.display()
        time.sleep( .01 )

except KeyboardInterrupt: 
    GPIO.cleanup()
