from pynput.mouse import Button, Controller
from numpy import *
from PIL import ImageGrab, ImageOps
import os
import time

"""
All coordinates assume a screen resolution of 1440x900, and Chrome 
sized to 1440x730 with the Bookmarks Toolbar disabled.

Play area (Mouse)  = offset_x+1, offset_x+1, 790, 448
Play area (Screen) = offset_x+1, offset_x+1, 1582, 897

ImageGrab.grab() appeared to work with smaller pixels, hence the
need for the Offset class
"""
class Offset:
	# padding for mouse coordinates
	mouse_x = 291
	mouse_y = 131

	# padding for screen coordinates in screenGrab()
	screen_x = 584
	screen_y = 264

	# coordinates of the first cell
	cell_x = 19
	cell_y = 62

# -----------------------------------------------
# Globals
# -----------------------------------------------
# TODO: Dynamically find size of grid and positions of cells
# size of grid for expert mode
height = 16
width = 30
cell_positions = [[(0, 0)] * width for i in range(height)]

# -----------------------------------------------
# Helper Functions
# -----------------------------------------------
def setCellPositions():
	for row in range(height):
		for col in range(width):
			cell_positions[row][col] = (Offset.cell_x + col * 16, Offset.cell_y + row * 16)
			mousePos(cell_positions[row][col])
			rightClick(1)

def screenGrab():
    box = (Offset.screen_x + 1, Offset.screen_y + 1, 
    	   Offset.screen_x + 998, Offset.screen_y + 633)
    im = ImageGrab.grab(box)
    path = os.getcwd() + '/snaps/snap__' + str(int(time.time())) + '.png'
    im.save(path, 'PNG')
    # return im

# -----------------------------------------------
# Mouse Controls
# -----------------------------------------------

mouse = Controller()

def leftClick(n):
	mouse.click(Button.left, n)
	print("Click!")

def rightClick(n):
	mouse.click(Button.right, n)
	print("Right Click!")

def mousePos(coord):
	x = Offset.mouse_x + coord[0]
	y = Offset.mouse_y + coord[1]
	mouse.position = (x, y)
	time.sleep(.1)	
	print("moved to: " + str(mouse.position))

def getCoords():
	x, y = mouse.position
	x = x - Offset.mouse_x
	y = y - Offset.mouse_y
	print (x, y)

# -----------------------------------------------
# Main
# -----------------------------------------------

def main():
    setCellPositions()

if __name__ == '__main__':
    main()
