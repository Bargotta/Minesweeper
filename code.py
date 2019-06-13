from pynput.mouse import Button, Controller
from numpy import *
from PIL import ImageGrab, ImageOps
import os
import time
import random

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
    flagged = (0, 0, 0, 255)

# -----------------------------------------------
# Globals
# -----------------------------------------------
# TODO: Dynamically find size of grid and positions of cells
# size of grid for expert mode
height = 16
width = 30

cell_positions = [[(0, 0)] * width for i in range(height)]
for row in range(height):
    for col in range(width):
        cell_positions[row][col] = (Offset.cell_x + col * 16, Offset.cell_y + row * 16)

# -----------------------------------------------
# Helper Functions
# -----------------------------------------------

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

    if (pix == Cell.zero and top_pix == Cell.unopened):
        return top_pix
    else:
        return pix

def neighbors(row, col):
    def is_valid(h, w):
        return 0 <= h < height and 0 <= w < width

    for diffR, diffC in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
        neighborR, neighborC = row + diffR, col + diffC
        if is_valid(neighborR, neighborC):
            yield neighborR, neighborC

def val(im, cell):
    pix = getPixel(im, cell)
    if (pix == Cell.one):
        return 1
    elif (pix == Cell.two):
        return 2
    elif (pix == Cell.three):
        return 3
    elif (pix == Cell.four):
        return 4
    else:
        return 0

def rule_one(im, row, col):
    ns = [cell_positions[r][c] for r, c in neighbors(row, col)]
    unopened_or_flagged_count = 0
    for n in ns:
        pix = getPixel(im, n)
        if (pix == Cell.unopened or pix == Cell.flagged):
            unopened_or_flagged_count += 1

    if val(im, cell_positions[row][col]) == unopened_or_flagged_count:
        for n in ns:
            if (getPixel(im, n) == Cell.unopened):
                move(n)
                rightClick(1)
                im = screenGrab()
                print("RULE 1 EXECUTED...")

    return im

def execute_move():
    finished = False
    im = screenGrab()

    for row in range(height):
        for col in range(width):
            cell = cell_positions[row][col]
            pix = getPixel(im, cell)
            if (pix == Cell.one or pix == Cell.two or
                pix == Cell.three or pix == Cell.four):
                im = rule_one(im, row, col)

# -----------------------------------------------
# Mouse Controls
# -----------------------------------------------

mouse = Controller()

def leftClick(n):
    mouse.click(Button.left, n)
    # print("Click!")

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
    # start the game by clicking the middle cell
    move(cell_positions[int(height / 2)][int(width / 2)]) 
    leftClick(1)

    execute_move()

    # i = 0
    # while i < 10:
    #     i += 1
    #     execute_move()

    # i = 0
    # j = 0
    # while i < 30 and j < 100:
    #     j += 1
    #     rand_x = random.randint(0, width - 1)
    #     rand_y = random.randint(0, height - 1)
    #     cell = cell_positions[rand_y][rand_x]
    #     im = screenGrab()

    #     if getPixel(im, cell) == Cell.bomb:
    #         print("bomb :(")
    #         break

    #     if getPixel(im, cell) == Cell.unopened:
    #         i += 1
    #         move(cell)
    #         leftClick(1)
    #         # print("unopened!")
    #         # print("")
    #     else:
    #         # print("opened")
    #         # print("")
    #         time.sleep(.1)


if __name__ == '__main__':
    main()
