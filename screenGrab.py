from PIL import ImageGrab
import os
import time

"""
All coordinates assume a screen resolution of 1440x900, and Chrome 
sized to 1440x730 with the Bookmarks Toolbar disabled.

x_pad = 584
y_pad = 264
Play area =  x_pad+1, y_pad+1, 1582, 897
"""

# Globals
# ------------------
# screen coordinate padding
x_pad = 582
y_pad = 262
 
def screenGrab():
    box = (x_pad + 2, y_pad + 2, x_pad + 998, y_pad + 633)
    im = ImageGrab.grab(box)
    path = os.getcwd() + '/snaps/snap__' + str(int(time.time())) + '.png'
    im.save(path, 'PNG')

def main():
    screenGrab()
 
if __name__ == '__main__':
    main()