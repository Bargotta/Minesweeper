from pynput.mouse import Button, Controller
from numpy import *
from PIL import ImageGrab, ImageOps, Image
import os
import time
import random
import mss
import mss.tools

"""
All coordinates assume a screen resolution of 1440x900, and Chrome 
sized to 1440x730 with the Bookmarks Toolbar disabled.

Play area  = Offset.x + 1, Offset.y + 1, 790, 448
"""
class Offset:
    # coordinates to top left corner of play area
    x = 291
    y = 131

    # coordinates of the first cell
    cell_x = 20
    cell_y = 63

    # number of pixels to get to the top border of a cell
    top_pixel = 11

class Cell:
    unopened = (255, 255, 255)
    zero = (189, 189, 189)
    one = (0, 33, 245)
    two = (53, 120, 32)
    three = (235, 50, 35)
    four = (0, 10, 118)
    five = (113, 18, 11)
    six = (51, 121, 122)
    flagged = (0, 0, 0)
    bomb = (106, 106, 106)

# -----------------------------------------------
# Globals
# -----------------------------------------------
mouse = Controller()

# TODO: Dynamically find size of grid and positions of cells
# size of grid for expert mode
height = 16
width = 30

cell_coords = [[(0, 0)] * width for i in range(height)]
for row in range(height):
    for col in range(width):
        cell_coords[row][col] = (Offset.cell_x + col * 16, Offset.cell_y + row * 16)

# -----------------------------------------------
# Helper Functions
# -----------------------------------------------
# PIL appears to work with pixels of half size, hence the need to convert
# between pixels used by the mouse and pixels used by PIL
def coord_PIL(coord):
    return (2 * coord[0], 2 * coord[1])

def screenshot(save = False):
    with mss.mss() as sct:
        # The screen part to capture
        screen = {"top": Offset.y + 1, "left": Offset.x + 1, "width": 499, "height": 317}
        im = sct.grab(screen)

        # Save image
        if save:
            path = os.getcwd() + '/snaps/snap__' + str(int(time.time())) + '.png'
            mss.tools.to_png(im.rgb, im.size, output=path)
        # Convert to PIL/Pillow Image
        return Image.frombytes('RGB', im.size, im.bgra, 'raw', 'BGRX')

def get_cell(im, coord):
    pixel = im.getpixel(coord_PIL(coord))
    # Zero and unopened cells have the same grey color in the center
    # To distinguish between the two, unopened cells have a white border
    top_pixel_coord = (coord[0] - Offset.top_pixel, coord[1])
    top_pixel = im.getpixel(coord_PIL(top_pixel_coord))

    if (pixel == Cell.zero and unopened(top_pixel)):
        return top_pixel
    else:
        return pixel

def neighbors(row, col):
    def is_valid(h, w):
        return 0 <= h < height and 0 <= w < width

    for diff_r, diff_c in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
        neighbor_r, neighbor_c = row + diff_r, col + diff_c
        if is_valid(neighbor_r, neighbor_c):
            yield neighbor_r, neighbor_c

def value(cell):
    if (cell == Cell.one):
        return 1
    elif (cell == Cell.two):
        return 2
    elif (cell == Cell.three):
        return 3
    elif (cell == Cell.four):
        return 4
    elif (cell == Cell.five):
        return 5
    elif (cell == Cell.six):
        return 6
    else:
        return 0

def flagged(cell):
    return cell == Cell.flagged

def unopened(cell):
    return cell == Cell.unopened

def numbered(cell):
    return (cell == Cell.one or cell == Cell.two or cell == Cell.three
        or cell == Cell.four or cell == Cell.five or cell == Cell.six)

# -----------------------------------------------
# Mouse Controls
# -----------------------------------------------
def left_click(n):
    mouse.click(Button.left, n)
    time.sleep(0.02)

def right_click(n):
    mouse.click(Button.right, n)
    time.sleep(0.02)

def move(coord):
    x = Offset.x + coord[0]
    y = Offset.y + coord[1]
    mouse.position = (x, y)
    time.sleep(.003)

def getCoords():
    x, y = mouse.position
    x = x - Offset.x
    y = y - Offset.y
    print(x, y)

