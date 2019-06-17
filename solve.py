from pynput.mouse import Button, Controller
from numpy import *
from PIL import ImageGrab, ImageOps, Image
import os
import time
import random
import mss
import mss.tools
import copy

"""
Minesweeper bot for http://minesweeperonline.com

Before running, ensure game["offset"] is set to the coordinates for 
the pixel in the top left corner of the play area.

(Current coordinates assume a screen resolution of 1440x900, and Chrome 
sized to 1440x730 with the Bookmarks Toolbar disabled.)
"""
class Game:
    beginner = {
        # height and width of board in cells
        "height": 9,
        "width": 9,
        # height and width of screen in pixels
        "screen_height": 205,
        "screen_width": 163,
        # coordinates to top left corner of play area
        "offset": { "x": 301, "y": 131 }
    }
    intermediate = {
        # height and width of board in cells
        "height": 16,
        "width": 16,
        # height and width of screen in pixels
        "screen_height": 317,
        "screen_width": 275,
        # coordinates to top left corner of play area
        "offset": { "x": 301, "y": 131 }
    }
    expert = {
        # height and width of board in cells
        "height": 16,
        "width": 30,
        # height and width of screen in pixels
        "screen_height": 317,
        "screen_width": 499,
        # coordinates to top left corner of play area
        "offset": { "x": 291, "y": 131 }
    }

class Offset:
    # coordinates of the first cell in grid
    cell_x = 20
    cell_y = 63

    # length of a cell side in pixels
    cell_length = 16

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
    mine = (106, 106, 106)

# -----------------------------------------------
# Globals
# -----------------------------------------------
# Change this based on the difficulty of the game
game = Game.expert

mouse = Controller()

cell_coords = [[(0, 0)] * game["width"] for i in range(game["height"])]
for row in range(game["height"]):
    for col in range(game["width"]):
        cell_coords[row][col] = (Offset.cell_x + col * Offset.cell_length, Offset.cell_y + row * Offset.cell_length)

# -----------------------------------------------
# Helper Functions
# -----------------------------------------------
# PIL appears to work with pixels of half size, hence the need to convert
# between pixels used by the mouse and pixels used by PIL
def coord_PIL(coord):
    return (2 * coord[0], 2 * coord[1])

def coords_to_row_col(coord):
    row = int((coord[1] - Offset.cell_y) / Offset.cell_length)
    col = int((coord[0] - Offset.cell_x) / Offset.cell_length)
    return (row, col)

def screenshot(save = False):
    with mss.mss() as sct:
        # The screen part to capture
        screen = {
            "top": game["offset"]["y"] + 1, 
            "left": game["offset"]["x"] + 1, 
            "width": game["screen_width"], 
            "height": game["screen_height"]
        }
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
        return 0 <= h < game["height"] and 0 <= w < game["width"]

    for diff_r, diff_c in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
        neighbor_r, neighbor_c = row + diff_r, col + diff_c
        if is_valid(neighbor_r, neighbor_c):
            yield neighbor_r, neighbor_c

def isNeighbor(coord_1, coord_2):
    c1_r, c1_c = coords_to_row_col(coord_1)
    c2_r, c2_c = coords_to_row_col(coord_2)
    diff_r = abs(c1_r - c2_r)
    diff_c = abs(c1_c - c2_c)
    return coord_1 != coord_2 and diff_r <= 1 and diff_c <= 1

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

# returns a set containing the coordinates of cells on the border 
def get_border_coords(im):
    border_coords = set()
    for row in range(game["height"]):
        for col in range(game["width"]):
            if numbered(get_cell(im, cell_coords[row][col])):
                n_coords = [cell_coords[r][c] for r, c in neighbors(row, col)]
                for n_coord in n_coords:
                    n_cell = get_cell(im, n_coord)
                    if unopened(n_cell) and (n_coord not in border_coords):
                        border_coords.add(n_coord)
    return border_coords

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

def get_board(im):
    board = [[Cell.unopened] * game["width"] for i in range(game["height"])]
    for row in range(game["height"]):
        for col in range(game["width"]):
            board[row][col] = get_cell(im, cell_coords[row][col])
    return board

def find_safe_cells(board_states, coords):
    if len(board_states) == 0:
        print("No board states...")
        return []

    safe_cells = []
    for coord in coords:
        row, col = coords_to_row_col(coord)
        safe = True
        for board in board_states:
            cell = board[row][col]
            if not unopened(cell):
                safe = False
                break
        if safe:
            safe_cells.append(coord)
    return safe_cells

def still_feasible(board, row, col):
    curr_cell = board[row][col]
    if not flagged(curr_cell):
        print("Cell is not flagged...")
        return False

    n_row_cols = [(r, c) for r, c in neighbors(row, col)]
    for n_row, n_col in n_row_cols:
        n_cell = board[n_row][n_col]

        if not numbered(n_cell):
            continue

        flag_count = 0
        n_n_cells = [board[r][c] for r, c in neighbors(n_row, n_col)]
        for n_n_cell in n_n_cells:
            if flagged(n_n_cell):
                flag_count += 1
        if flag_count > value(n_cell):
            return False

    return True

