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

    ui_state = 'history'
    current_line = 0
    list_len = 0
    previous_text = ''
    content = ''

    def __init__( self ) :
        self.initialize_GPIO()
        self.setup_GPIO_events()
        self.initialize_screen()
        ui_state = self.ui_state
        self.update_ui_state( ui_state )

    def initialize_gpio() :

        GPIO.setmode( GPIO.BCM ) 

        GPIO.setup( self.L_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP ) # Input with pull-up
        GPIO.setup( self.R_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP ) # Input with pull-up
        GPIO.setup( self.U_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP ) # Input with pull-up
        GPIO.setup( self.D_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP ) # Input with pull-up
        GPIO.setup( self.C_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP ) # Input with pull-up

    def setup_GPIO_events() :
        #GPIO.add_event_detect(U_pin, GPIO.FALLING, callback=count_up, bouncetime=300)
        #GPIO.add_event_detect(D_pin, GPIO.FALLING, callback=count_down, bouncetime=300)

        GPIO.add_event_detect(self.U_pin, GPIO.FALLING, callback=direction_event, bouncetime=300)
        GPIO.add_event_detect(self.D_pin, GPIO.FALLING, callback=direction_event, bouncetime=300)

        GPIO.add_event_detect(self.L_pin, GPIO.FALLING, callback=direction_event, bouncetime=300)
        GPIO.add_event_detect(self.R_pin, GPIO.FALLING, callback=direction_event, bouncetime=300)

    def initialize_screen() :

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
        self.draw.rectangle( (0, 0, self.width, self.height ), outline=0, fill=0 )
        x = 0
        top = -2

        # Load default font.
        self.font = ImageFont.load_default()

    def get_ui_state() :
        return self.ui_state

    def update_ui_state( state ) :
        # File based directional UI

        # define default
        file = '/home/pi/history.log'

        if( 'history' == state ) : # initial state is history
            file = '/home/pi/history.log'
        elif( 'results' == state ) : # ASR results
            file = '/home/pi/words.log'

        with open( file ) as f :
            content = f.readlines()
        
        # reset previous list related settings when ui changes
        self.current_line = 0
        self.previous_text = ''
        self.content = [x.strip() for x in content]
        self.list_len = len(content)

    def get_current_line() :
        return self.current_line

    def set_current_line( line ) :
        list_len = self.list_len

        if( line >= list_len ) :
            line = list_len

        if ( line <= 0 ) :
            line = 0

        self.current_line = line
        return current_line

    def count_up( obj ) :
        current_line = self.get_current_line()
        new_line = self.set_current_line( current_line + 1 )

        print 'count up: '
        print new_line
        
        self.get_text_from_line( new_line )

    def count_down( obj ) :
        current_line = self.get_current_line()
        new_line = self.set_current_line( current_line - 1 )

        print 'count down: '
        print new_line
        
        self.get_text_from_line( new_line )

    def direction_event( obj ) :
        current_line = self.get_current_line()

        print 'direction_event: '
        print obj
        
        if U_pin == obj :
            new_line = current_line + 1
        elif D_pin == obj :
            new_line = current_line - 1
        
        if U_pin == obj or D_pin == obj :
            new_line = self.set_current_line( new_line )
            self.get_text_from_line( new_line )
            print new_line

        if L_pin == obj or R_pin == obj :
            ui_state = self.ui_state
            if R_pin : # clicked forward, regardless of UI state, play current line sound
                # @TODO: play sound
                self.update_ui_state( 'history' ) # reset interface
            elif 'result' == ui_state and L_Pin : # clicked back on result line, return to history
                self.update_ui_state( 'history' ) # reset interface


        if L_pin == obj :
           get_text_from_input( 'left' )
        elif R_pin == obj :
           get_text_from_input( 'right' )

    def get_text_from_input( text, x=0, top=-2 ) :

        self.draw.rectangle( ( 0, 0, self.width, self.height ), outline=0, fill=0 )
        self.draw.text( (x, top), str( text ),  font=font, fill=255 )

        print text
        return text

    def get_text_from_line( line, x=0, top=-2 ) :

        text = self.content[ line ]
        draw.rectangle( (0, 0, self.width, self.height ), outline=0, fill=0 )
        draw.text( (x, top ), str( text ),  font=font, fill=255 )
        
        print text
        return text

try:
    while 1:
        if not GPIO.input(C_pin):
            catImage = Image.open('/home/pi/happycat_oled_32.ppm').convert('1')
            disp.image(catImage)
        else:
            # Display image.
            disp.image(image)

        disp.display()
        time.sleep(.01) 


except KeyboardInterrupt: 
    GPIO.cleanup()
