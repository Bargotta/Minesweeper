from pynput.mouse import Button, Controller
from numpy import *
from PIL import ImageGrab, ImageOps
import os
import time

"""
All coordinates assume a screen resolution of 1440x900, and Chrome 
sized to 1440x730 with the Bookmarks Toolbar disabled.

Play area  = pad_x + 1, pad_y + 1, 790, 448

PIL appears to work with pixels of half size, hence the need to convert
between pixels used by the mouse and pixels used by PIL
"""
def coordPIL(coords):
    return (2 * coords[0], 2 * coords[1])

class Offset:
    # coordinates to top left corner of play area
    x = 291
    y = 131

    # coordinates of the first cell
    cell_x = 20
    cell_y = 63

    # number of pixels to get to the top border of a cell
    top_border = 11

class Cell:
    unopened = (255, 255, 255, 255)
    zero = (189, 189, 189, 255)
    one = (0, 33, 245, 255)
    two = (53, 120, 32, 255)
    three = (235, 50, 35, 255)
    four = (0, 10, 118, 255)
    bomb = (106, 106, 106, 255)

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

def screenGrab():
    box = (2 * (Offset.x + 1), 2 * (Offset.y + 1), 
           2 * (Offset.x + 499), 2 * (Offset.y + 317))
    im = ImageGrab.grab(box)
    # path = os.getcwd() + '/snaps/snap__' + str(int(time.time())) + '.png'
    # im.save(path, 'PNG')
    return im

def getPixel(im, coord):
    pix = im.getpixel(coordPIL(coord))
    # Zero and unopened cells have the same grey color in the center
    # To distinguish between the two, unopened cells have a white border
    top_border_coords = (coord[0] - Offset.top_border, coord[1])
    top_pix = im.getpixel(coordPIL(top_border_coords))

    return pix if top_pix != Cell.unopened else top_pix

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

def move(coord):
    x = Offset.x + coord[0]
    y = Offset.y + coord[1]
    mouse.position = (x, y)
    time.sleep(.1)   
    # print("moved to: " + str(mouse.position))

def getCoords():
    x, y = mouse.position
    x = x - Offset.x
    y = y - Offset.y
    print (x, y)

# -----------------------------------------------
# Main
# -----------------------------------------------

def main():
    setCellPositions()
    im = screenGrab()

    for row in range(height):
        for col in range(width):
            pos = cell_positions[row][col]
            if (getPixel(im, pos) == Cell.one):
                print("1")
            elif (getPixel(im, pos) == Cell.two):
                print("2")
            elif (getPixel(im, pos) == Cell.three):
                print("3")
            elif (getPixel(im, pos) == Cell.four):
                print("4")
            elif (getPixel(im, pos) == Cell.zero):
                print("0")
            elif (getPixel(im, pos) == Cell.bomb):
                print("bomb")
            elif (getPixel(im, pos) == Cell.unopened):
                print("unopened")
            else:
                print("not sure...")
            # move(pos)


if __name__ == '__main__':
    main()
