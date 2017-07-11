import RPi.GPIO as GPIO

import time

# import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

with open('/home/pi/words.log') as f:
    content = f.readlines()

content = [x.strip() for x in content]
list_len = len(content)
current_index = 0
previous_text = ""

# Input pins:
L_pin = 16 
R_pin = 12 
C_pin = 6 
U_pin = 19 
D_pin = 21 

A_pin = 5 
B_pin = 6 


GPIO.setmode(GPIO.BCM) 

# GPIO.setup(A_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
# GPIO.setup(B_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(L_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(R_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(U_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(D_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(C_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up


# Raspberry Pi pin configuration:
RST = 24
# Note the following are only used with SPI:
DC = 23
SPI_PORT = 0
SPI_DEVICE = 0

# 128x32 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)

# Initialize library.
disp.begin()

# Clear display.
disp.clear()
disp.display()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0,0,width,height), outline=0, fill=0)
x = 0
top = -2

# Load default font.
font = ImageFont.load_default()

def get_count() :
    global current_index
    return current_index

def set_count(new_count) :
    global current_index
    global list_len

    if( new_count >= list_len ) :
        new_count = list_len

    if ( new_count <= 0 ) :
        new_count = 0

    current_index = new_count
    return new_count

def count_up(obj) :
    print "count_up: "
    #print obj
#    curr_count = get_count()
#    update_count = set_count( curr_count + 1 )
#    print update_count
#    get_text_from_count(update_count)
    global content
    curr_count = get_count()
    update_count = set_count( curr_count + 1 )
    print update_count
    get_text_from_count(update_count)


def count_down(obj) :
    print "count_down: "
    #print obj
    global content
    curr_count = get_count()
    update_count = set_count( curr_count - 1 )
    print update_count
    get_text_from_count(update_count)

def direction_event(obj) :
    global content
    print "direction_event: "
    print obj
    curr_count = get_count()
    if U_pin == obj :
        update_count = set_count( curr_count + 1 )
    elif D_pin == obj :
        update_count = set_count( curr_count - 1 )
    
    if U_pin == obj or D_pin == obj :
        get_text_from_count(update_count)
        print update_count

    if L_pin == obj :
       get_text_from_input("left")
    elif R_pin == obj :
       get_text_from_input("right")

def get_text_from_input(input) :
    global font
    global width
    global height
    draw.rectangle((0,0,width,height), outline=0, fill=0)
    x = 0
    top = -2
    draw.text((x, top), str(input),  font=font, fill=255)

def get_text_from_count(count) :
    # @todo: don't use globals
    global content
    global font
    global width
    global height
    draw.rectangle((0,0,width,height), outline=0, fill=0)
    x = 0
    top = -2
    draw.text((x, top), str(content[count]),  font=font, fill=255)
    # print content[count]


#GPIO.add_event_detect(U_pin, GPIO.FALLING, callback=count_up, bouncetime=300)
#GPIO.add_event_detect(D_pin, GPIO.FALLING, callback=count_down, bouncetime=300)

GPIO.add_event_detect(U_pin, GPIO.FALLING, callback=direction_event, bouncetime=300)
GPIO.add_event_detect(D_pin, GPIO.FALLING, callback=direction_event, bouncetime=300)

GPIO.add_event_detect(L_pin, GPIO.FALLING, callback=direction_event, bouncetime=300)
GPIO.add_event_detect(R_pin, GPIO.FALLING, callback=direction_event, bouncetime=300)


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