# -----------------------------------------------
# Main
# -----------------------------------------------
def apply_rules(im, row, col):
    cell = get_cell(im, cell_coords[row][col])
    unopened_cells = []
    flagged_cells = []

    n_coords = [cell_coords[r][c] for r, c in neighbors(row, col)]
    for n_coord in n_coords:
        n_cell = get_cell(im, n_coord)
        if unopened(n_cell):
            unopened_cells.append(n_coord)
        elif flagged(n_cell):
            flagged_cells.append(n_coord)

    # rule one 
    if value(cell) == (len(unopened_cells) + len(flagged_cells)):
        for coord in unopened_cells:
            move(coord)
            right_click(1)
        im = screenshot() if len(unopened_cells) > 0 else im

    # rule two
    if value(cell) == len(flagged_cells):
        for coord in unopened_cells:
            move(coord)
            left_click(1)
        im = screenshot() if len(unopened_cells) > 0 else im

    return im

# returns a set containing the coordinates of cells on the border 
def get_border_coords(im):
    border_coords = set()
    for row in range(height):
        for col in range(width):
            if numbered(get_cell(im, cell_coords[row][col])):
                n_coords = [cell_coords[r][c] for r, c in neighbors(row, col)]
                for n_coord in n_coords:
                    n_cell = get_cell(im, n_coord)
                    if unopened(n_cell) and (n_coord not in border_coords):
                        border_coords.add(n_coord)
    return border_coords

def isNeighbor(coord_1, coord_2):
    c1 = coords_to_row_col(coord_1)
    c2 = coords_to_row_col(coord_2)
    diff_x = abs(c1[0] - c2[0])
    diff_y = abs(c1[1] - c2[1])
    return c1 != c2 and diff_x <= 1 and diff_y <= 1

def coords_to_row_col(coord):
    row = int((coord[1] - Offset.cell_y) / 16)
    col = int((coord[0] - Offset.cell_x) / 16)
    return (row, col)

# TODO: Clean up and make more efficient
# Potentially use Union Find to create the disjoint sets
def segregate(coords):
    count = 0
    groups = []
    seen = set()
    while count < len(coords):
        group = []
        change = True
        while change:
            change = False
            for c1 in coords:
                if c1 not in seen:
                    for c2 in group:
                        if isNeighbor(c1, c2):
                            group.append(c1)
                            seen.add(c1)
                            change = True
                    if len(group) == 0:
                        group.append(c1)
                        seen.add(c1)
                        change = True
        group = list(dict.fromkeys(group))
        count += len(group)
        groups.append(group)

    return groups

def tank_rule(im):
    border_coords = get_border_coords(im)
    border_coords_groups = segregate(border_coords)
    for border_coords_group in border_coords_groups:
        tank_recurse(border_coords_group, 0)

# TODO: Implement
def tank_recurse(group, k):
    pass

def execute_move():
    move_made = False
    im = screenshot()

    for row in range(height):
        for col in range(width):
            cell = get_cell(im, cell_coords[row][col])
            if numbered(cell):
                prev_im = im
                im = apply_rules(im, row, col)
                if prev_im != im:
                    move_made = True

    return move_made

def main():
    # start the game by clicking the middle cell
    move(cell_coords[int(height / 2)][int(width / 2)]) 
    left_click(2)
    time.sleep(0.1)

    while (execute_move()):
        pass

if __name__ == '__main__':
    main()

# -----------------------------------------------
# Misc
# -----------------------------------------------
def flag_all():
    for row in range(height):
        for col in range(width):
            coord = cell_coords[row][col]
            move(coord)
            right_click(1)

def flag_group(i, groups):
    group = groups[i]
    for c in group:
        move(c)
        time.sleep(0.1)
        right_click(1)
        time.sleep(0.1)

def screenshot_slow(save = False):
    box = (2 * (Offset.x + 1), 2 * (Offset.y + 1), 
           2 * (Offset.x + 499), 2 * (Offset.y + 317))
    im = ImageGrab.grab(box)
    if save:
        path = os.getcwd() + '/snaps/snap__' + str(int(time.time())) + '.png'
        im.save(path, 'PNG')
    return im