from inky import InkyWHAT
from PIL import Image, ImageFont, ImageDraw
from font_source_serif_pro import SourceSerifProSemibold
from font_source_sans_pro import SourceSansProSemibold

import time # needed to delay x seconds between checks
import lastfm_user_data # the api which pulls the lastfm data
import sys # needed to pull command line arguments

# this function prints a new line to the image
def write_new_line(text_to_write, font_size, alignment):
    global line_y
    
    # set font
    font = ImageFont.truetype(SourceSansProSemibold, font_size)

    # work out the size of the text
    text_width, text_height = font.getsize(text_to_write)

    # set the x based on alignment
    if alignment == "center":
        # and set the x to start so that is appears in the middle
        line_x = (display_width - text_width) / 2
    if alignment == "left":
        line_x = left_padding

    # write text to the canvas
    draw.text((line_x, line_y), text_to_write, fill=inky_display.BLACK, font=font)
    print ("Printing to ink >>> " + text_to_write)

    # move to next line
    line_y = line_y + text_height + line_padding

# set globals
previous_track_name = ""

# define variables
colour = "black"
frequency = 15  # number of seconds between checks of the API
rotate = 180  # this can only be 0 or 180 depending on whether you want it upside down or not

if (rotate is not 0) and (rotate is not 180):
    # quits out with error if you ignored the comment above
    exit ("Rotation can only be 0 or 180")

# Set up the correct display and scaling factors
inky_display = InkyWHAT(colour)
inky_display.set_border(inky_display.WHITE)

# find the size of the display
display_width = inky_display.WIDTH
display_height = inky_display.HEIGHT

# Set amount of padding
top_padding = 15
left_padding = 10
line_padding = 5

#set font sizes
fontsize_for_track = 30
fontsize_for_artist = 24
fontsize_for_album = 24
fontsize_for_gap = 34
fontsize_for_stats = 20

# check if a command line argument has been passed to identify the user, if not ask
if len(sys.argv) == 2:
    # if command line includes username then set it to that
    requested_username = str(sys.argv[1])
else:
    # if not then ask the user to input a username
    requested_username = input ("Enter a last.fm username to check the playcount of >>>  ")

# loop to refresh ever x seconds
while True:
    # gather last played information from lastfm api
    print ("Checking API: ", end = '')
    lastplayed_track, lastplayed_artist, lastplayed_album, lastplayed_image = lastfm_user_data.lastplayed (requested_username)
    
    # see if there is new data to display
    if lastplayed_track == previous_track_name:  #check if the track name is same as what we displayed last time
        print ("no change to data - not refreshing")
    else:
        print ("new data found from api - refreshing screen")

        # reset the y start point to the top
        line_y = top_padding

        # create a new canvas to draw on
        img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
        draw = ImageDraw.Draw(img)

        # write the various lines to the image
        write_new_line (lastplayed_track, fontsize_for_track, "center")
        write_new_line (lastplayed_artist, fontsize_for_artist, "center")
        write_new_line (" ", fontsize_for_gap, "left")
        write_new_line (lastfm_user_data.playcount(requested_username, "") + " tracks played all time", fontsize_for_stats, "left")
        write_new_line (lastfm_user_data.playcount(requested_username, "this_year") + " tracks played so far this year", fontsize_for_stats, "left")
        write_new_line (lastfm_user_data.playcount(requested_username, "this_month") + " tracks played so far this month", fontsize_for_stats, "left")
        write_new_line (lastfm_user_data.playcount(requested_username, "this_week") + " tracks played so far this week", fontsize_for_stats, "left")
        write_new_line (lastfm_user_data.playcount(requested_username, "today") + " tracks played so far today", fontsize_for_stats, "left")

        if rotate == 180:
            img = img.rotate(180)

        # display the image on the screen
        inky_display.set_image(img)
        inky_display.show()

        # keep a record of the previous track name to see if it changes next time
        previous_track_name = lastplayed_track

    print ("Waiting " + str(frequency) + " seconds")
    time.sleep (frequency)