def valid_cell(board, row, col):
    curr_cell = board[row][col]
    if numbered(curr_cell):
        flag_count = 0
        n_cells = [board[r][c] for r, c in neighbors(row, col)]
        for n_cell in n_cells:
            if flagged(n_cell):
                flag_count += 1
        if flag_count != value(curr_cell):
            return False
    return True

def valid_board_group(board, coords):
    for coord in coords:
        row, col = coords_to_row_col(coord)
        n_row_cols = [(r, c) for r, c in neighbors(row, col)]
        for n_row, n_col in n_row_cols:
            if not valid_cell(board, n_row, n_col):
                return False
    return True

def sort_by_elem_length(arr):
    arr = [(len(elem), elem) for elem in arr]
    sorted_arr = sorted(arr, key = lambda elem: elem[0])
    return [elem[1] for elem in sorted_arr]

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
    x = game["offset"]["x"] + coord[0]
    y = game["offset"]["y"] + coord[1]
    mouse.position = (x, y)
    time.sleep(.003)

def getCoords():
    x, y = mouse.position
    x = x - game["offset"]["x"]
    y = y - game["offset"]["y"]
    print(x, y)

# -----------------------------------------------
# Main
# -----------------------------------------------
def educated_guess(board_states, coords):
    if len(board_states) == 0:
        print("No board states...")
        return False

    if len(coords) == 0:
        print("No coords given...")
        return False

    counts = []
    for coord in coords:
        count = 0
        row, col = coords_to_row_col(coord)
        for board in board_states:
            cell = board[row][col]
            # invarient check
            if not (unopened(cell) or flagged(cell)):
                print("Something went wrong...")
            if flagged(cell):
                count += 1
        counts.append((count, coord))

    counts = sorted(counts, key = lambda elem: elem[0])
    return counts[0][1]

def tank_recurse(coords_group, k, board, board_states):
    if k == len(coords_group):
        if valid_board_group(board, coords_group):
            board_states.append(copy.deepcopy(board))
        return

    row, col = coords_to_row_col(coords_group[k])
    # invarient check
    if not unopened(board[row][col]):
        print("Something went wrong...")

    board[row][col] = Cell.unopened
    tank_recurse(coords_group, k + 1, board, board_states)

    board[row][col] = Cell.flagged
    if still_feasible(board, row, col):
        tank_recurse(coords_group, k + 1, board, board_states)
    board[row][col] = Cell.unopened

# Last restort rule... Very time consuming
def tank_rule(im):
    print("\nBringing in reinforcement...")
    border_coords = get_border_coords(im)
    border_coords_groups = sort_by_elem_length(segregate(border_coords))
    board = get_board(im)
    give_up = False
    all_board_states = []

    move_made = False
    for border_coords_group in border_coords_groups:
        border_len = len(border_coords_group)
        print("length of border: " + str(border_len))
        # hopefully enough has been done to go back to rule 1 and rule 2...
        if move_made and border_len > 15:
            print("Going back to rule 1 and rule 2...\n")
            give_up = True
            break

        # continuing will take too long
        if border_len > 27:
            print("Giving up...")
            give_up = True
            break

        board_states = []
        tank_recurse(border_coords_group, 0, board, board_states)
        all_board_states.append(board_states)
        safe_cells = find_safe_cells(board_states, border_coords_group)
        for coord in safe_cells:
            move(coord)
            left_click(1)
            move_made = True

    # All else has failed... make an educated guess
    if not move_made and not give_up:
        guess_made = False
        for i in range(len(border_coords_groups)):
            if guess_made:
                print("Going back to rule 1 and rule 2...\n")
                break

            print("time for an educated guess...")
            coord = educated_guess(all_board_states[i], border_coords_groups[i])
            if coord:
                move(coord)
                left_click(1)
                guess_made = True

    return im != screenshot()

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

def execute_move():
    move_made = False
    im = screenshot()

    for row in range(game["height"]):
        for col in range(game["width"]):
            cell = get_cell(im, cell_coords[row][col])
            if numbered(cell):
                prev_im = im
                im = apply_rules(im, row, col)
                if im != prev_im:
                    move_made = True

    return move_made

def main():
    # start the game by clicking the middle cell
    move(cell_coords[int(game["height"] / 2)][int(game["width"] / 2)]) 
    left_click(2)
    time.sleep(0.03)

    while (True):
        # try rules 1 and 2
        if not execute_move():
            # try the final rule as a last resort
            if not tank_rule(screenshot()):
                # we're finished (or stuck)
                break

if __name__ == '__main__':
    main()

# -----------------------------------------------
# Misc and deprecated functions
# -----------------------------------------------
def flag_all():
    for row in range(game["height"]):
        for col in range(game["width"]):
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
    box = (2 * (game["offset"]["x"] + 1), 2 * (game["offset"]["y"] + 1), 
           2 * (game["offset"]["x"] + 499), 2 * (game["offset"]["y"] + 317))
    im = ImageGrab.grab(box)
    if save:
        path = os.getcwd() + '/snaps/snap__' + str(int(time.time())) + '.png'
        im.save(path, 'PNG')
    return im

def valid_board(board):
    for row in range(game["height"]):
        for col in range(game["width"]):
            if not valid_cell(board, row, col):
                return False
    return True
