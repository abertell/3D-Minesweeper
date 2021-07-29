3D Minesweeper v1.2.3

Author: Adam Bertelli (abertell@andrew.cmu.edu)

3D Minesweeper is an infinitely generated first-person three-dimensional variant of the classic Windows game "Minesweeper". In each cube there is a number, telling you how many of the adjacent cubes (up to 26) contain a mine. Using these numbers, the player's goal is to click on the safe squares to clear them, while right clicking to flag mines as unsafe. As the board is effectively unbounded, your goal is to explore as far as possible without dying.

This game uses the Panda3D graphics library. To run 3D Minesweeper, use "pip install Panda3D" in command prompt to add Panda3D to python (if you do not already have it). Then, run main.py in this folder to play the game.

Controls (ingame):
+ Mouse - point cursor
+ Space - accelerate forward
+ Shift - accelerate backwards
+ W key - accelerate up
+ A key - accelerate left
+ S key - accelerate down
+ D key - accelerate right
+ Click - clear a cube
+ Right Click - flag a cube
+ Q key - clear all unflagged cubes around you (if the number of flags matches the number in the cube)
+ Tab - save the current game state
+ R key - restart (after game over)
+ Escape - quit

Your score is calculated as the sum of the number of cubes you uncovered, plus 100 points for every mine you correctly flag. However, you will lose 10% of your total score, applied cummulatively, for every cube you incorrectly flag.

Save files are written to "saves/saveState.txt", and can be moved freely. If you want to load an external state, be sure to place it in the "saves" folder, and rename it to "saveState.txt".

Explanation of changeable settings (found in main.py) below. Note that most of these settings are accessible in the settings menu.

+ __GAME_PROB__: The probability that a randomly generated cube is a mine.
+ __LIVES__: The amount of times the player can incorrectly click before losing.
+ __CAMERA_FOV__: The first-person field of view angle on the camera.
+ __PLAYER_SPEED__: The speed at which the player can move.
+ __NUM_DISP_PERCENTAGE__: What percentage of the cube you want the size of the displayed number to take up.
+ __LOAD_LIMIT__: How far the game is allowed to propogate outwards while clearing new regions before manually halting, measured in euclidean distance. The lower the number, the less time loading new regions will take.
+ __CHUNK_SIZE__: The playing field is split up into "chunks" for rendering purposes. Each chunk is a cube with side length 2 * CHUNK_SIZE + 1.
+ __RENDER_DIST__: At any given time, there is a 2 * RENDER_DIST + 1 size cube of chunks being rendered, making your total visible area a cube with side length (2 * RENDER_DIST + 1) * (2 * CHUNK_SIZE + 1).
+ __NUM_CHUNK_SIZE__: Analogous to CHUNK_SIZE, but for number rendering. This is recommended to be kept at 0, so that numbers load smoothly as the player traverses cubes.
+ __NUM_RENDER_DIST__: Analogous to RENDER_DIST, but for number rendering. Increase this value if you want to see more numbers at a given time, although this may slow performance somewhat.
+ __DO_COLLIDE__: Prevents the player from going out of bounds if True.
+ __DISP_GUI__: Whether or not the ingame overlay (lives, statistics) is displayed.
+ __WIPE_ON_DEATH__: Wipes the save file on death if True.
+ __FULLSCREEN__: Sets the game window to fullscreen.
