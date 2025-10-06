"""
**********************************************************************************************
SOFTWARE COPYRIGHT NOTIFICATION
**********************************************************************************************
Copyright © 2025, UChicago Argonne, LLC

All Rights Reserved

Software Name: Hydropower Market Game

By: UChicago Argonne, LLC

**********************************************************************************************

OPEN SOURCE LICENSE (MIT)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, 
including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
· The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

**********************************************************************************************

Third-Party Resources and Acknowledgments

We extend our sincere gratitude to the following individuals, organizations, and resources whose contributions and publicly available information have been invaluable in the development of the Hydropower Market Game.

--------------------------------------------------------------------------------
Research & Data Sources:

REDi Island project: https://www.nrel.gov/water/redi-island

The REDi Island project's contribution to this game builds upon their previous collaborative work with IKM, from whom they sourced 3D models. specifically:

3D Modeling & Animation:

IKM Testing UK - For their expertise and contribution in 3D animation: https://www.ikm.com/ikm-testing-uk/3d-animation/

--------------------------------------------------------------------------------

AI-Generated Content:

Google's Whisk and OpenAI’s ChatGPT - For the creation of AI-generated pictures used within this game.

--------------------------------------------------------------------------------

Python Libraries:

· Standard Python Library License: Python Software Foundation License (PSF License) Copyright: Python Software Foundation and individual contributors URL: https://www.python.org/about/legal/

· OpenCV (cv2) License: Apache License 2.0 Copyright: OpenCV Team and Contributors URL: https://opencv.org/license/

· Pygame License: GNU LGPL version 2.1 Copyright: Pygame Community and Contributors URL: https://www.pygame.org/docs/LGPL.txt

· NumPy License: BSD 3-Clause License Copyright: NumPy Developers URL: https://numpy.org/doc/stable/license.html

· Matplotlib License: Python Software Foundation License (BSD-style) Copyright: Matplotlib Development Team URL: https://matplotlib.org/stable/project/license.html

· OR-Tools License: Apache License 2.0 Copyright: Google LLC URL: https://developers.google.com/optimization/

--------------------------------------------------------------------------------

Thank you for playing the Hydropower Market Game!
"""
import pygame
import sys
import os
from pathlib import Path
import webbrowser
import cv2
import numpy as np
import random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import tempfile
plt.rcParams["axes3d.mouserotationstyle"] = 'azel'
from matplotlib.backends.backend_agg import FigureCanvasAgg
from ortools.math_opt.python import mathopt
import time
import json

#Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 200, 0)

pygame.init()


def get_save_path():
    """
    Finds the correct cross-platform save location for user data.
    - Windows: %APPDATA%/HydropowerMarketGame
    - macOS:   ~/Library/Application Support/HydropowerMarketGame
    - Linux:   ~/.config/HydropowerMarketGame
    """
    home = Path.home()

    if sys.platform == "win32":
        # Windows path
        save_dir = Path(os.getenv('APPDATA')) / "HydropowerMarketGame"
    elif sys.platform == "darwin":
        # macOS path
        save_dir = home / "Library" / "Application Support" / "HydropowerMarketGame"
    else:
        # Linux/other path
        save_dir = home / ".config" / "HydropowerMarketGame"

    # Create the directory if it doesn't exist
    save_dir.mkdir(parents=True, exist_ok=True)

    return save_dir / "save_game.json"

SAVE_FILE = get_save_path()

#Model Variables
fig_3d, ax_3d, canvas_3d, scatter = None, None, None, None
fig_colormap, ax_colormap, canvas_colormap, red_dot = None, None, None, None
g = 9.81  # Gravity

# Screen settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Hydropower Market Game")

#Character Select variables
FACE_PATH_TEMPLATE = "assets/CYC_Assets/Faces/F{}.jpg"
BODY_PATH_TEMPLATE = "assets/CYC_Assets/Bodies/B{}.jpg"
NUM_CHARACTERS = 9  # Includes the center "Random"

cursor_visible = True
cursor_last_switch = 0
cursor_switch_interval = 500  # milliseconds

#Player Information
selected_character = 1
face_rects = []
player_name = "Brooks"
max_name_length = 16
name_input_rect = None

#Level Select variables
level_names = [
        "Level 0 - Welcome to Blue Rapids!",
        "Level 1 - First Job: Run of River Hydropower Plant",
        "Level 2 - Moving Up: Dam Hydropower Plant",
        "Level 3 - Pumped Storage Hydropower Plant",
        "Level 4 - Management: Environmental Operations",
        "Level 5 - Management: Working With the Power Grid"
    ]
level_completed = [False] * len(level_names)
unlocked_levels = [False] * len(level_names)
level_scores = [0] * len(level_names)

#RoR Variables
NUM_ROR_FRAMES = 62
WATER_LOWER_PATH_TEMPLATE = 'assets/RoRWaterFrames/RoRLoopFrame_{}.jpg'
TUBE_PATH_TEMPLATE = 'assets/RoRTubeFrames/RoRLoopFrame_{}.jpg'
ROR_LEVEL_DURATION = 60
MAX_ROTATION = 90
ROTATION_ANGLE = 5
NUM_OVALS = 16

#Dam Variables
NUM_FLOW_FRAMES = 37
FLOW_PATH_TEMPLATE = 'assets/DamSequences/Flow Cuts/Flow1_frame_{}.jpg'
FLOW2_PATH_TEMPLATE = 'assets/DamSequences/Flow Cuts 2/Flow2_frame_{}.jpg'
FLOW3_PATH_TEMPLATE = 'assets/DamSequences/Flow Cuts 3/Flow3_frame_{}.jpg'
FLOW4_PATH_TEMPLATE = 'assets/DamSequences/Flow Cuts 4/Flow4_frame_{}.jpg'
NUM_TURBINE_FRAMES = 34
TURBINE_PATH_TEMPLATE = 'assets/DamSequences/Turbine Cuts/Turbine1_frame_{}.jpg'
TURBINE2_PATH_TEMPLATE = 'assets/DamSequences/Turbine Cuts 2/Turbine2_frame_{}.jpg'
TURBINE3_PATH_TEMPLATE = 'assets/DamSequences/Turbine Cuts 3/Turbine3_frame_{}.jpg'
TURBINE4_PATH_TEMPLATE = 'assets/DamSequences/Turbine Cuts 4/Turbine4_frame_{}.jpg'
NUM_WATER_FRAMES = 127
WATER_PATH_TEMPLATE = 'assets/DamSequences/WaterLevels/WaterLevel_{}.jpg'
NUM_SPILLWAY_FRAMES = 25
SPILLWAY_PATH_TEMPLATE = 'assets/DamSequences/Spillway Cuts/Spillway_frame_{}.jpg'
MAX_WATER_LEVEL = 5.656
WATER_LEVEL_THRESHOLD = 0.01 * MAX_WATER_LEVEL  # 1% of the max water level
DAM_LEVEL_DURATION = 120 # Duration of the level in seconds
BAR_IMAGE_PATH_TEMPLATE = 'assets/IKM_Assets/AnimatedBarSequence/Bar_{}.png'
BAR_IMAGE_COUNT = 101 # Bar_0 to Bar_100

#RoR and Dam Load Curve
LOAD_CURVE = np.array([280.        , 277.33553356, 274.83879336, 272.50225427,

       270.31839115, 268.27967885, 266.37859225, 264.6076062 ,

       262.95919557, 261.42583522, 260.        , 258.67416478,

       257.44080443, 256.2923938 , 255.22140775, 254.22032115,

       253.28160885, 252.39774573, 251.56120664, 250.76446644,

       250.        , 249.26280731, 248.55798893, 247.89317055,

       247.27597786, 246.71403656, 246.21497233, 245.78641087,

       245.43597786, 245.17129901, 245.        , 244.92960597,

       244.96723985, 245.119924  , 245.3946808 , 245.79853262,

       246.33850183, 247.0216108 , 247.8548819 , 248.84533751,

       250.        , 251.32376881, 252.81305169, 254.46213346,

       256.26529895, 258.21683297, 260.31102036, 262.54214594,

       264.90449452, 267.39235093, 270.        , 272.7303188 ,

       275.62055341, 278.71654217, 282.06412342, 285.70913549,

       289.69741672, 294.07480546, 298.88714002, 304.18025876,

       310.        , 316.364956  , 323.18473468, 330.34169786,

       337.71820738, 345.19662506, 352.65931274, 359.98863224,

       367.0669454 , 373.77661404, 380.        , 385.64985719,

       390.76050786, 395.39666637, 399.62304705, 403.50436425,

       407.10533231, 410.49066557, 413.72507838, 416.87328507,

       420.        , 423.15561524, 426.33323386, 429.51163665,

       432.6696044 , 435.78591793, 438.83935801, 441.80870547,

       444.67274109, 447.41024566, 450.        , 452.42768184,

       454.7065567 , 456.85678705, 458.89853534, 460.85196405,

       462.73723563, 464.57451255, 466.38395728, 468.18573227,

       470.        , 471.8436574 , 473.72053934, 475.63121517,

       477.57625424, 479.55622589, 481.57169946, 483.62324432,

       485.71142979, 487.83682524, 490.        , 492.19768856,

       494.41128593, 496.61835226, 498.79644771, 500.92313241,

       502.97596652, 504.93251018, 506.77032355, 508.46696677,

       510.        , 511.35558836, 512.55431693, 513.62537577,

       514.59795494, 515.50124449, 516.36443447, 517.21671496,

       518.08727601, 519.00530767, 520.        , 521.08995799,

       522.25144633, 523.45014464, 524.65173254, 525.82188965,

       526.92629559, 527.93062997, 528.80057242, 529.50180256,

       530.        , 530.26957968, 530.31989774, 530.16904566,

       529.83511489, 529.33619691, 528.69038318, 527.91576516,

       527.03043431, 526.0524821 , 525.        , 523.88672331,

       522.70896271, 521.45867273, 520.12780788, 518.7083227 ,

       517.1921717 , 515.5713094 , 513.83769034, 511.98326903,

       510.        , 507.89852709, 505.76425142, 503.70126344,

       501.81365358, 500.2055123 , 498.98093004, 498.24399723,

       498.09880433, 498.64944177, 500.        , 502.21416834,

       505.19403161, 508.80127353, 512.89757779, 517.3446281 ,

       522.00410816, 526.73770167, 531.40709235, 535.87396389,

       540.        , 543.67479955, 546.89962212, 549.70364244,

       552.11603526, 554.16597531, 555.88263733, 557.29519608,

       558.43282627, 559.32470267, 560.        , 560.47663344,

       560.7274799 , 560.7141567 , 560.39828118, 559.74147067,

       558.70534251, 557.25151403, 555.34160256, 552.93722544,

       550.        , 546.50866667, 542.51045829, 538.06973077,

       533.25084003, 528.11814202, 522.73599264, 517.16874782,

       511.48076349, 505.73639558, 500.        , 494.31869986,

       488.67068695, 483.01692024, 477.31835869, 471.53596127,

       465.63068695, 459.5634947 , 453.29534347, 446.78719225,

       440.        , 432.90653389, 425.52679392, 417.89258829,

       410.03572522, 401.98801291, 393.78125957, 385.4472734 ,

       377.01786261, 368.52483541, 360.        , 351.47516459,

       342.98213739, 334.5527266 , 326.21874043, 318.01198709,

       309.96427478, 302.10741171, 294.47320608, 287.09346611])
 

#PSH Variables
NUM_PSH_FRAMES = 278
PSH_PATH_TEMPLATE = 'assets/PSHSequences/PSHLevelFramesCut/Generating_Frame_{}.jpg'

POWERHOUSE_NUM_FRAMES = 47
POWERHOUSE_PATH_TEMPLATE = 'assets/PSHSequences/PSHTurbineCut/Turbine_frame_{}.jpg'

MAX_PSH_RELEASE = 150
MIN_PSH_RELEASE = -150
RELEASE_STEP = 10
PSH_LEVEL_DURATION = 120

UPPER_RESERVOIR_PATH_TEMPLATE = 'assets/PSHSequences/PSHUpperReservoirFramesCut/UpperReservoir_frame_{}.jpg'

FLOW_CUT_NUM_FRAMES = 211
FLOW_CUT_PATH_TEMPLATE = 'assets/PSHSequences/PSHNoFlowTest1/NoFlow_frame_{}.jpg'

PSH_LOAD = np.array([ 4.00000000e+02,  3.98629950e+02,  3.97103074e+02,  3.95425686e+02,
        3.93604099e+02,  3.91644628e+02,  3.89553587e+02,  3.87337289e+02,
        3.85002050e+02,  3.82554182e+02,  3.80000000e+02,  3.77345818e+02,
        3.74597950e+02,  3.71762711e+02,  3.68846413e+02,  3.65855372e+02,
        3.62795901e+02,  3.59674314e+02,  3.56496926e+02,  3.53270050e+02,
        3.50000000e+02,  3.46696777e+02,  3.43385124e+02,  3.40093471e+02,
        3.36850248e+02,  3.33683885e+02,  3.30622810e+02,  3.27695455e+02,
        3.24930248e+02,  3.22355620e+02,  3.20000000e+02,  3.17877074e+02,
        3.15941553e+02,  3.14133404e+02,  3.12392594e+02,  3.10659090e+02,
        3.08872859e+02,  3.06973867e+02,  3.04902082e+02,  3.02597471e+02,
        3.00000000e+02,  2.97054926e+02,  2.93728663e+02,  2.89992911e+02,
        2.85819375e+02,  2.81179755e+02,  2.76045756e+02,  2.70389078e+02,
        2.64181424e+02,  2.57394498e+02,  2.50000000e+02,  2.41983221e+02,
        2.33383796e+02,  2.24254951e+02,  2.14649907e+02,  2.04621888e+02,
        1.94224119e+02,  1.83509822e+02,  1.72532221e+02,  1.61344539e+02,
        1.50000000e+02,  1.38562191e+02,  1.27136152e+02,  1.15837286e+02,
        1.04780999e+02,  9.40826915e+01,  8.38577692e+01,  7.42216353e+01,
        6.52896933e+01,  5.71773470e+01,  5.00000000e+01,  4.38180157e+01,
        3.84715962e+01,  3.37459034e+01,  2.94260993e+01,  2.52973456e+01,
        2.11448043e+01,  1.67536372e+01,  1.19090062e+01,  6.39607317e+00,
        0.00000000e+00, -7.43425361e+00, -1.58225366e+01, -2.50209003e+01,
       -3.48853957e+01, -4.52720740e+01, -5.60369864e+01, -6.70361840e+01,
       -7.81257180e+01, -8.91616397e+01, -1.00000000e+02, -1.10511001e+02,
       -1.20621450e+02, -1.30272302e+02, -1.39404517e+02, -1.47959050e+02,
       -1.55876859e+02, -1.63098901e+02, -1.69566134e+02, -1.75219515e+02,
       -1.80000000e+02, -1.83881741e+02, -1.86971665e+02, -1.89409890e+02,
       -1.91336538e+02, -1.92891727e+02, -1.94215578e+02, -1.95448211e+02,
       -1.96729746e+02, -1.98200302e+02, -2.00000000e+02, -2.02222033e+02,
       -2.04771891e+02, -2.07508136e+02, -2.10289332e+02, -2.12974041e+02,
       -2.15420827e+02, -2.17488253e+02, -2.19034882e+02, -2.19919277e+02,
       -2.20000000e+02, -2.19170126e+02, -2.17460772e+02, -2.14937566e+02,
       -2.11666135e+02, -2.07712108e+02, -2.03141112e+02, -1.98018775e+02,
       -1.92410726e+02, -1.86382591e+02, -1.80000000e+02, -1.73317462e+02,
       -1.66345021e+02, -1.59081601e+02, -1.51526128e+02, -1.43677527e+02,
       -1.35534725e+02, -1.27096645e+02, -1.18362214e+02, -1.09330357e+02,
       -1.00000000e+02, -9.03800249e+01, -8.05191450e+01, -7.04760310e+01,
       -6.03093534e+01, -5.00777826e+01, -3.98399893e+01, -2.96546438e+01,
       -1.95804167e+01, -9.67597864e+00,  1.77635684e-15,  9.41756166e+00,
        1.86616008e+01,  2.78457249e+01,  3.70835415e+01,  4.64886579e+01,
        5.61746817e+01,  6.62552204e+01,  7.68438813e+01,  8.80542720e+01,
        1.00000000e+02,  1.12759778e+02,  1.26272742e+02,  1.40443131e+02,
        1.55175188e+02,  1.70373151e+02,  1.85941262e+02,  2.01783762e+02,
        2.17804892e+02,  2.33908891e+02,  2.50000000e+02,  2.65993325e+02,
        2.81847432e+02,  2.97531750e+02,  3.13015708e+02,  3.28268738e+02,
        3.43260269e+02,  3.57959730e+02,  3.72336553e+02,  3.86360166e+02,
        4.00000000e+02,  4.13236920e+02,  4.26097530e+02,  4.38619870e+02,
        4.50841979e+02,  4.62801897e+02,  4.74537663e+02,  4.86087317e+02,
        4.97488898e+02,  5.08780446e+02,  5.20000000e+02,  5.31148995e+02,
        5.42082448e+02,  5.52618771e+02,  5.62576376e+02,  5.71773675e+02,
        5.80029079e+02,  5.87161002e+02,  5.92987855e+02,  5.97328051e+02,
        6.00000000e+02,  6.00877099e+02,  6.00052677e+02,  5.97675046e+02,
        5.93892517e+02,  5.88853404e+02,  5.82706019e+02,  5.75598674e+02,
        5.67679681e+02,  5.59097352e+02,  5.50000000e+02,  5.40522608e+02,
        5.30746844e+02,  5.20741047e+02,  5.10573555e+02,  5.00312708e+02,
        4.90026844e+02,  4.79784302e+02,  4.69653422e+02,  4.59702542e+02,
        4.50000000e+02,  4.40612468e+02,  4.31599947e+02,  4.23020767e+02,
        4.14933262e+02,  4.07395764e+02,  4.00466605e+02,  3.94204116e+02,
        3.88666631e+02,  3.83912482e+02,  3.80000000e+02,  3.76987518e+02,
        3.74933369e+02,  3.73895884e+02,  3.73933395e+02,  3.75104236e+02,
        3.77466738e+02,  3.81079233e+02,  3.86000053e+02,  3.92287532e+02])

#Environment Variables
# Global simulation parameters and OR-Tools model setup.
N_timesteps = 24
hours = np.arange(N_timesteps)
TARGET = 32000  # Daily release value
min_release = 400
max_ramp_up = 400
max_ramp_down = 600
target_tol = 200
price_values = 40 * np.array(
    [20, 18, 17, 16, 18, 25, 30, 35, 32, 30, 28, 27,
     28, 30, 32, 35, 40, 45, 42, 38, 35, 30, 25, 22]
)

model = mathopt.Model(name="game")
release = [model.add_variable(lb=0.0) for _ in hours]
model.maximize(sum([release[h] * price_values[h] for h in hours]))
model.add_linear_constraint(sum([release[h] for h in hours]) == TARGET)
for h in hours:
    model.add_linear_constraint(release[h] >= min_release)
    model.add_linear_constraint(release[h] - release[h - 1] <= max_ramp_up)
    model.add_linear_constraint(release[h] - release[h - 1] >= -max_ramp_down)

params = mathopt.SolveParameters(enable_output=False)
result = mathopt.solve(model, mathopt.SolverType.GLOP, params=params)
optimal_value = 0
if result.termination.reason == mathopt.TerminationReason.OPTIMAL:
    optimal_value = result.objective_value()

clock = pygame.time.Clock()

# --- Utility functions ---
def save_game_data():
    global player_name, selected_character, unlocked_levels, level_completed, level_scores
    data = {
        'player_name': player_name,
        'selected_character': selected_character,
        'unlocked_levels': unlocked_levels,
        'level_completed': level_completed,
        'level_scores': level_scores
    }
    with open(SAVE_FILE, 'w') as file:
        json.dump(data, file)

def load_game_data():
    global player_name, selected_character, unlocked_levels, level_completed, level_scores
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, 'r') as file:
            data = json.load(file)
            player_name = data.get('player_name', player_name)
            selected_character = data.get('selected_character', selected_character)
            unlocked_levels = data.get('unlocked_levels', unlocked_levels)
            level_completed = data.get('level_completed', level_completed)
            level_scores = data.get('level_scores', level_scores)
            return True
    else:
        return False

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_image(filename):
    try:
        return pygame.image.load(resource_path(filename)).convert_alpha()
    except pygame.error as e:
        print(f"Unable to load image: {e}")
        return None

pygame.display.set_icon(load_image('assets/Game.png'))

def load_frames(num_frames, path_template):
    frames = []
    for i in range(num_frames):
        path = resource_path(path_template.format(i))
        try:
            frame = pygame.image.load(path).convert_alpha()
            frames.append(frame)
        except pygame.error as e:
            print(f"Error loading frame {i}: {e}")
            sys.exit(1)
    return frames

def load_ROR_frames(num_frames, path_template):
    frames = []
    for i in range(0, num_frames):
        try:
            frame_path = resource_path(path_template.format(i))
            frame = pygame.image.load(frame_path).convert()
            frame = pygame.transform.scale(frame, (frame.get_size()[0]*SCREEN_WIDTH/1920, frame.get_size()[1]*SCREEN_HEIGHT/1080))
            frames.append(frame)
        except pygame.error as e:
            print(f"Error loading frame {i}: {e}")
            sys.exit(1)
    return frames

def load_dam_frames(num_frames, path_template):
    """Load and scale frames for animation."""
    frames = []
    for i in range(0, num_frames):
        try:
            frame_path = resource_path(path_template.format(i))
            frame = pygame.image.load(frame_path).convert()
            frame = pygame.transform.scale(frame, (int(frame.get_size()[0]*SCREEN_WIDTH/1920), int(frame.get_size()[1]*SCREEN_HEIGHT/1080)))
            frames.append(frame)
        except pygame.error as e:
            print(f"Error loading frame {i}: {e}")
            sys.exit(1)
    return frames

def blit_centered_text(surface, text, font, y, color=(0, 0, 0)):
            rendered = font.render(text, True, color)
            rect = rendered.get_rect(center=(SCREEN_WIDTH // 2, y))
            surface.blit(rendered, rect)

def tint_surface(surface, tint_color):
    tinted = surface.copy()
    tint = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
    tint.fill(tint_color + (150,))
    tinted.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    return tinted

def change_screen_size(width, height):
    global screen, SCREEN_WIDTH, SCREEN_HEIGHT
    SCREEN_WIDTH = width
    SCREEN_HEIGHT = height
    screen = pygame.display.set_mode((width, height))

def truncate_float(value, decimal_places):
    factor = 10.0 ** decimal_places
    return int(value * factor) / factor

def run_dialogue(scenes):
    global SCREEN_WIDTH, SCREEN_HEIGHT, border_frame, player_name, level_completed, screen

    # --- Dialogue Box Geometry ---
    DIALOGUE_BOX_WIDTH = SCREEN_WIDTH * 0.78
    DIALOGUE_BOX_HEIGHT = SCREEN_HEIGHT * 0.25
    BOX_X = (SCREEN_WIDTH - DIALOGUE_BOX_WIDTH) / 2
    BOX_Y = SCREEN_HEIGHT * 0.85 - DIALOGUE_BOX_HEIGHT / 2
    TEXT_MARGIN_X = DIALOGUE_BOX_WIDTH * 0.02
    TEXT_MARGIN_Y = SCREEN_HEIGHT * 0.06
    LINE_SPACING = SCREEN_HEIGHT * 0.045
    NAME_Y_OFFSET = DIALOGUE_BOX_HEIGHT * 0.05
    NAME_TO_TEXT_SPACING = SCREEN_HEIGHT * 0.015
    HINT_Y_OFFSET = SCREEN_HEIGHT * 0.03

    dialogue_frame = pygame.transform.smoothscale(
        border_frame, (int(DIALOGUE_BOX_WIDTH), int(DIALOGUE_BOX_HEIGHT))
    )

    # --- Fonts ---
    font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Regular.ttf"), int(SCREEN_HEIGHT * 0.035))
    hint_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Italic.ttf"), int(SCREEN_HEIGHT * 0.03))
    name_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.038))
    text_color = (255, 255, 255)

    current_scene_index = 0
    dialogues = scenes[current_scene_index][1]
    idx = 0
    speaker, full_text = dialogues[idx]
    display_text = ""
    text_speed = 30  # chars per second
    timer = 0
    done_typing = False

    clock = pygame.time.Clock()
    running = True
    while running:
        delta = clock.tick(60) / 1000.0
        timer += delta

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game_data()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if not done_typing:
                    display_text = full_text
                    done_typing = True
                else:
                    idx += 1
                    if idx >= len(dialogues):
                        current_scene_index += 1
                        if current_scene_index >= len(scenes):
                            running = False
                            break
                        dialogues = scenes[current_scene_index][1]
                        idx = 0
                        speaker, full_text = dialogues[idx]
                        display_text = ""
                        timer = 0
                        done_typing = False
                    else:
                        speaker, full_text = dialogues[idx]
                        display_text = ""
                        timer = 0
                        done_typing = False

        # Typewriter effect
        if not done_typing:
            chars = min(int(timer * text_speed), len(full_text))
            display_text = full_text[:chars]
            if chars == len(full_text):
                done_typing = True

        # --- Draw ---
        if current_scene_index >= len(scenes):
            running = False
        else:
            screen.blit(scenes[current_scene_index][0], (0, 0))
            screen.blit(dialogue_frame, (BOX_X, BOX_Y))

            # Speaker name
            screen.blit(name_font.render(speaker, True, text_color),
                        (BOX_X + TEXT_MARGIN_X, BOX_Y + NAME_Y_OFFSET))

            # Word-wrap dialogue text
            words = display_text.split(' ')
            lines, line = [], ""
            max_w = DIALOGUE_BOX_WIDTH - 2 * TEXT_MARGIN_X
            for w in words:
                test = f"{line}{w} "
                if font.size(test)[0] < max_w:
                    line = test
                else:
                    lines.append(line)
                    line = f"{w} "
            lines.append(line)

            for i, l in enumerate(lines[:5]):
                y = BOX_Y + TEXT_MARGIN_Y + NAME_TO_TEXT_SPACING + i * LINE_SPACING
                screen.blit(font.render(l, True, text_color), (BOX_X + TEXT_MARGIN_X, y))

            if done_typing:
                hint = hint_font.render("Click to Continue", True, text_color)
                x = BOX_X + DIALOGUE_BOX_WIDTH - TEXT_MARGIN_X - hint.get_width()
                y = BOX_Y + DIALOGUE_BOX_HEIGHT - HINT_Y_OFFSET
                screen.blit(hint, (x, y))

            pygame.display.flip()

def calculate_score(imbalance,water_waste=0,factor=55):
    return int(10000/((imbalance/factor) + (water_waste/20)))

def Example_Graph(x_start=0, x_end=5, power_data=[], display=0,mode=0):
    global LOAD_CURVE
    x = np.linspace(x_start, x_end, 100)
    power_x = np.linspace(x_start, x_start + 0.5, len(power_data))
    plt.figure(figsize=(4, 3), facecolor=(0, 0, 0, 0))
    ax = plt.gca()
    ax.set_facecolor((0, 0, 0, 0))
    plt.plot(power_x, power_data, label='Power Generated', color='red')
    indices = (np.arange(display, display + 100) % len(LOAD_CURVE))
    plt.plot(x, LOAD_CURVE[indices]/30, label='Load Curve', color='white')
    plt.xlim(x_start, x_end)
    plt.ylim(1, 20)
    plt.axis('off')

    if mode == 0:
        legend = plt.legend(loc='upper right', facecolor='none', edgecolor='none', fontsize=16)
    elif mode == 2:
        legend = plt.legend(loc='lower left', facecolor='none', edgecolor='none', fontsize=16)
    for text in legend.get_texts():
        text.set_color('white')

    plt.tight_layout()
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=400, transparent=True)
    plt.close()
    return temp_file.name

# --- Character Select Functions ---
def new_game():
    global selected_character,hovered_index,current_preview_index,ignore_mouse_hover_until_move,block_hover_if_random
    global random_selection_active,random_selection_start_time,random_highlight_index,last_interval_step
    global confirm_clicked,name_input_active,player_name,level_completed, unlocked_levels, level_scores
    global cyc_font_size, cyc_font, cyc_label, cyc_title_font, cyc_title_text, cyc_confirm_font, cyc_confirm_text
    #Resets Things
    selected_character = 4
    hovered_index = None
    current_preview_index = 4
    ignore_mouse_hover_until_move = False
    block_hover_if_random = False
    random_selection_active = False
    random_selection_start_time = 0
    random_highlight_index = None
    last_interval_step = -1
    confirm_clicked = False
    name_input_active = False
    player_name = ""
    cyc_font_size = int(SCREEN_HEIGHT * 0.03)
    cyc_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), cyc_font_size)
    cyc_label = cyc_font.render("Random", True, WHITE)
    cyc_title_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.05))
    cyc_title_text = cyc_title_font.render("Choose your character!", True, WHITE)
    cyc_confirm_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.025))
    cyc_confirm_text = cyc_confirm_font.render("Confirm", True, WHITE)
    level_scores = [0] * len(level_names)
    level_completed = [False] * len(level_names)
    unlocked_levels = [True] + [False] * (len(level_names) - 1)

def trigger_random_selection():
    global random_selection_active, random_selection_start_time, last_interval_step
    random_selection_active = True
    random_selection_start_time = pygame.time.get_ticks()
    last_interval_step = -1


def handle_arrow_keys(key):
    global selected_character, current_preview_index
    row = selected_character // 3
    col = selected_character % 3

    if key == pygame.K_LEFT and col > 0:
        selected_character -= 1
    elif key == pygame.K_RIGHT and col < 2:
        selected_character += 1
    elif key == pygame.K_UP and row > 0:
        selected_character -= 3
    elif key == pygame.K_DOWN and row < 2:
        selected_character += 3

    current_preview_index = selected_character


def draw_character_grid(face_frames, face_size, border_frame, green_border_frame, player_name):
    global face_rects, confirm_button_rect, cursor_visible, cursor_last_switch, cursor_switch_interval
    face_rects = []

    grid_size = 3
    margin = int(SCREEN_WIDTH * 0.01)
    total_grid_width = grid_size * face_size + (grid_size - 1) * margin
    total_grid_height = grid_size * face_size + (grid_size - 1) * margin
    start_x = int(SCREEN_WIDTH * 0.05)
    start_y = (SCREEN_HEIGHT - total_grid_height) // 2

    # Title
    title_x = start_x + (total_grid_width - cyc_title_text.get_width()) // 2
    screen.blit(cyc_title_text, (title_x, start_y - face_size * 0.8))

    # Name input box
    name_box_width = int(face_size * 2.5)
    name_box_height = int(face_size * 0.3)
    name_x = start_x + (total_grid_width - name_box_width) // 2
    name_y = start_y - face_size // 2
    name_input_rect = pygame.Rect(name_x, name_y, name_box_width, name_box_height)
    border_color = (20, 20, 20) if name_input_active else (50, 50, 50)
    name_border = tint_surface(border_frame, border_color)
    name_border = pygame.transform.smoothscale(name_border, (name_box_width + 2, name_box_height + 2))
    screen.blit(name_border, (name_x - 2, name_y - 2))

    text_color = WHITE if player_name else (180, 180, 180)
    display_text = player_name if player_name or name_input_active else "Enter Name:"
    if name_input_active and cursor_visible:
        display_text += "|"  # Add cursor if active and blinking

    name_surface = cyc_font.render(display_text, True, text_color)
    name_text_x = name_x + 10
    name_text_y = name_y + (name_box_height - name_surface.get_height()) // 2
    screen.blit(name_surface, (name_text_x, name_text_y))


    index = 0
    for row in range(grid_size):
        for col in range(grid_size):
            if index >= len(face_frames):
                continue

            x = start_x + col * (face_size + margin)
            y = start_y + row * (face_size + margin)
            rect = pygame.Rect(x, y, face_size, face_size)

            center_x = x + face_size // 2
            center_y = y + face_size // 2
            border_x = center_x - border_frame.get_width() // 2
            border_y = center_y - border_frame.get_height() // 2

            if random_selection_active:
                if index == random_highlight_index and index != 4:
                    screen.blit(green_border_frame, (border_x, border_y))
                else:
                    screen.blit(border_frame, (border_x, border_y))
            else:
                if index == selected_character:
                    screen.blit(green_border_frame, (border_x, border_y))
                else:
                    screen.blit(border_frame, (border_x, border_y))

            screen.blit(face_frames[index], (x, y))
            face_rects.append((rect, index))

            if index == 4:
                screen.blit(cyc_label, (
                    rect.centerx - cyc_label.get_width() // 2,
                    rect.bottom + int(SCREEN_HEIGHT * 0.005)
                ))

            index += 1

    # Confirm Button
    confirm_width = int(face_size * 0.6)
    confirm_height = int(face_size * 0.2)
    confirm_border = pygame.transform.smoothscale(border_frame, (confirm_width + 2, confirm_height + 2))
    confirm_x = start_x + (total_grid_width - confirm_width) // 2
    confirm_y = start_y + total_grid_height + face_size // 4
    confirm_button_rect = pygame.Rect(confirm_x, confirm_y, confirm_width, confirm_height)
    border_center_x = confirm_x + confirm_width // 2
    border_center_y = confirm_y + confirm_height // 2
    border_x = border_center_x - confirm_border.get_width() // 2
    border_y = border_center_y - confirm_border.get_height() // 2

    # Determine if Confirm button should be enabled
    button_enabled = selected_character != 4 and player_name.strip() != ""

    if not button_enabled:
        # Tint confirm button gray when disabled
        gray_border = tint_surface(confirm_border, (100, 100, 100))
        screen.blit(gray_border, (border_x, border_y))
    else:
        screen.blit(confirm_border, (border_x, border_y))

    screen.blit(cyc_confirm_text, (
        confirm_x + (confirm_width - cyc_confirm_text.get_width()) // 2,
        confirm_y + (confirm_height - cyc_confirm_text.get_height()) // 2
    ))

    return name_input_rect


def draw_body_preview(body_frames, index, border_frame):
    if index is None or index >= len(body_frames):
        return
    body_img = body_frames[index]
    x = SCREEN_WIDTH - body_img.get_width() - int(SCREEN_WIDTH * 0.05)
    y = (SCREEN_HEIGHT - body_img.get_height()) // 2
    border_w, border_h = border_frame.get_size()
    center_x = x + body_img.get_width() // 2
    center_y = y + body_img.get_height() // 2
    border_x = center_x - border_w // 2
    border_y = center_y - border_h // 2
    screen.blit(border_frame, (border_x, border_y))
    screen.blit(body_img, (x, y))

# --- Model Functions ---
def draw_3d_surface(Q_val, h_val, azim, elev):
    global fig_3d, ax_3d, canvas_3d, scatter
    if fig_3d:
        plt.close(fig_3d)

    if SCREEN_WIDTH == 960:
        fig_3d = plt.figure(figsize=(4, 3), dpi=100)
    elif SCREEN_WIDTH == 1280:
        fig_3d = plt.figure(figsize=(5, 4), dpi=100)
    elif SCREEN_WIDTH == 1600:
        fig_3d = plt.figure(figsize=(6, 5), dpi=100)
    ax_3d = fig_3d.add_subplot(111, projection='3d',computed_zorder=False)
    fig_3d.subplots_adjust(left=0.15, right=0.85, bottom=0.2)
    Q = np.linspace(0, 10000, 20)
    h = np.linspace(0, 100, 20)
    Q_grid, h_grid = np.meshgrid(Q, h)
    P_grid = 0.00007 * Q_grid * h_grid
    ax_3d.plot_surface(Q_grid, h_grid, P_grid, cmap='viridis', alpha=0.9)
    P_val = 0.00007 * Q_val * h_val
    scatter = ax_3d.scatter(Q_val, h_val, P_val, color='red', s=50,depthshade=False)
    ax_3d.set_xlabel("Flow Rate Q (cfs)", labelpad=10)
    ax_3d.xaxis.set_major_formatter(mticker.StrMethodFormatter('{x:,.0f}'))
    ax_3d.set_ylabel("Head h (ft)", labelpad=10)
    ax_3d.set_zlabel("Power P (MW)", labelpad=10)
    ax_3d.set_xlim(0, 10000)
    ax_3d.set_ylim(0, 100)
    ax_3d.set_zlim(0, 72)
    ax_3d.view_init(elev=elev, azim=azim)
    canvas_3d = FigureCanvasAgg(fig_3d)
    canvas_3d.draw()
    raw_data = canvas_3d.get_renderer().buffer_rgba()
    size = canvas_3d.get_width_height()
    return pygame.image.frombuffer(raw_data, size, "RGBA")

def update_3d_surface(Q_val, h_val, azim, elev):
    global scatter, canvas_3d, ax_3d, fig_3d
    scatter.remove()
    P_val = 0.00007 * Q_val * h_val
    scatter = ax_3d.scatter(Q_val, h_val, P_val, color='red', s=50,depthshade=False)
    ax_3d.view_init(elev=elev, azim=azim)
    canvas_3d.draw()
    raw_data = canvas_3d.get_renderer().buffer_rgba()
    size = canvas_3d.get_width_height()
    return pygame.image.frombuffer(raw_data, size, "RGBA")

def draw_colormap(Q_val, h_val):
    global fig_colormap, ax_colormap, canvas_colormap, red_dot
    if fig_colormap:
        plt.close(fig_colormap)

    if SCREEN_WIDTH == 960:
        fig_colormap, ax_colormap = plt.subplots(figsize=(4, 3), dpi=100)
    elif SCREEN_WIDTH == 1280:
        fig_colormap, ax_colormap = plt.subplots(figsize=(5, 4), dpi=100)
    elif SCREEN_WIDTH == 1600:
        fig_colormap, ax_colormap = plt.subplots(figsize=(6, 5), dpi=100)
    Q = np.linspace(0, 10000, 200)
    h = np.linspace(0, 100, 200)
    Q_grid, h_grid = np.meshgrid(Q, h)
    P_grid = 0.00007 * Q_grid * h_grid
    cmap = plt.get_cmap('viridis')
    c = ax_colormap.pcolormesh(Q_grid, h_grid, P_grid, shading='auto', cmap=cmap)
    fig_colormap.colorbar(c, ax=ax_colormap, label="Power P (MW)")
    red_dot = ax_colormap.plot(Q_val, h_val, 'ro')[0]
    ax_colormap.set_xlabel("Flow Rate Q (cfs)")
    ax_colormap.xaxis.set_major_formatter(mticker.StrMethodFormatter('{x:,.0f}'))
    ax_colormap.set_ylabel("Head h (ft)")
    fig_colormap.tight_layout()
    fig_colormap.patch.set_alpha(0)         # transparent figure background
    ax_colormap.set_facecolor((0,0,0,0))    # transparent axes background
    canvas_colormap = FigureCanvasAgg(fig_colormap)
    canvas_colormap.draw()
    raw_data = canvas_colormap.get_renderer().buffer_rgba()
    size = canvas_colormap.get_width_height()
    return pygame.image.frombuffer(raw_data, size, "RGBA")

def update_colormap(Q_val, h_val):
    global red_dot, canvas_colormap
    red_dot.set_data([Q_val], [h_val])
    canvas_colormap.draw()
    raw_data = canvas_colormap.get_renderer().buffer_rgba()
    size = canvas_colormap.get_width_height()
    return pygame.image.frombuffer(raw_data, size, "RGBA")

# --- RoR Level Functions ---
def draw_arrow_keys(screen, center_x, center_y, pressed_key=None):
    global SCREEN_WIDTH, SCREEN_HEIGHT

    # Colors
    base_color = (0, 206, 244)
    pressed_alpha = 255
    unpressed_alpha = 64
    triangle_color = (0, 0, 0)

    # Sizes relative to screen
    key_size = int(SCREEN_HEIGHT * 0.11)  # Key size ~11% of screen height
    spacing = int(SCREEN_HEIGHT * 0.02)   # Spacing ~2% of screen height
    offset = int(key_size * 0.4)          # Triangle offset relative to key size

    vertical_spacing = key_size + spacing
    horizontal_spacing = key_size + spacing

    # Key positions
    keys = {
        'up': pygame.Rect(center_x - key_size // 2, center_y - vertical_spacing, key_size, key_size),
        'left': pygame.Rect(center_x - 1.42 * horizontal_spacing, center_y, key_size, key_size),
        'down': pygame.Rect(center_x - key_size // 2, center_y, key_size, key_size),
        'right': pygame.Rect(center_x + 1.42 * horizontal_spacing - key_size, center_y, key_size, key_size),
    }

    # Draw keys
    for key, rect in keys.items():
        alpha = pressed_alpha if key == pressed_key else unpressed_alpha
        color_with_alpha = (*base_color, alpha)
        surface = pygame.Surface((key_size, key_size), pygame.SRCALPHA)
        surface.fill(color_with_alpha)
        screen.blit(surface, rect.topleft)

        # Draw arrow triangles
        triangle_points = {
            'up': [(rect.centerx, rect.top + offset), (rect.left + offset, rect.bottom - offset), (rect.right - offset, rect.bottom - offset)],
            'down': [(rect.centerx, rect.bottom - offset), (rect.left + offset, rect.top + offset), (rect.right - offset, rect.top + offset)],
            'left': [(rect.left + offset, rect.centery), (rect.right - offset, rect.top + offset), (rect.right - offset, rect.bottom - offset)],
            'right': [(rect.right - offset, rect.centery), (rect.left + offset, rect.top + offset), (rect.left + offset, rect.bottom - offset)],
        }
        pygame.draw.polygon(screen, triangle_color, triangle_points[key])

def draw_controls_page_ROR(screen, show_pressed_keys, show_blinking_rect):
    # Colors
    text_color = (255, 255, 255)

    # Fonts relative to height
    pygame.font.init()
    title_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Regular.ttf"), int(SCREEN_HEIGHT * 0.09))
    caption_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Regular.ttf"), int(SCREEN_HEIGHT * 0.045))

    # Background
    background = load_image("assets/RoRStatics/RoRStatic.jpg")
    background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
    screen.blit(background, (0, 0))

    gate_image = load_image('assets/RoRStatics/Wicket_gate.png')
    border_frame = load_image('assets/IKM_Assets/BorderFrame.png')

    # Frame and gate scaling
    NUM_OVALS = 16
    angles = [220 - i * 360 / NUM_OVALS for i in range(NUM_OVALS)]
    active_circle_radius = SCREEN_WIDTH * 0.12

    frame_size = int(active_circle_radius * 2.7)
    frame_x = int(SCREEN_WIDTH * 0.55)
    frame_y = int(SCREEN_HEIGHT * 0.2)

    scaled_frame = pygame.transform.smoothscale(border_frame, (frame_size, frame_size))

    gate_scale_factor = 0.18
    gate_size = int(frame_size * gate_scale_factor)
    active_gate_image = pygame.transform.smoothscale(gate_image, (gate_size, gate_size))

    center_x, center_y = frame_x + frame_size / 2, frame_y + frame_size / 2
    positions = [
        (center_x + active_circle_radius * np.cos(2 * np.pi * i / NUM_OVALS),
         center_y + active_circle_radius * np.sin(2 * np.pi * i / NUM_OVALS))
        for i in range(NUM_OVALS)
    ]
    gate_caption = caption_font.render("Wicket Gate Display", True, text_color)
    screen.blit(gate_caption, (frame_x + frame_size / 2 - gate_caption.get_width() / 2, frame_y - SCREEN_HEIGHT * 0.055))

    # Title
    title_text = title_font.render("Controls", True, text_color)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 4, int(SCREEN_HEIGHT * 0.07)))
    screen.blit(title_text, title_rect)

    # Arrow keys
    draw_arrow_keys(screen, SCREEN_WIDTH // 4, int(SCREEN_HEIGHT * 0.28), 'up' if show_pressed_keys else 'down')

    # Keyboard caption
    up_caption = caption_font.render("Press up/down to open/close the wicket gate.", True, text_color)
    up_caption_rect = up_caption.get_rect(center=(SCREEN_WIDTH // 4, int(SCREEN_HEIGHT * 0.42)))
    screen.blit(up_caption, up_caption_rect)

    # Mouse image
    mouse_image_original = load_image("assets/RoRStatics/mouse.png")
    original_size = mouse_image_original.get_size()
    scale_factor = SCREEN_HEIGHT * 0.00055
    new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
    mouse_image = pygame.transform.smoothscale(mouse_image_original, new_size)
    mouse_rect = mouse_image.get_rect(center=(SCREEN_WIDTH // 4, int(SCREEN_HEIGHT * 0.72)))

    scroll_up_image = load_image("assets/RoRStatics/Scroll_Up.png")
    scroll_down_image = load_image("assets/RoRStatics/Scroll_Down.png")
    rect_width = int(SCREEN_WIDTH * 0.01)
    rect_height = int(SCREEN_HEIGHT * 0.054)
    rect_x = int(SCREEN_WIDTH * 0.246)
    rect_y = int(SCREEN_HEIGHT * 0.63)
   
    if show_blinking_rect: #Show Up
        scroll_up_image = pygame.transform.smoothscale(scroll_up_image, (rect_width, rect_height))
        screen.blit(scroll_up_image, (rect_x, rect_y))
    else: #Show Down
        scroll_down_image = pygame.transform.smoothscale(scroll_down_image, (rect_width, rect_height))
        screen.blit(scroll_down_image, (rect_x, rect_y))
        angles = [angle + 50 for angle in angles]

    screen.blit(mouse_image, mouse_rect)

    # Mouse caption
    mouse_caption = caption_font.render("Scroll up/down to open/close the wicket gate.", True, text_color)
    mouse_caption_rect = mouse_caption.get_rect(center=(SCREEN_WIDTH // 4, int(SCREEN_HEIGHT * 0.92)))
    screen.blit(mouse_caption, mouse_caption_rect)

    screen.blit(scaled_frame, (frame_x, frame_y))

    # Draw rotating gates
    for i, (pos_x, pos_y) in enumerate(positions):
        rotated_image = pygame.transform.rotozoom(active_gate_image, angles[i], 1.0)
        rect = rotated_image.get_rect(center=(pos_x, pos_y))
        screen.blit(rotated_image, rect.topleft)

def reset_RoR():
    return {
        'rotation': 90,
        'release': 0.0,
        'power_data': [],
        'x_start': 0,
        'x_end': 5,
        'level_complete': False,
        'angles': [],
        'center_x': 0,
        'center_y': 0,
        'score': 0.0,
        'elapsed_time': 0.0,
        'positions': []
    }

def update_RoR_graph(x_start=0, x_end=5, power_data=[], display=0,mode=0):
    global LOAD_CURVE, SCREEN_WIDTH
    x = np.linspace(x_start, x_end, 100)
    power_x = np.linspace(x_start, x_start + 0.5, len(power_data))
    plt.figure(figsize=(4, 3), facecolor=(0, 0, 0, 0))
    ax = plt.gca()
    ax.set_facecolor((0, 0, 0, 0))
    plt.plot(power_x, power_data, label='Power Generated', color='red')
    indices = (np.arange(display, display + 100) % len(LOAD_CURVE))
    plt.plot(x, LOAD_CURVE[indices]/110, label='Load Curve', color='white')
    plt.xlim(x_start, x_end)
    plt.ylim(0, 6)
    plt.axis('off')

    if mode == 0:
        legend = plt.legend(loc='upper right', facecolor='none', edgecolor='none')
    elif mode == 2:
        legend = plt.legend(loc='lower left', facecolor='none', edgecolor='none')

    for text in legend.get_texts():
        text.set_color('white')

    plt.tight_layout()
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=400, transparent=True)
    plt.close()
    return temp_file.name

# --- Dam Level Functions ---
def draw_controls_page_dam(screen, show_pressed_keys, show_blinking_rect):
    # Colors
    text_color = (255, 255, 255)

    # Fonts relative to height
    pygame.font.init()
    title_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.09))
    caption_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Regular.ttf"), int(SCREEN_HEIGHT * 0.045))

    # Background
    background = load_image("assets/DamSequences/DamStatics/DamStatics.jpg")
    background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
    screen.blit(background, (0, 0))

    # Title
    title_text = title_font.render("Controls", True, text_color)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, int(SCREEN_HEIGHT * 0.07)))
    screen.blit(title_text, title_rect)

    # Arrow keys
    draw_arrow_keys(screen, SCREEN_WIDTH // 2, int(SCREEN_HEIGHT * 0.28), 'up' if show_pressed_keys else 'down')

    # Keyboard caption
    up_caption = caption_font.render("Press up/down to open/close the gates.", True, text_color)
    up_caption_rect = up_caption.get_rect(center=(SCREEN_WIDTH // 2, int(SCREEN_HEIGHT * 0.42)))
    screen.blit(up_caption, up_caption_rect)

    # Mouse image
    mouse_image_original = load_image("assets/RoRStatics/mouse.png")
    original_size = mouse_image_original.get_size()
    scale_factor = SCREEN_HEIGHT * 0.00055
    new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
    mouse_image = pygame.transform.smoothscale(mouse_image_original, new_size)
    mouse_rect = mouse_image.get_rect(center=(SCREEN_WIDTH // 2, int(SCREEN_HEIGHT * 0.72)))

    scroll_up_image = load_image("assets/RoRStatics/Scroll_Up.png")
    scroll_down_image = load_image("assets/RoRStatics/Scroll_Down.png")
    rect_width = int(SCREEN_WIDTH * 0.011)
    rect_height = int(SCREEN_HEIGHT * 0.054)
    rect_x = int(SCREEN_WIDTH * 0.496)
    rect_y = int(SCREEN_HEIGHT * 0.63)
   
    if show_blinking_rect: #Show Up
        scroll_up_image = pygame.transform.smoothscale(scroll_up_image, (rect_width, rect_height))
        screen.blit(scroll_up_image, (rect_x, rect_y))
    else: #Show Down
        scroll_down_image = pygame.transform.smoothscale(scroll_down_image, (rect_width, rect_height))
        screen.blit(scroll_down_image, (rect_x, rect_y))

    screen.blit(mouse_image, mouse_rect)

    # Mouse caption
    mouse_caption = caption_font.render("Scroll up/down to open/close the gates.", True, text_color)
    mouse_caption_rect = mouse_caption.get_rect(center=(SCREEN_WIDTH // 2, int(SCREEN_HEIGHT * 0.92)))
    screen.blit(mouse_caption, mouse_caption_rect)

def load_bar_frames():
    frames = []
    for i in range(BAR_IMAGE_COUNT):
        try:
            path = resource_path(BAR_IMAGE_PATH_TEMPLATE.format(i))
            image = pygame.image.load(path).convert_alpha()
            rotated_bar_image = pygame.transform.rotate(image, 90)
            image = pygame.transform.scale(rotated_bar_image, ((image.get_size()[0]*SCREEN_WIDTH/1920)/2, (image.get_size()[1]*SCREEN_HEIGHT/1080)))
            frames.append(image)
        except pygame.error as e:
            print(f"Error loading bar frame {i}: {e}")
            sys.exit(1)
    return frames

def update_dam_graph(x_start=0, x_end=5, power_data=[], display=0):
    global LOAD_CURVE
    x = np.linspace(x_start, x_end, 100)

    # Calculate x-values for power data
    power_x = np.linspace(x_start, x_start + 0.5, len(power_data))

    plt.figure(figsize=(4, 3), facecolor=(0, 0, 0, 0))
    ax = plt.gca()
    ax.set_facecolor((0, 0, 0, 0))
    plt.plot(power_x, power_data, label='Power Generated', color='red')
    indices = (np.arange(display, display + 100) % len(LOAD_CURVE))
    plt.plot(x, (LOAD_CURVE[indices]/6)-15, label='Load Curve', color='white')
    plt.xlim(x_start, x_end)
    plt.ylim(-5, 100)
    plt.axis('off')

    legend = plt.legend(loc='upper right', facecolor='none', edgecolor='none', fontsize=14)
    for text in legend.get_texts():
        text.set_color('white')

    plt.tight_layout()
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=300, transparent=True)
    plt.close()
    return temp_file.name

def reset_Dam():
    """Reset game variables to initial conditions."""
    return {
        'water_level': 0,
        'water_volume': 45.0,
        'intake_rate': 2.5,
        'base_outer_flow': 4.0,
        'active_outer_flow': 4.0,
        'spillway_rate': 0.0,
        'wasted_water': 0.0,
        'gates': [0,0,0,0],
        'power_data': [],
        'x_start': 0,
        'x_end': 5,
        'game_over': False,
        'score': 0.0,
        'elapsed_time': 0.0,
        'level_complete': False
    }

def volume_to_elevation(volume,a,b):
    """Convert water volume to water elevation in the reservoir."""
    #c*sqrt+d
    elevation = np.sqrt(a * volume + b)
    return elevation

def draw_dam_colormap(Q_val, h_val):
    global fig_colormap, ax_colormap, canvas_colormap, red_dot
    if fig_colormap:
        plt.close(fig_colormap)

    if SCREEN_WIDTH == 960:
        fig_colormap, ax_colormap = plt.subplots(figsize=(2.5, 2), dpi=100)
    elif SCREEN_WIDTH == 1280:
        fig_colormap, ax_colormap = plt.subplots(figsize=(3.5, 2.5), dpi=100)
    elif SCREEN_WIDTH == 1600:
        fig_colormap, ax_colormap = plt.subplots(figsize=(4.5, 3), dpi=100)
    Q = np.linspace(0, 4, 50)
    h = np.linspace(0, 100, 200)
    Q_grid, h_grid = np.meshgrid(Q, h)
    P_grid = (Q_grid * g * h_grid)/40
    cmap = plt.get_cmap('viridis')
    c = ax_colormap.pcolormesh(Q_grid, h_grid, P_grid, shading='auto', cmap=cmap)
    cbar = fig_colormap.colorbar(c, ax=ax_colormap, label="Power P (MW)")
    cbar.ax.yaxis.label.set_color("white")
    cbar.set_ticks([])
    cbar.outline.set_edgecolor("white")
    red_dot = ax_colormap.plot(Q_val, h_val, 'ro')[0]
    ax_colormap.set_xlabel("Flow Rate Q (cfs)", color='white')
    ax_colormap.set_ylabel("Head h (ft)", color='white')
    for spine in ax_colormap.spines.values():
        spine.set_color("white")
    ax_colormap.set_xticks([])
    ax_colormap.set_yticks([])
    fig_colormap.tight_layout()
    fig_colormap.patch.set_alpha(0)         # transparent figure background
    ax_colormap.set_facecolor((0,0,0,0))    # transparent axes background
    canvas_colormap = FigureCanvasAgg(fig_colormap)
    canvas_colormap.draw()
    raw_data = canvas_colormap.get_renderer().buffer_rgba()
    size = canvas_colormap.get_width_height()
    return pygame.image.frombuffer(raw_data, size, "RGBA")

def update_dam_colormap(Q_val, h_val):
    global red_dot, canvas_colormap
    red_dot.set_data([Q_val], [h_val])
    canvas_colormap.draw()
    raw_data = canvas_colormap.get_renderer().buffer_rgba()
    size = canvas_colormap.get_width_height()
    return pygame.image.frombuffer(raw_data, size, "RGBA")

# --- PSH Level Functions ---
def draw_controls_page_PSH(screen, show_pressed_keys, show_blinking_rect):
    # Colors
    text_color = (255, 255, 255)

    # Fonts relative to height
    pygame.font.init()
    title_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.09))
    caption_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Regular.ttf"), int(SCREEN_HEIGHT * 0.045))

    # Background
    background = load_image("assets/PSHSequences/PSHStatics/PSHStatics.jpg")
    background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
    screen.blit(background, (0, 0))

    # Title
    title_text = title_font.render("Controls", True, text_color)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, int(SCREEN_HEIGHT * 0.07)))
    screen.blit(title_text, title_rect)

    # Arrow keys
    draw_arrow_keys(screen, SCREEN_WIDTH // 2, int(SCREEN_HEIGHT * 0.28), 'up' if show_pressed_keys else 'down')

    # Keyboard caption
    up_caption = caption_font.render("Press up/down to increase/decrease power generation.", True, text_color)
    up_caption_rect = up_caption.get_rect(center=(SCREEN_WIDTH // 2, int(SCREEN_HEIGHT * 0.42)))
    screen.blit(up_caption, up_caption_rect)

    # Mouse image
    mouse_image_original = load_image("assets/RoRStatics/mouse.png")
    original_size = mouse_image_original.get_size()
    scale_factor = SCREEN_HEIGHT * 0.00055
    new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
    mouse_image = pygame.transform.smoothscale(mouse_image_original, new_size)
    mouse_rect = mouse_image.get_rect(center=(SCREEN_WIDTH // 2, int(SCREEN_HEIGHT * 0.72)))

    scroll_up_image = load_image("assets/RoRStatics/Scroll_Up.png")
    scroll_down_image = load_image("assets/RoRStatics/Scroll_Down.png")
    rect_width = int(SCREEN_WIDTH * 0.011)
    rect_height = int(SCREEN_HEIGHT * 0.054)
    rect_x = int(SCREEN_WIDTH * 0.496)
    rect_y = int(SCREEN_HEIGHT * 0.63)
   
    if show_blinking_rect: #Show Up
        scroll_up_image = pygame.transform.smoothscale(scroll_up_image, (rect_width, rect_height))
        screen.blit(scroll_up_image, (rect_x, rect_y))
    else: #Show Down
        scroll_down_image = pygame.transform.smoothscale(scroll_down_image, (rect_width, rect_height))
        screen.blit(scroll_down_image, (rect_x, rect_y))

    screen.blit(mouse_image, mouse_rect)

    # Mouse caption
    mouse_caption = caption_font.render("Scroll up/down to increase/decrease power generation.", True, text_color)
    mouse_caption_rect = mouse_caption.get_rect(center=(SCREEN_WIDTH // 2, int(SCREEN_HEIGHT * 0.92)))
    screen.blit(mouse_caption, mouse_caption_rect)

def load_upper_reservoir_frames(num_frames, path_template):
    frames = []
    for i in range(num_frames):
        try:
            frame_path = resource_path(path_template.format(i))
            frame = pygame.image.load(frame_path).convert_alpha()
            frame = pygame.transform.scale(frame, (int(frame.get_size()[0]*SCREEN_WIDTH/1920)/2.5, int(frame.get_size()[1]*SCREEN_HEIGHT/1080)/2.5))
            frames.append(frame)
        except pygame.error as e:
            print(f"Error loading upper reservoir frame {i}: {e}")
            sys.exit(1)
    return frames

def update_psh_graph(x_start=0, x_end=5, power_data=[], display=0):
    global PSH_LOAD
    x = np.linspace(x_start, x_end, 100)
    power_x = np.linspace(x_start, x_start + 0.5, len(power_data))

    plt.figure(figsize=(4, 3), facecolor=(0, 0, 0, 0))
    ax = plt.gca()
    ax.set_facecolor((0, 0, 0, 0))
    plt.axhline(y=0, color='white', linestyle='--', linewidth=1)
    plt.plot(power_x, power_data, label='Power Generated', color='red')
    indices = (np.arange(display, display + 100) % len(PSH_LOAD))
    plt.plot(x, (PSH_LOAD[indices]/6)-20, label='Load Curve', color='white')
    plt.xlim(x_start, x_end)
    plt.ylim(-100, 100)
    plt.axis('off')

    legend = plt.legend(loc='upper right', facecolor='none', edgecolor='none', fontsize=14)
    for text in legend.get_texts():
        text.set_color('white')

    plt.tight_layout()
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    plt.savefig(temp_file.name, dpi=400, transparent=True)
    plt.close()
    return temp_file.name

def reset_PSH():
    return {
        'release': 0.0,
        'power_data': [],
        'score': 0.0,
        'x_start': 0,
        'x_end': 5,
        'elapsed_time': 0.0,
        'level_complete': False,
    }

def load_psh_frames(num_frames, path_template):
    frames = []
    for i in range(num_frames):
        try:
            frame_path = resource_path(path_template.format(i))
            frame = pygame.image.load(frame_path).convert_alpha()
            frame = pygame.transform.scale(frame, (int(frame.get_size()[0]*SCREEN_WIDTH/1920), int(frame.get_size()[1]*SCREEN_HEIGHT/1080)))
            frames.append(frame)
        except pygame.error as e:
            print(f"Error loading frame {i}: {e}")
            sys.exit(1)
    return frames

# --- Environment Functions ---
def get_bg_color(game):
    return (30, 30, 30) if game['dark_mode'] else (255, 255, 255)

def get_text_color(game):
    return (255, 255, 255) if game['dark_mode'] else (0, 0, 0)

def get_panel_color(game):
    return (80, 80, 80) if game['dark_mode'] else (200, 200, 200)

def get_button_color(game):
    return (100, 100, 100) if game['dark_mode'] else (180, 180, 200)

def get_button_outline_color(game):
    return (255, 255, 255) if game['dark_mode'] else (0, 0, 0)

def reset_env():
    global SCREEN_WIDTH, SCREEN_HEIGHT, TARGET
    return {
        'window_width': SCREEN_WIDTH,
        'window_height': SCREEN_HEIGHT,
        'screen': 0,
        'clock': 0, 
        'running': True,
        'font': None,
        'large_font': None,
        'button_font': None,
    # Flags and messages.
        'show_instructions': False,
        'message': "",
        'dark_mode': False,
        'level_complete': False,
        'best_optimality': 0,
    # Button animation settings.
        'button_anim_duration': 0.2,
        'button_animations': {},
    # Initial hourly releases.
        'y_values': (TARGET/24) * np.ones(24),
        'selected_bar': None,
        'dragging': False,
        'last_mouse_y': None,
        'start_time': time.time(),
        'solution_checked': False,
        'try_again_button_rect': None,
    # Metrics placeholders.
        'total_sum': 0,
        'total_revenue': 0,
        'maximum_ramp_up_rate': 0,
        'maximum_ramp_down_rate': 0,
        'feasible_solution': False
    }

def draw_dashed_line(surface, color, start_pos, end_pos, width=1, dash_length=10, space_length=5):
    x1, y1 = start_pos
    x2, y2 = end_pos
    dx = x2 - x1
    dy = y2 - y1
    line_length = (dx**2 + dy**2) ** 0.5
    dash_gap = dash_length + space_length
    num_dashes = int(line_length / dash_gap)
    for i in range(num_dashes + 1):
        start_fraction = i * dash_gap / line_length
        end_fraction = min((i * dash_gap + dash_length) / line_length, 1)
        start_x = x1 + dx * start_fraction
        start_y = y1 + dy * start_fraction
        end_x = x1 + dx * end_fraction
        end_y = y1 + dy * end_fraction
        pygame.draw.line(surface, color, (start_x, start_y), (end_x, end_y), width)

def update_layout(game):
    # We calculate the window size from our fixed screen.
    game['window_width'], game['window_height'] = game['screen'].get_size()
    new_font_size = max(12, int(game['window_height'] / 50))
    new_large_font_size = max(16, int(game['window_height'] / 32))
    game['font'] = pygame.font.Font(resource_path("assets/Fonts/Electrolize-Regular.ttf"), new_font_size)
    game['button_font'] = pygame.font.Font(resource_path("assets/Fonts/Gudea-Regular.ttf"), new_font_size)
    game['large_font'] = pygame.font.Font(resource_path("assets/Fonts/Gudea-Regular.ttf"), new_large_font_size)

    game['instructions_area'] = pygame.Rect(int(game['window_width'] * 0.04),
                                            int(game['window_height'] * 0.01),
                                            int(game['window_width'] * 0.92),
                                            int(game['window_height'] * 0.06))
    game['bar_graph_area'] = pygame.Rect(int(game['window_width'] * 0.08),
                                         int(game['window_height'] * 0.15),
                                         int(game['window_width'] * 0.83),
                                         int(game['window_height'] * 0.45))
    game['button_area'] = pygame.Rect(game['bar_graph_area'].x,
                                      int(game['window_height'] * 0.08),
                                      game['bar_graph_area'].width,
                                      int(game['window_height'] * 0.07))
    game['total_panel_area'] = pygame.Rect(int(game['window_width'] * 0.08),
                                           int(game['window_height'] * 0.69),
                                           int(game['window_width'] * 0.83),
                                           int(game['window_height'] * 0.15))

    button_width = int(150 * game['window_width'] / 1200)
    gap = int(50 * game['window_width'] / 1200)
    button_labels = ["Restart", "Check Solution", "Instructions", "Dark Mode"]
    total_buttons_width = len(button_labels) * button_width + (len(button_labels) - 1) * gap
    start_x = game['button_area'].x + (game['button_area'].width - total_buttons_width) // 2

    button_height = int(40 * game['window_height'] / 900)
    button_y = game['button_area'].y + (game['button_area'].height - button_height) // 2
    buttons = {}
    for i, label in enumerate(button_labels):
        buttons[label] = pygame.Rect(start_x + i * (button_width + gap),
                                     button_y, button_width, button_height)
    game['buttons'] = buttons

    panel_margin = int(10 * game['window_width'] / 1200)
    labels = ["Total revenue", "Total release", "Maximum ramp up", "Maximum ramp down"]
    panel_count = len(labels)
    panel_width = (game['total_panel_area'].width - (panel_count - 1) * panel_margin) // panel_count
    panel_height = game['total_panel_area'].height
    total_bar_graphs = {}
    for i, label in enumerate(labels):
        x = game['total_panel_area'].x + i * (panel_width + panel_margin)
        y = game['total_panel_area'].y
        total_bar_graphs[label] = pygame.Rect(x, y, panel_width, panel_height)
    game['total_bar_graphs'] = total_bar_graphs

    # Define the exit button rectangle relative to the window size.
    exit_width = int(80 * game['window_width'] / 800)
    exit_height = int(40 * game['window_height'] / 600)
    game['exit_button_rect'] = pygame.Rect(int(game['window_width'] * 0.02),
                                             int(game['window_height'] * 0.02),
                                             exit_width, exit_height)
    
def update_metrics(game):
    game['total_sum'] = np.sum(game['y_values'])
    game['total_revenue'] = np.sum(game['y_values'] * price_values)
    game['minimum_release_rate'] = np.min(game['y_values'])
    if len(game['y_values']) > 1:
        ramp_rate = game['y_values'][1:] - game['y_values'][:-1]
        game['maximum_ramp_up_rate'] = np.max(ramp_rate)
        game['maximum_ramp_down_rate'] = np.max(-ramp_rate)
    else:
        game['maximum_ramp_up_rate'] = 0
        game['maximum_ramp_down_rate'] = 0
    game['feasible_total_sum'] = abs(game['total_sum'] - TARGET) <= target_tol
    game['feasible_ramp_up'] = game['maximum_ramp_up_rate'] <= (max_ramp_up + 0.1 * target_tol)
    game['feasible_ramp_down'] = game['maximum_ramp_down_rate'] <= (max_ramp_down + 0.1 * target_tol)
    game['feasible_solution'] = (game['feasible_total_sum'] and game['feasible_ramp_up'] and game['feasible_ramp_down'])

def draw_timer(game):
    elapsed = time.time() - game['start_time']
    timer_text = game['font'].render(f"Time: {int(elapsed)}s", True, get_text_color(game))
    timer_rect = timer_text.get_rect(topright=(
        game['window_width'] - int((20/800)*game['window_width']),
        int((20/600)*game['window_height'])
    ))
    game['screen'].blit(timer_text, timer_rect)
    revenue_pct = 0
    if optimal_value:
        revenue_pct = 100 * game['total_revenue'] / optimal_value
    if game['feasible_solution'] and revenue_pct <= 100:
        pct_str = f"Optimality: {revenue_pct:.0f}%"
    else:
        pct_str = "Optimality: --"
    pct_text = game['font'].render(pct_str, True, get_text_color(game))
    pct_rect = pct_text.get_rect(topright=(
        game['window_width'] - int((20/800)*game['window_width']),
        timer_rect.bottom + int((5/600)*game['window_height'])
    ))
    game['screen'].blit(pct_text, pct_rect)
    # Only display "Best:" if solution is checked and feasible; otherwise show "--"
    if game['solution_checked'] and game['feasible_solution']:
        best_str = f"Best: {game.get('best_optimality', 0):.0f}%"
    else:
        best_str = "Best: --"
    best_text = game['font'].render(best_str, True, get_text_color(game))
    best_rect = best_text.get_rect(topright=(
        game['window_width'] - int((20/800)*game['window_width']),
        pct_rect.bottom + int((5/600)*game['window_height'])
    ))
    game['screen'].blit(best_text, best_rect)
    feas_text = "Feasible!" if (game['feasible_solution']) else "Infeasible"
    feas_color = (0, 200, 0) if (game['feasible_solution']) else (200, 0, 0)
    feas_line = game['font'].render(feas_text, True, feas_color)
    feas_rect = feas_line.get_rect(topright=(
        game['window_width'] - int((20/800)*game['window_width']),
        best_rect.bottom + int((5/600)*game['window_height'])
    ))
    game['screen'].blit(feas_line, feas_rect)

def draw_bar_graph(game):
    screen = game['screen']
    bar_graph_area = game['bar_graph_area']
    pygame.draw.rect(screen, get_panel_color(game), bar_graph_area, 2)
    max_value = 5000
    pygame.draw.line(screen, get_text_color(game),
                     (bar_graph_area.x, bar_graph_area.y),
                     (bar_graph_area.x, bar_graph_area.y + bar_graph_area.height), 2)
    tick_interval = 1000
    num_ticks = int(max_value / tick_interval) + 1
    for i in range(num_ticks):
        tick_value = i * tick_interval
        y = bar_graph_area.y + bar_graph_area.height - (tick_value / max_value) * bar_graph_area.height
        pygame.draw.line(screen, get_text_color(game),
                         (bar_graph_area.x - int((5/800)*game['window_width']), y),
                         (bar_graph_area.x, y), 2)
        tick_label = game['font'].render(f"{tick_value:,}", True, get_text_color(game))
        screen.blit(tick_label, (bar_graph_area.x - int((35/800)*game['window_width']), y - int((10/600)*game['window_height'])))
    pygame.draw.line(screen, get_text_color(game),
                     (bar_graph_area.x, bar_graph_area.y + bar_graph_area.height),
                     (bar_graph_area.x + bar_graph_area.width, bar_graph_area.y + bar_graph_area.height), 2)
    # Draw the bars.
    left_margin = int((5/800)*game['window_width'])
    available_width = bar_graph_area.width - left_margin
    bar_width = available_width / N_timesteps
    for i in range(N_timesteps):
        x = int(bar_graph_area.x + left_margin + i * bar_width)
        value = game['y_values'][i]
        bar_height = int((value / max_value) * bar_graph_area.height)
        y = int(bar_graph_area.y + bar_graph_area.height - bar_height)
        color = (31, 119, 180)
        pygame.draw.rect(screen, color, (x, y, int(bar_width) - 2, bar_height))
        text = game['font'].render(f"{int(value)}", True, get_text_color(game))
        text_rect = text.get_rect(center=(x + bar_width / 2, y - int((10/600)*game['window_height'])))
        screen.blit(text, text_rect)

    # Draw price points.
    price_points = []
    for i in range(N_timesteps):
        x = bar_graph_area.x + left_margin + (i + 0.5) * bar_width
        y = bar_graph_area.y + bar_graph_area.height - (price_values[i] / max_value) * bar_graph_area.height
        price_points.append((x, y))
    if len(price_points) >= 2:
        pygame.draw.lines(screen, (255,0,0), False, price_points, 2)

    # Draw dashed lines (thresholds) after drawing bars & price points so they appear on top.
    dashed_y_0_2 = bar_graph_area.y + bar_graph_area.height - (400 / max_value) * bar_graph_area.height
    dashed_y_2_0 = bar_graph_area.y + bar_graph_area.height - (4000 / max_value) * bar_graph_area.height
    draw_dashed_line(screen, get_text_color(game),
                     (bar_graph_area.x, dashed_y_0_2),
                     (bar_graph_area.x + bar_graph_area.width, dashed_y_0_2),
                     width=2, dash_length=5, space_length=3)
    draw_dashed_line(screen, get_text_color(game),
                     (bar_graph_area.x, dashed_y_2_0),
                     (bar_graph_area.x + bar_graph_area.width, dashed_y_2_0),
                     width=2, dash_length=5, space_length=3)
    
    # Dynamically size the legend based on the bar graph dimensions.
    legend_width = int(game['bar_graph_area'].width * 0.2)
    legend_height = int(game['bar_graph_area'].height * 0.2)
    legend_x = game['bar_graph_area'].right - legend_width - int((0.02)*game['window_width'])
    legend_y = game['bar_graph_area'].y + int((0.02)*game['window_height'])
    legend_rect = pygame.Rect(legend_x, legend_y, legend_width, legend_height)
    pygame.draw.rect(screen, get_panel_color(game), legend_rect)
    pygame.draw.rect(screen, get_text_color(game), legend_rect, 2)
    dash_start = (legend_rect.x + int((0.07)*legend_width), legend_rect.y + int((0.25)*legend_height))
    dash_end = (legend_rect.x + int((0.2)*legend_width), legend_rect.y + int((0.25)*legend_height))
    draw_dashed_line(screen, get_text_color(game), dash_start, dash_end, width=2, dash_length=4, space_length=3)
    release_limit_text = game['font'].render("Release limit (cfs)", True, get_text_color(game))
    screen.blit(release_limit_text, (legend_rect.x + int((0.3)*legend_width), legend_rect.y + int((0.1)*legend_height)))
    pygame.draw.rect(screen, (31, 119, 180), (legend_rect.x + int((0.07)*legend_width), legend_rect.y + int((0.49)*legend_height), int((0.15)*legend_width), int((0.15)*legend_height)))
    rel_text = game['font'].render("Releases (cfs)", True, get_text_color(game))
    screen.blit(rel_text, (legend_rect.x + int((0.3)*legend_width), legend_rect.y + int((0.41)*legend_height)))
    price_curve_text = game['font'].render("Price ($/MWh)", True, get_text_color(game))
    screen.blit(price_curve_text, (legend_rect.x + int((0.3)*legend_width), legend_rect.y + int((0.71)*legend_height)))
    pygame.draw.line(screen, (255, 0, 0), (legend_rect.x + int((0.07)*legend_width), legend_rect.y + int((0.83)*legend_height)), (legend_rect.x + int((0.2)*legend_width), legend_rect.y + int((0.83)*legend_height)), 2)

    y_axis_title = game['font'].render("Hourly release (cfs)", True, get_text_color(game))
    y_axis_title_rotated = pygame.transform.rotate(y_axis_title, 90)
    y_title_rect = y_axis_title_rotated.get_rect(center=(bar_graph_area.x - int((50/800)*game['window_width']),
                                                         bar_graph_area.centery))
    screen.blit(y_axis_title_rotated, y_title_rect)

    x_axis_title = game['font'].render("Hours", True, get_text_color(game))
    screen.blit(x_axis_title,(SCREEN_WIDTH//2 - x_axis_title.get_width()//1.35,0.62*SCREEN_HEIGHT))

def draw_total_bars(game):
    screen = game['screen']
    total_bar_graphs = game['total_bar_graphs']
    metrics = {
        "Total revenue": (game['total_revenue'], optimal_value, "Optimal value"),
        "Total release": (game['total_sum'], TARGET, "Total Release Volume"),
        "Maximum ramp up": (game['maximum_ramp_up_rate'], max_ramp_up, "Ramp up limit"),
        "Maximum ramp down": (game['maximum_ramp_down_rate'], max_ramp_down, "Ramp down limit"),
    }
    for key, rect in total_bar_graphs.items():
        if key not in metrics:
            continue
        value, target_value, target_name = metrics[key]
        pygame.draw.rect(screen, get_panel_color(game), rect, 2)
        max_display = target_value * 1.5 if target_value != 0 else 1
        calculated_bar_height = (value / max_display) * rect.height
        bar_height = min(calculated_bar_height, rect.height)
        bar_bottom_y = rect.y + rect.height
        bar_rect = pygame.Rect(
            rect.x + int((10/800)*game['window_width']),
            bar_bottom_y - bar_height,
            rect.width - int((20/800)*game['window_width']),
            bar_height
        )

        if key == "Total revenue":
            color = (31, 119, 180)
            if abs(value - target_value) <= target_tol:
                color = (0, 200, 0)
        elif key == "Total release":
            color = (0, 200, 0) if abs(value - target_value) <= target_tol else (200, 0, 0)
        elif key == "Maximum ramp up":
            color = (200, 0, 0)
            if value <= (target_value + 0.1 * target_tol):
                color = (0, 200, 0)
        elif key == "Maximum ramp down":
            color = (200, 0, 0)
            if value <= (target_value + 0.1 * target_tol):
                color = (0, 200, 0)

        pygame.draw.rect(screen, color, bar_rect)
        axis_y = rect.y + rect.height - (target_value / max_display) * rect.height
        draw_dashed_line(screen, get_text_color(game),
                         (rect.x, axis_y),
                         (rect.x + rect.width, axis_y),
                         width=2, dash_length=10, space_length=5)
        label = game['font'].render(f"{key}", True, get_text_color(game))
        label_rect = label.get_rect(center=(rect.centerx, rect.y - int((10/600)*game['window_height'])))
        screen.blit(label, label_rect)
        target_label = game['font'].render(target_name, True, get_text_color(game))
        target_label_rect = target_label.get_rect(center=(rect.centerx, axis_y - int((10/600)*game['window_height'])))
        screen.blit(target_label, target_label_rect)

def draw_buttons(game):
    screen = game['screen']
    # Draw standard buttons.
    for label, rect in game['buttons'].items():
        anim_scale = 1.0
        if label in game['button_animations']:
            elapsed = time.time() - game['button_animations'][label]
            if elapsed < game['button_anim_duration']:
                progress = elapsed / game['button_anim_duration']
                if progress < 0.5:
                    anim_scale = 1 - 0.1 * (progress / 0.5)
                else:
                    anim_scale = 0.9 + 0.1 * ((progress - 0.5) / 0.5)
            else:
                del game['button_animations'][label]
        scaled_width = int(rect.width * anim_scale)
        scaled_height = int(rect.height * anim_scale)
        scaled_rect = pygame.Rect(0, 0, scaled_width, scaled_height)
        scaled_rect.center = rect.center
        pygame.draw.rect(screen, get_button_color(game), scaled_rect)
        pygame.draw.rect(screen, get_button_outline_color(game), scaled_rect, 2)
        display_label = label
        if label == "Dark Mode":
            display_label = f"Dark Mode: {'On' if game['dark_mode'] else 'Off'}"
        text = game['button_font'].render(display_label, True, get_text_color(game))
        text_rect = text.get_rect(center=scaled_rect.center)
        screen.blit(text, text_rect)

    # Draw clickable red exit button with animation.
    if "Exit" in game['button_animations']:
        elapsed = time.time() - game['button_animations']["Exit"]
        if elapsed < game['button_anim_duration']:
            progress = elapsed / game['button_anim_duration']
            if progress < 0.5:
                exit_scale = 1 - 0.1 * (progress / 0.5)
            else:
                exit_scale = 0.9 + 0.1 * ((progress - 0.5) / 0.5)
        else:
            del game['button_animations']["Exit"]
            exit_scale = 1.0
    else:
        exit_scale = 1.0

    exit_rect_orig = game['exit_button_rect']
    scaled_exit_width = int(exit_rect_orig.width * exit_scale)
    scaled_exit_height = int(exit_rect_orig.height * exit_scale)
    scaled_exit_rect = pygame.Rect(0, 0, scaled_exit_width, scaled_exit_height)
    scaled_exit_rect.center = exit_rect_orig.center
    pygame.draw.rect(screen, (200, 0, 0), scaled_exit_rect)  # Red fill.
    pygame.draw.rect(screen, (255, 255, 255), scaled_exit_rect, 2)  # White outline.
    exit_text = game['button_font'].render("Exit", True, (255, 255, 255))
    exit_text_rect = exit_text.get_rect(center=scaled_exit_rect.center)
    screen.blit(exit_text, exit_text_rect)

def draw_message(game):
    if game['message']:
        overlay = pygame.Surface((game['window_width'], game['window_height']), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        game['screen'].blit(overlay, (0, 0))
        lines = game['message'].split("\n")
        text_rects = []
        for i, line in enumerate(lines):
            text = game['large_font'].render(line, True, (255, 255, 255))
            # Render each line with a vertical offset proportional to the window height.
            text_rect = text.get_rect(center=(game['window_width'] // 2,
                                              game['window_height'] // 2 - int((50/600)*game['window_height']) + i * int((40/600)*game['window_height'])))
            game['screen'].blit(text, text_rect)
            text_rects.append(text_rect)
        # Place the Close button below the message text block.
        if text_rects:
            btn_y = max(rect.bottom for rect in text_rects) + int((40/600)*game['window_height'])
        else:
            btn_y = game['window_height'] // 2 + int((90/600)*game['window_height'])
        btn_label = "Close"
        btn_width = int(150 * game['window_width'] / 1200)
        btn_height = int(40 * game['window_height'] / 900)
        btn_x = (game['window_width'] - btn_width) // 2
        game['try_again_button_rect'] = pygame.Rect(btn_x, btn_y, btn_width, btn_height)
        pygame.draw.rect(game['screen'], get_button_color(game), game['try_again_button_rect'])
        pygame.draw.rect(game['screen'], get_button_outline_color(game), game['try_again_button_rect'], 2)
        btn_text = game['button_font'].render(btn_label, True, get_text_color(game))
        btn_text_rect = btn_text.get_rect(center=game['try_again_button_rect'].center)
        game['screen'].blit(btn_text, btn_text_rect)
        if game.get('level_complete'):
            lc_label = "Level Complete"
            lc_btn_width = int(150 * game['window_width'] / 1200)
            lc_btn_height = int(40 * game['window_height'] / 900)
            lc_btn_x = (game['window_width'] - lc_btn_width) // 2
            lc_btn_y = btn_y + lc_btn_height + int((10/600)*game['window_height'])
            game['level_complete_button_rect'] = pygame.Rect(lc_btn_x, lc_btn_y, lc_btn_width, lc_btn_height)
            pygame.draw.rect(game['screen'], get_button_color(game), game['level_complete_button_rect'])
            pygame.draw.rect(game['screen'], get_button_outline_color(game), game['level_complete_button_rect'], 2)
            lc_text = game['button_font'].render(lc_label, True, get_text_color(game))
            lc_text_rect = lc_text.get_rect(center=game['level_complete_button_rect'].center)
            game['screen'].blit(lc_text, lc_text_rect)

def handle_button_click(game, pos):
    for label, rect in game['buttons'].items():
        if rect.collidepoint(pos):
            game['button_animations'][label] = time.time()
            if label == "Restart":
                start_action(game)
            elif label == "Check Solution":
                check_action(game)
            elif label == "Instructions":
                game['show_instructions'] = True
                game['message'] = "\n Find the best hydropower revenue by changing the hourly releases - click and drag the bars to adjust. \n The curve represents the price of energy at each hour, and is your guide to maximize revenue. \n Ensure all environmental rules are met: daily target, minimum release, maximum ramp up, and maximum ramp down. \n To complete the level, you must obtain both a feasible solution and at least a 90% optimality, then check your solution."
            elif label == "Dark Mode":
                game['dark_mode'] = not game['dark_mode']
            return
        
def start_action(game):
    game['y_values'] = (TARGET/24) * np.ones(24)
    game['solution_checked'] = False
    game['start_time'] = time.time()
    game['message'] = ""
    game['show_instructions'] = False
    game['level_complete'] = False

def check_action(game):
    global revenue_pct
    update_metrics(game)
    time_to_find = time.time() - game['start_time']
    revenue_pct = 100 * game['total_revenue'] / optimal_value if optimal_value else 0
    if game['feasible_solution']:
        if revenue_pct >= 90:
            game['message'] = (f"Solution is feasible! You reached >90% optimality!\nTime: {time_to_find:.0f}s\nOptimality: {revenue_pct:.0f}%")
            if revenue_pct > game.get('best_optimality', 0):
                game['best_optimality'] = revenue_pct
        else:
            game['message'] = (f"Solution is feasible! However, you need to achieve at least a 90% optimality. Try again!\nTime: {time_to_find:.0f}s")
    else:
        game['message'] = (f"Solution is not feasible. Try again!\nTime: {time_to_find:.0f}s")
    
    game['solution_checked'] = True
    game['level_complete'] = game['feasible_solution'] and (revenue_pct >= 90)
    # Do not reset the timer here.

def handle_events_env(game):
    global level_completed, revenue_pct, level_scores
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_game_data()
            pygame.quit()
            sys.exit()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                pos = event.pos
                # Check if the exit button was clicked.
                if game['exit_button_rect'].collidepoint(pos):
                    game['button_animations']["Exit"] = time.time()
                    game['running'] = False
                    break

                if game['message']:
                    if (game.get('try_again_button_rect')
                            and game['try_again_button_rect'].collidepoint(pos)):
                        game['message'] = ""
                        game['show_instructions'] = False
                        continue
                    if (game.get('level_complete_button_rect')
                            and game['level_complete_button_rect'].collidepoint(pos)):
                        level_completed[4] = True
                        if level_scores[4] < int((revenue_pct-90)*1000):
                            level_scores[4] = int((revenue_pct-90)*1000)
                        game['running'] = False
                        break
                if game['button_area'].collidepoint(pos):
                    handle_button_click(game, pos)
                elif game['bar_graph_area'].collidepoint(pos):
                    bar_width = game['bar_graph_area'].width / N_timesteps
                    rel_x = pos[0] - game['bar_graph_area'].x
                    bar_index = int(rel_x // bar_width)
                    if 0 <= bar_index < N_timesteps:
                        game['selected_bar'] = bar_index
                        game['dragging'] = True
                        game['last_mouse_y'] = pos[1]

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                game['dragging'] = False
                game['selected_bar'] = None

        elif event.type == pygame.MOUSEMOTION:
            if game['dragging'] and game['selected_bar'] is not None:
                dy = game['last_mouse_y'] - event.pos[1]
                sensitivity = 4.5
                delta = dy * sensitivity
                new_value = np.clip(game['y_values'][game['selected_bar']] + delta, 400, 4000)
                game['y_values'][game['selected_bar']] = new_value
                game['last_mouse_y'] = event.pos[1]

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game['message'] = ""
                game['show_instructions'] = False

# --- Load all assets once ---
assets_path = "assets/Transitions"

background = pygame.image.load(resource_path(os.path.join(assets_path, "Background.jpg"))).convert()
background1 = pygame.transform.smoothscale(background, (960, 540))
background2 = pygame.transform.smoothscale(background, (1280, 720))
background3 = pygame.transform.smoothscale(background, (1600, 900))

border_frame = load_image("assets/IKM_Assets/BorderFrame.png")
control_panel = load_image('assets/IKM_Assets/ControlPanel.png')
up_active = load_image('assets/IKM_Assets/UpButtonActive.png')
up_inactive = load_image('assets/IKM_Assets/UpButtonInactive.png')
down_active = load_image('assets/IKM_Assets/DownButtonActive.png')
down_inactive = load_image('assets/IKM_Assets/DownButtonInactive.png')

argonne_logo = load_image(os.path.join(assets_path, "ArgonneLogo.png"))
nrel_logo = load_image(os.path.join(assets_path, "NRELLogo.png"))
doe_logo = load_image(os.path.join(assets_path, "DOELogo.png"))

# Scale logos
logo_scale = 0.4
argonne_logo = pygame.transform.smoothscale(argonne_logo, (int(argonne_logo.get_width() * logo_scale),
                                                     int(argonne_logo.get_height() * logo_scale)))
nrel_logo = pygame.transform.smoothscale(nrel_logo, (int(nrel_logo.get_width() * logo_scale),
                                               int(nrel_logo.get_height() * logo_scale)))
doe_logo = pygame.transform.smoothscale(doe_logo, (int(doe_logo.get_width() * logo_scale),
                                             int(doe_logo.get_height() * logo_scale)))

# --- Opening screen ---
def opening_screen(background, argonne_logo, nrel_logo, doe_logo):
    # Fonts
    font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), 50)
    title_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), 140)
    prompt_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), 40)

    # Text surfaces
    developed_text = font.render("An educational tool developed by", True, (255, 255, 255))
    funded_text = font.render("Funded by", True, (255, 255, 255))
    title_text1 = title_font.render("Hydropower Market", True, (173, 216, 230))
    title_text2 = title_font.render("Game", True, (173, 216, 230))
    prompt_text = prompt_font.render("Click anywhere to start!", True, (255, 255, 255))

    developed_rect = developed_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.2))
    funded_rect = funded_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.2))

    # Title positions (two lines)
    total_height = title_text1.get_height() + title_text2.get_height() + 10
    title_rect1 = title_text1.get_rect(center=(SCREEN_WIDTH / 2,
                                               SCREEN_HEIGHT / 2 - total_height / 2 + title_text1.get_height() / 2))
    title_rect2 = title_text2.get_rect(center=(SCREEN_WIDTH / 2,
                                               SCREEN_HEIGHT / 2 + total_height / 2 - title_text2.get_height() / 2))
    prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.85))

    # Logo positions
    argonne_rect = argonne_logo.get_rect(center=(SCREEN_WIDTH * 0.3, SCREEN_HEIGHT * 0.5))
    nrel_rect = nrel_logo.get_rect(center=(SCREEN_WIDTH * 0.7, SCREEN_HEIGHT * 0.5))
    doe_rect = doe_logo.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.5))

    alpha = 0
    phase = "fade_in_dev"
    fade_speed = 10
    hold_time = 60
    hold_counter = 0
    finished = False

    # Sponsor phase
    while not finished:
        screen.fill((0,0,0))

        if phase in ("fade_in_dev", "hold_dev", "fade_out_dev"):
            developed_surf = developed_text.copy()
            developed_surf.set_alpha(alpha)
            screen.blit(developed_surf, developed_rect)

            argonne_surf = argonne_logo.copy()
            argonne_surf.set_alpha(alpha)
            screen.blit(argonne_surf, argonne_rect)

            nrel_surf = nrel_logo.copy()
            nrel_surf.set_alpha(alpha)
            screen.blit(nrel_surf, nrel_rect)

            if phase == "fade_in_dev":
                alpha += fade_speed
                if alpha >= 255:
                    alpha = 255
                    phase = "hold_dev"
                    hold_counter = 0
            elif phase == "hold_dev":
                hold_counter += 1
                if hold_counter >= hold_time:
                    phase = "fade_out_dev"
            elif phase == "fade_out_dev":
                alpha -= fade_speed
                if alpha <= 0:
                    alpha = 0
                    phase = "fade_in_funded"

        elif phase in ("fade_in_funded", "hold_funded", "fade_out_funded"):
            funded_surf = funded_text.copy()
            funded_surf.set_alpha(alpha)
            screen.blit(funded_surf, funded_rect)

            doe_surf = doe_logo.copy()
            doe_surf.set_alpha(alpha)
            screen.blit(doe_surf, doe_rect)

            if phase == "fade_in_funded":
                alpha += fade_speed
                if alpha >= 255:
                    alpha = 255
                    phase = "hold_funded"
                    hold_counter = 0
            elif phase == "hold_funded":
                hold_counter += 1
                if hold_counter >= hold_time:
                    finished = True
            elif phase == "fade_out_funded":
                alpha -= fade_speed
                if alpha <= 0:
                    finished = True
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                finished = True

        pygame.display.flip()
        clock.tick(60)

    # Fade in background
    bg_alpha = 0
    bg_surface = background.copy()

    while bg_alpha < 255:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        screen.fill((255, 255, 255))
        bg_surface.set_alpha(bg_alpha)
        screen.blit(bg_surface, (0, 0))
        pygame.display.flip()

        bg_alpha += 5
        clock.tick(60)

    # Title screen with pulsing text
    pulse_alpha = 0
    pulse_increasing = True
    waiting = True
    while waiting:
        screen.blit(background, (0, 0))

        pulsing_title1 = title_text1.copy()
        pulsing_title1.set_alpha(pulse_alpha)
        screen.blit(pulsing_title1, title_rect1)

        pulsing_title2 = title_text2.copy()
        pulsing_title2.set_alpha(pulse_alpha)
        screen.blit(pulsing_title2, title_rect2)

        pulsing_prompt = prompt_text.copy()
        pulsing_prompt.set_alpha(pulse_alpha)
        screen.blit(pulsing_prompt, prompt_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                waiting = False

        if pulse_increasing:
            pulse_alpha += 3
            if pulse_alpha >= 255:
                pulse_alpha = 255
                pulse_increasing = False
        else:
            pulse_alpha -= 3
            if pulse_alpha <= 100:
                pulse_alpha = 100
                pulse_increasing = True

        pygame.display.flip()
        clock.tick(60)

def main_menu():
    global background1,background2, background3, border_frame, SCREEN_WIDTH, SCREEN_HEIGHT, has_save_file
    if has_save_file:
        menu_items = ["New Game", "Continue Game", "Settings", "Credits"]
    else:
        menu_items = ["New Game", "Settings", "Credits"]
    running = True
    while running:
        title_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.07))
        button_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.038))

        # Title text (top-left)
        title_text = title_font.render("Main Menu", True, (255, 255, 255))
        title_rect = title_text.get_rect(topleft=(SCREEN_WIDTH * 0.02, SCREEN_HEIGHT * 0.02))

        # Button dimensions: 5% of screen height
        button_height = SCREEN_HEIGHT * 0.05
        button_width = SCREEN_WIDTH * 0.25
        button_spacing = SCREEN_HEIGHT * 0.02
        start_y = SCREEN_HEIGHT * 0.2

        # Pre-scale frames
        normal_frame = pygame.transform.smoothscale(border_frame, (int(button_width), int(button_height)))
        hover_frame = normal_frame.copy()
        hover_frame.fill((50, 50, 50, 50), special_flags=pygame.BLEND_RGBA_ADD)

        # Create menu buttons
        buttons = []
        for i, label in enumerate(menu_items):
            rect = pygame.Rect(
                SCREEN_WIDTH * 0.05,
                start_y + i * (button_height + button_spacing),
                button_width,
                button_height
            )
            text_surf = button_font.render(label, True, (255, 255, 255))
            hover_text_surf = button_font.render(label, True, (173, 216, 230))
            text_rect = text_surf.get_rect(center=rect.center)
            buttons.append((label, rect, text_surf, hover_text_surf, text_rect))

        # REDi Island button (bottom right)
        redi_width = SCREEN_WIDTH * 0.25
        redi_height = SCREEN_HEIGHT * 0.05
        redi_rect = pygame.Rect(
            SCREEN_WIDTH - redi_width - SCREEN_WIDTH * 0.02,
            SCREEN_HEIGHT - redi_height - SCREEN_HEIGHT * 0.02,
            redi_width,
            redi_height
        )
        redi_frame = pygame.transform.smoothscale(border_frame, (int(redi_width), int(redi_height)))
        redi_hover_frame = redi_frame.copy()
        redi_hover_frame.fill((50, 50, 50, 50), special_flags=pygame.BLEND_RGBA_ADD)
        redi_text = button_font.render("Visit REDi Island!", True, (255, 255, 255))
        redi_hover_text = button_font.render("Visit REDi Island!", True, (173, 216, 230))
        redi_text_rect = redi_text.get_rect(center=redi_rect.center)
        # Our Website
        website_rect = pygame.Rect(
            SCREEN_WIDTH - redi_width - SCREEN_WIDTH * 0.32,
            SCREEN_HEIGHT - redi_height - SCREEN_HEIGHT * 0.02,
            redi_width,
            redi_height
        )
        website_frame = redi_frame.copy()
        website_hover_frame = redi_hover_frame.copy()
        website_text = button_font.render("Visit our official webpage!", True, (255, 255, 255))
        website_hover_text = button_font.render("Visit our official webpage!", True, (173, 216, 230))
        website_text_rect = website_text.get_rect(center=website_rect.center)

        if SCREEN_WIDTH == 960:
            screen.blit(background1, (0, 0))
        elif SCREEN_WIDTH == 1280:
            screen.blit(background2,(0,0))
        elif SCREEN_WIDTH == 1600:
            screen.blit(background3,(0,0))
        screen.blit(title_text, title_rect)

        mouse_pos = pygame.mouse.get_pos()
        # Draw menu buttons
        for label, rect, text_surf, hover_text_surf, text_rect in buttons:
            if rect.collidepoint(mouse_pos):
                screen.blit(hover_frame, rect)
                screen.blit(hover_text_surf, text_rect)
            else:
                screen.blit(normal_frame, rect)
                screen.blit(text_surf, text_rect)

        # Draw REDi Island button
        if redi_rect.collidepoint(mouse_pos):
            screen.blit(redi_hover_frame, redi_rect)
            screen.blit(redi_hover_text, redi_text_rect)
        else:
            screen.blit(redi_frame, redi_rect)
            screen.blit(redi_text, redi_text_rect)

        # Draw REDi Island button
        if website_rect.collidepoint(mouse_pos):
            screen.blit(website_hover_frame, website_rect)
            screen.blit(website_hover_text, website_text_rect)
        else:
            screen.blit(website_frame, website_rect)
            screen.blit(website_text, website_text_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Check main menu buttons
                for label, rect, _, _, _ in buttons:
                    if rect.collidepoint(mouse_pos):
                        if label == "New Game":
                            new_game()
                            character_select()
                        elif label == "Continue Game":
                            if has_save_file:
                                load_game_data()
                                level_select()
                        elif label == "Settings":
                            settings_screen()
                        elif label == "Credits":
                            credits_screen()
                        
                # Check REDi Island button
                if redi_rect.collidepoint(mouse_pos):
                    webbrowser.open("https://www1.eere.energy.gov/apps/water/redi_island/#/large-island/")
                elif website_rect.collidepoint(mouse_pos):
                    webbrowser.open("https://www.anl.gov/hydropower/hydropower-game")

        pygame.display.flip()
        clock.tick(60)

def character_select():
    global border_frame
    global hovered_index, selected_character, current_preview_index
    global ignore_mouse_hover_until_move, block_hover_if_random
    global random_selection_active, random_highlight_index, random_selection_start_time, last_interval_step
    global confirm_button_rect, confirm_clicked, name_input_rect, name_input_active, player_name
    global cursor_visible, cursor_last_switch, cursor_switch_interval

    border_frame_raw = border_frame
    face_frames_raw = load_frames(NUM_CHARACTERS, FACE_PATH_TEMPLATE)
    body_frames_raw = load_frames(NUM_CHARACTERS, BODY_PATH_TEMPLATE)

    max_body_height = int(SCREEN_HEIGHT * 0.8)
    body_frames = []
    for img in body_frames_raw:
        scale_factor = max_body_height / img.get_height()
        new_size = (int(img.get_width() * scale_factor), int(img.get_height() * scale_factor))
        body_frames.append(pygame.transform.smoothscale(img, new_size))

    grid_size = 3
    target_area_fraction = 0.2
    face_size = int((SCREEN_WIDTH * SCREEN_HEIGHT * target_area_fraction / (grid_size * grid_size)) ** 0.5)
    face_frames = [pygame.transform.smoothscale(f, (face_size, face_size)) for f in face_frames_raw]
    border_size = (face_size + 2, face_size + 2)
    border_frame = pygame.transform.smoothscale(border_frame_raw, border_size)
    green_border_frame = tint_surface(border_frame, GREEN)

    body_border_frames = []
    for body_img in body_frames:
        border_size = (body_img.get_width() + 2, body_img.get_height() + 2)
        body_border = pygame.transform.smoothscale(border_frame_raw, border_size)
        body_border_frames.append(body_border)

    video_path = resource_path("assets/CYC_Assets/Background.mp4")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Failed to open video.")
        sys.exit(1)

    button_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.03))
    exit_width = SCREEN_WIDTH * 0.15
    exit_height = SCREEN_HEIGHT * 0.06
    exit_rect = pygame.Rect(SCREEN_WIDTH * 0.765, SCREEN_HEIGHT * 0.92, exit_width, exit_height)
    exit_frame = pygame.transform.smoothscale(border_frame, (int(exit_width), int(exit_height)))
    exit_red_frame = tint_surface(exit_frame, (255, 0, 0))
    exit_text = button_font.render("Exit", True, (255, 255, 255))
    exit_text_rect = exit_text.get_rect(center=exit_rect.center)

    running = True
    while running:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (SCREEN_WIDTH, SCREEN_HEIGHT))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_surface = pygame.surfarray.make_surface(np.flipud(np.rot90(frame)))
        screen.blit(frame_surface, (0, 0))

        current_time = pygame.time.get_ticks()

        if random_selection_active:
            duration = 1000
            interval = 100
            elapsed = current_time - random_selection_start_time
            interval_step = elapsed // interval

            if interval_step != last_interval_step:
                while True:
                    temp = random.randint(0, 8)
                    if temp != 4 and temp != random_highlight_index:
                        break
                random_highlight_index = temp
                last_interval_step = interval_step

            if elapsed >= duration:
                random_selection_active = False
                selected_character = random_highlight_index
                current_preview_index = selected_character
                hovered_index = 4
                block_hover_if_random = True
                random_highlight_index = None

        mouse_pos = pygame.mouse.get_pos()
        if not ignore_mouse_hover_until_move and not random_selection_active:
            hovered_index = None
            for rect, index in face_rects:
                if rect.collidepoint(mouse_pos):
                    hovered_index = index
                    break

            if block_hover_if_random:
                if hovered_index is None or hovered_index == 4:
                    hovered_index = 4
                else:
                    block_hover_if_random = False
            if not block_hover_if_random:
                if hovered_index is not None and hovered_index != current_preview_index:
                    current_preview_index = hovered_index
                elif hovered_index is None and selected_character != 4 and selected_character != current_preview_index:
                    current_preview_index = selected_character

        
        # Cursor blink logic
        if name_input_active:
            now = pygame.time.get_ticks()
            if now - cursor_last_switch >= cursor_switch_interval:
                cursor_visible = not cursor_visible
                cursor_last_switch = now
        else:
            cursor_visible = False  # hide cursor when not active


        name_input_rect = draw_character_grid(
            face_frames, face_size, border_frame, green_border_frame,
            player_name
        )
        draw_body_preview(body_frames, current_preview_index, body_border_frames[current_preview_index])
        
        screen.blit(exit_red_frame, exit_rect)
        screen.blit(exit_text, exit_text_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if name_input_rect and name_input_rect.collidepoint(event.pos):
                    name_input_active = True
                else:
                    name_input_active = False
                if hovered_index is not None and not random_selection_active:
                    if hovered_index == 4:
                        trigger_random_selection()
                    else:
                        selected_character = hovered_index
                        current_preview_index = selected_character
                elif confirm_button_rect and confirm_button_rect.collidepoint(event.pos):
                    # Only accept confirm if valid selection and name entered
                    if selected_character != 4 and player_name.strip() != "":
                        save_game_data()
                        cap.release()
                        level_select()
                elif exit_rect.collidepoint(event.pos):
                    cap.release()
                    main_menu()
            elif event.type == pygame.MOUSEMOTION:
                ignore_mouse_hover_until_move = False
            elif event.type == pygame.KEYDOWN and name_input_active:
                if event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                elif event.key == pygame.K_RETURN:
                    name_input_active = False
                elif len(player_name) < max_name_length:
                    char = event.unicode
                    if char.isprintable():
                        player_name += char
            elif event.type == pygame.KEYDOWN and not random_selection_active:
                handle_arrow_keys(event.key)
                ignore_mouse_hover_until_move = True
        pygame.display.flip()
        clock.tick(60)

def level_select():
    global SCREEN_WIDTH, SCREEN_HEIGHT, screen, level_names, level_completed, selected_character, unlocked_levels, level_scores, has_save_file

    max_body_height = int(SCREEN_HEIGHT * 0.8)
    body_image = load_image(f"assets/CYC_Assets/Bodies/B{selected_character}.jpg")
    scale_factor = max_body_height / body_image.get_height()
    new_size = (int(body_image.get_width() * scale_factor), int(body_image.get_height() * scale_factor))
    body_image = pygame.transform.smoothscale(body_image, new_size)
    lock_image = load_image("assets/Lock.png")

    border_size = (body_image.get_width() + 2, body_image.get_height() + 2)
    body_border = pygame.transform.smoothscale(border_frame, border_size)

    score_frame = pygame.transform.smoothscale(border_frame, (int(SCREEN_WIDTH * 0.07), int(SCREEN_HEIGHT * 0.05)))

    # Video background setup
    video_path = resource_path("assets/Transitions/OperatingBackground.mp4")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Failed to open background video.")
        sys.exit(1)

    name_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.03))
    name_text = name_font.render(player_name, True, (255, 255, 255))

    preview_x = SCREEN_WIDTH - body_image.get_width() - int(SCREEN_WIDTH * 0.05)
    preview_y = (SCREEN_HEIGHT - body_image.get_height()) // 2
    text_x = preview_x + (body_image.get_width() - name_text.get_width()) // 2
    text_y = preview_y + int(body_image.get_height() * 0.85)

    title_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.06))
    level_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.025))
    button_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.03))

    title_text = title_font.render("Level Select", True, (255, 255, 255))
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH * 0.25, SCREEN_HEIGHT * 0.15))

    best_score_text = button_font.render("Best Score", True, (255, 255, 255))
    best_score_rect = best_score_text.get_rect(center=(SCREEN_WIDTH * 0.5, SCREEN_HEIGHT * 0.15))

    exit_width = SCREEN_WIDTH * 0.15
    exit_height = SCREEN_HEIGHT * 0.06
    exit_rect = pygame.Rect(SCREEN_WIDTH * 0.02, SCREEN_HEIGHT * 0.02, exit_width, exit_height)
    exit_frame = pygame.transform.smoothscale(border_frame, (int(exit_width), int(exit_height)))
    exit_red_frame = tint_surface(exit_frame, (255, 0, 0))
    exit_text = button_font.render("Exit", True, (255, 255, 255))
    exit_text_rect = exit_text.get_rect(center=exit_rect.center)

    button_width = SCREEN_WIDTH * 0.4
    button_height = SCREEN_HEIGHT * 0.08
    spacing = SCREEN_HEIGHT * 0.02
    start_x = SCREEN_WIDTH * 0.05
    total_height = len(level_names) * button_height + (len(level_names) - 1) * spacing
    start_y = (SCREEN_HEIGHT - total_height) / 2

    frame = pygame.transform.smoothscale(border_frame, (int(button_width), int(button_height)))
    green_frame = tint_surface(frame, (0, 200, 0))
    hover_frame = tint_surface(frame, (50, 50, 50))
    indicator_size = int(button_height * 0.5)
    lock_image = pygame.transform.smoothscale(lock_image, (indicator_size, indicator_size))

    play_width = button_width * 0.5
    play_height = SCREEN_HEIGHT * 0.06
    play_x = start_x + (button_width - play_width) / 2
    play_y = start_y + total_height + SCREEN_HEIGHT * 0.05
    play_rect = pygame.Rect(play_x, play_y, play_width, play_height)
    play_frame = pygame.transform.smoothscale(border_frame, (int(play_width), int(play_height)))
    play_green_frame = tint_surface(play_frame, (0, 200, 0))
    play_text = button_font.render("Play", True, (255, 255, 255))
    play_text_rect = play_text.get_rect(center=play_rect.center)

    selected_level = 0

    running = True
    while running:
        ret, frame_img = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame_img = cap.read()
        if not ret:
            break

        frame_img = cv2.resize(frame_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        frame_img = cv2.cvtColor(frame_img, cv2.COLOR_BGR2RGB)
        background = pygame.surfarray.make_surface(np.flipud(np.rot90(frame_img)))
        screen.blit(background, (0, 0))

        mouse_pos = pygame.mouse.get_pos()
        for i in range(1, len(level_names)):
            if level_completed[i - 1]:
                unlocked_levels[i] = True

        screen.blit(title_text, title_rect)
        screen.blit(best_score_text, best_score_rect)

        if level_completed[5]:
            player_role = "Power Market Operator"
        elif level_completed[4]:
            player_role = "Environmental Expert"
        elif level_completed[3]:
            player_role = "Senior Hydropower Engineer"
        elif level_completed[2]:
            player_role = "Hydropower Engineer"
        elif level_completed[1]:
            player_role = "Junior Hydropower Engineer"
        elif level_completed[0]:
            player_role = "Hydropower Intern"
        else:
            player_role = "New Hire"
        role_text = name_font.render(player_role, True, (255, 255, 255))
        role_x = preview_x + (body_image.get_width() - role_text.get_width()) // 2
        role_y = text_y + int(body_image.get_height() * 0.05)

        level_rects = []
        for i, name in enumerate(level_names):
            rect = pygame.Rect(start_x, start_y + i * (button_height + spacing),
                               button_width, button_height)
            unlocked = unlocked_levels[i] if i<5 else False
            high_score = level_scores[i]

            if i == selected_level and unlocked:
                frame_to_use = green_frame
            elif rect.collidepoint(mouse_pos) and unlocked:
                frame_to_use = hover_frame
            else:
                frame_to_use = frame
            screen.blit(frame_to_use, rect)

            if i != 0:
                screen.blit(score_frame, ((SCREEN_WIDTH * 0.5)-(score_frame.get_width()/2), rect.y + (button_height - score_frame.get_height()) / 2))

            color = (255, 255, 255) if unlocked else (150, 150, 150)
            level_text = level_font.render(name, True, color)
            level_text_rect = level_text.get_rect(midleft=(rect.left + SCREEN_WIDTH * 0.02, rect.centery))
            screen.blit(level_text, level_text_rect)
            if i != 0 and level_completed[i]:
                score_text = level_font.render(f"{high_score}", True, color)
                score_text_rect = score_text.get_rect(center=(SCREEN_WIDTH * 0.5, rect.centery))
                screen.blit(score_text, score_text_rect)

            indicator_x = rect.right - indicator_size - SCREEN_WIDTH * 0.02
            indicator_y = rect.centery - indicator_size // 2
            if not unlocked:
                screen.blit(lock_image, (indicator_x, indicator_y))

            level_rects.append((rect, unlocked))

        screen.blit(play_green_frame if unlocked_levels[selected_level] else play_frame, play_rect)
        screen.blit(play_text, play_text_rect)

        screen.blit(exit_red_frame, exit_rect)
        screen.blit(exit_text, exit_text_rect)

        draw_body_preview([body_image], 0, body_border)
        screen.blit(name_text, (text_x, text_y))
        screen.blit(role_text, (role_x, role_y))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game_data()
                cap.release()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    prev = selected_level
                    while True:
                        selected_level = (selected_level - 1) % len(level_names)
                        if unlocked_levels[selected_level] or selected_level == prev:
                            break
                elif event.key == pygame.K_DOWN:
                    prev = selected_level
                    while True:
                        selected_level = (selected_level + 1) % len(level_names)
                        if unlocked_levels[selected_level] or selected_level == prev:
                            break
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if exit_rect.collidepoint(mouse_pos):
                    has_save_file = True
                    cap.release()
                    main_menu()
                for i, (rect, unlocked) in enumerate(level_rects):
                    if rect.collidepoint(mouse_pos) and unlocked:
                        selected_level = i
                        break
                if play_rect.collidepoint(mouse_pos) and unlocked_levels[selected_level]:
                    if selected_level == 0:
                        intro_level()
                    elif selected_level == 1:
                        Level1_intro()
                        RoR_Exploration()
                        Load_Instructions(1)
                        RoR_Controls()
                        RoR_Level()
                    elif selected_level == 2:
                        Level2_intro()
                        Hydropower_Model()
                        Level2_intro_cont()
                        Dam_Exploration()
                        Load_Instructions(2)
                        Dam_Controls()
                        Dam_Level()
                    elif selected_level == 3:
                        Level3_intro()
                        PSH_Exploration()
                        Load_Instructions(3)
                        PSH_Controls()
                        PSH_Level()
                    elif selected_level == 4:
                        Level4_intro()
                        Environment_Level()

        pygame.display.flip()
        clock.tick(60)

def settings_screen():
    # Resolution options & buttons in a row
    resolutions = ["960x540", "1280x720", "1600x900"]
    # Music options & buttons in a row
    music_options = ["On", "Off"]   
    running = True
    while running:
        # Fonts
        category_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.06))
        button_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.04))

        # Text
        resolution_text = category_font.render("Resolution", True, (255, 255, 255))
        music_text = category_font.render("Music", True, (255, 255, 255))

        # Positions
        resolution_rect = resolution_text.get_rect(topleft=(SCREEN_WIDTH * 0.05, SCREEN_HEIGHT * 0.15))
        music_rect = music_text.get_rect(topleft=(SCREEN_WIDTH * 0.05, SCREEN_HEIGHT * 0.4))

        # Button size and spacing
        button_width = SCREEN_WIDTH * 0.18
        button_height = SCREEN_HEIGHT * 0.06
        button_spacing = SCREEN_WIDTH * 0.03

        # Pre-scale frames for buttons
        normal_frame = pygame.transform.smoothscale(border_frame, (int(button_width), int(button_height)))
        hover_frame = normal_frame.copy()
        hover_frame.fill((50, 50, 50, 50), special_flags=pygame.BLEND_RGBA_ADD)

        res_buttons = []
        start_x = SCREEN_WIDTH * 0.05
        y_res = resolution_rect.bottom + SCREEN_HEIGHT * 0.03
        for i, res in enumerate(resolutions):
            rect = pygame.Rect(start_x + i * (button_width + button_spacing), y_res, button_width, button_height)
            text_surf = button_font.render(res, True, (255, 255, 255))
            # Align text centered *horizontally* within button rect:
            text_rect = text_surf.get_rect(center=rect.center)
            res_buttons.append((res, rect, text_surf, text_rect))
        music_buttons = []
        start_x_music = SCREEN_WIDTH * 0.05
        y_music = music_rect.bottom + SCREEN_HEIGHT * 0.03
        for i, option in enumerate(music_options):
            rect = pygame.Rect(start_x_music + i * (button_width + button_spacing), y_music, button_width, button_height)
            text_surf = button_font.render(option, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=rect.center)
            music_buttons.append((option, rect, text_surf, text_rect))
        # Exit button (top left)
        exit_width = SCREEN_WIDTH * 0.15
        exit_height = SCREEN_HEIGHT * 0.06
        exit_rect = pygame.Rect(SCREEN_WIDTH * 0.02, SCREEN_HEIGHT * 0.02, exit_width, exit_height)
        scaled_frame = pygame.transform.smoothscale(border_frame, (int(exit_width), int(exit_height)))
        red_frame = tint_surface(scaled_frame, (255, 0, 0))
        exit_text = button_font.render("Exit", True, (255, 255, 255))
        exit_text_rect = exit_text.get_rect(center=exit_rect.center)

        mouse_pos = pygame.mouse.get_pos()

        # Draw background
        if SCREEN_WIDTH == 960:
            screen.blit(background1, (0, 0))
        elif SCREEN_WIDTH == 1280:
            screen.blit(background2,(0,0))
        elif SCREEN_WIDTH == 1600:
            screen.blit(background3,(0,0))

        # Draw categories
        screen.blit(resolution_text, resolution_rect)
        screen.blit(music_text, music_rect)

        # Draw buttons with hover effect
        for _, rect, text_surf, text_rect in res_buttons:
            if rect.collidepoint(mouse_pos):
                screen.blit(hover_frame, rect)
                screen.blit(text_surf, text_rect)
            else:
                screen.blit(normal_frame, rect)
                screen.blit(text_surf, text_rect)

        for _, rect, text_surf, text_rect in music_buttons:
            if rect.collidepoint(mouse_pos):
                screen.blit(hover_frame, rect)
                screen.blit(text_surf, text_rect)
            else:
                screen.blit(normal_frame, rect)
                screen.blit(text_surf, text_rect)

        # Draw exit button
        screen.blit(red_frame, exit_rect)
        screen.blit(exit_text, exit_text_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if exit_rect.collidepoint(mouse_pos):
                    return  # Return to main menu

                # Handle resolution clicks
                for res, rect, _, _ in res_buttons:
                    if rect.collidepoint(mouse_pos):
                        # Parse resolution and apply change_screen_size
                        width, height = map(int, res.split('x'))
                        change_screen_size(width, height)

                # Handle music clicks
                for option, rect, _, _ in music_buttons:
                    if rect.collidepoint(mouse_pos):
                        print(f"Music turned {option}")

        pygame.display.flip()
        clock.tick(60)

def credits_screen():
    # Fonts
    text_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.025))
    button_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.03))

    # Your credits text from the document
    credits_text_str = """Credits and Legal Information

Copyright © 2025, UChicago Argonne, LLC

All Rights Reserved

Software Name: Hydropower Market Game

By: UChicago Argonne, LLC

OPEN SOURCE LICENSE (MIT)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), 
to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, 
and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
· The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES 
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS 
BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Third-Party Resources and Acknowledgments

We extend our sincere gratitude to the following individuals, organizations, and resources whose contributions and publicly available information
have been invaluable in the development of the Hydropower Market Game.
Research & Data Sources:

REDi Island project: https://www.nrel.gov/water/redi-island

The REDi Island project's contribution to this game builds upon their previous collaborative work with IKM, from whom they sourced 3D models.

3D Modeling & Animation:

IKM Testing UK - For their expertise and contribution in 3D animation: https://www.ikm.com/ikm-testing-uk/3d-animation/

AI-Generated Content:

Google's Whisk and OpenAI’s ChatGPT - For the creation of AI-generated pictures used within this game.

Python Libraries:

· Standard Python Library License: Python Software Foundation License (PSF License) Copyright: 
Python Software Foundation and individual contributors URL: https://www.python.org/about/legal/

· OpenCV (cv2) License: Apache License 2.0 Copyright: 
OpenCV Team and Contributors URL: https://opencv.org/license/

· Pygame License: GNU LGPL version 2.1 Copyright: 
Pygame Community and Contributors URL: https://www.pygame.org/docs/LGPL.txt

· NumPy License: BSD 3-Clause License Copyright: 
NumPy Developers URL: https://numpy.org/doc/stable/license.html

· Matplotlib License: Python Software Foundation License (BSD-style) Copyright: 
Matplotlib Development Team URL: https://matplotlib.org/stable/project/license.html

· OR-Tools License: Apache License 2.0 Copyright: 
Google LLC URL: https://developers.google.com/optimization/

Thank you for playing the Hydropower Market Game!
"""

    # Split text into lines
    credits_lines = credits_text_str.split("\n")

    # Render all lines into surfaces
    rendered_lines = [text_font.render(line, True, (255, 255, 255)) for line in credits_lines]

    # Scroll variables
    scroll_offset = 0
    line_height = text_font.get_linesize()
    total_text_height = len(rendered_lines) * line_height

    # Exit button size and position
    button_width = SCREEN_WIDTH * 0.15
    button_height = SCREEN_HEIGHT * 0.06
    button_rect = pygame.Rect(SCREEN_WIDTH * 0.8, SCREEN_HEIGHT * 0.02, button_width, button_height)

    scaled_frame = pygame.transform.smoothscale(border_frame, (int(button_width), int(button_height)))
    red_frame = tint_surface(scaled_frame, (255, 0, 0))
    exit_text = button_font.render("Exit", True, (255, 255, 255))
    exit_text_rect = exit_text.get_rect(center=button_rect.center)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if button_rect.collidepoint(event.pos):
                        return  # exit
                elif event.button == 4:  # scroll up
                    scroll_offset = min(scroll_offset + 20, 0)
                elif event.button == 5:  # scroll down
                    if total_text_height + scroll_offset > SCREEN_HEIGHT:
                        scroll_offset -= 20

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    scroll_offset = min(scroll_offset + 20, 0)
                elif event.key == pygame.K_DOWN:
                    if total_text_height + scroll_offset > SCREEN_HEIGHT:
                        scroll_offset -= 20
                elif event.key == pygame.K_PAGEUP:
                    scroll_offset = min(scroll_offset + SCREEN_HEIGHT // 2, 0)
                elif event.key == pygame.K_PAGEDOWN:
                    if total_text_height + scroll_offset > SCREEN_HEIGHT:
                        scroll_offset -= SCREEN_HEIGHT // 2

        # Draw background
        screen.fill((0, 0, 0))

        # Draw credits text
        y_pos = scroll_offset
        for line_surface in rendered_lines:
            screen.blit(line_surface, (SCREEN_WIDTH * 0.05, y_pos))
            y_pos += line_height

        # Draw exit button
        screen.blit(red_frame, button_rect)
        screen.blit(exit_text, exit_text_rect)

        pygame.display.flip()
        clock.tick(60)


# --- Game Levels ---
def intro_level():
    global selected_character, SCREEN_WIDTH, SCREEN_HEIGHT, border_frame, player_name, level_completed

    # Character‑specific images
    if selected_character == 0:
        scene1_image = load_image("assets/Transitions/Welcome/FB_Welcome.jpg")
        scene2_image = load_image("assets/Transitions/Turbine room/FB_Turbine.jpg")
    elif selected_character == 1:
        scene1_image = load_image("assets/Transitions/Welcome/MW_Welcome.jpg")
        scene2_image = load_image("assets/Transitions/Turbine room/MW_Turbine.jpg")
    elif selected_character == 2:
        scene1_image = load_image("assets/Transitions/Welcome/FA_Welcome.jpg")
        scene2_image = load_image("assets/Transitions/Turbine room/FA_Turbine.jpg")
    elif selected_character == 3:
        scene1_image = load_image("assets/Transitions/Welcome/MH_Welcome.jpg")
        scene2_image = load_image("assets/Transitions/Turbine room/MH_Turbine.jpg")
    elif selected_character == 4:
        scene1_image = load_image("assets/Transitions/Welcome/FA_Welcome.jpg")
        scene2_image = load_image("assets/Transitions/Turbine room/FA_Turbine.jpg")
    elif selected_character == 5:
        scene1_image = load_image("assets/Transitions/Welcome/MB_Welcome.jpg")
        scene2_image = load_image("assets/Transitions/Turbine room/MB_Turbine.jpg")
    elif selected_character == 6:
        scene1_image = load_image("assets/Transitions/Welcome/FH_Welcome.jpg")
        scene2_image = load_image("assets/Transitions/Turbine room/FH_Turbine.jpg")
    elif selected_character == 7:
        scene1_image = load_image("assets/Transitions/Welcome/MI_Welcome.jpg")
        scene2_image = load_image("assets/Transitions/Turbine room/MI_Turbine.jpg")
    elif selected_character == 8:
        scene1_image = load_image("assets/Transitions/Welcome/FW_Welcome.jpg")
        scene2_image = load_image("assets/Transitions/Turbine room/FW_Turbine.jpg")

    # Scale both scenes
    scene1_image = pygame.transform.smoothscale(scene1_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    scene2_image = pygame.transform.smoothscale(scene2_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

    # --- Dialogue Data ---
    dialogue_scene1 = [
        ("Tom (Boss)",
         f"Welcome to Blue Rapids, {player_name}! We were looking forward to hiring a brilliant engineer like you! "
         "My name is Tom, and I will be supervising you."),
        ("Tom", "Come with me to get a look at our turbine room!")
    ]
    dialogue_scene2 = [
        ("Tom", "This is the turbine room of our Dam Hydropower Plant! "
                "These large machines convert the kinetic energy from flowing water into electricity! "
                "I'm eager to start working with you! You will learn how to operate all of our plants here and about various aspects of hydropower.")
    ]

    scenes = [(scene1_image, dialogue_scene1), (scene2_image, dialogue_scene2)]
    if scenes:
        run_dialogue(scenes)
    level_completed[0] = True
    save_game_data()

def Hydropower_Model():
    global SCREEN_WIDTH, SCREEN_HEIGHT
    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GRAY = (200, 200, 200)
    BLUE = (0, 0, 255)
    WIDTH, HEIGHT = SCREEN_WIDTH, SCREEN_HEIGHT

    # Continue button setup
    Continue_width = SCREEN_WIDTH * 0.15
    Continue_height = SCREEN_HEIGHT * 0.06
    Continue_rect = pygame.Rect(SCREEN_WIDTH - Continue_width - SCREEN_WIDTH * 0.02,
                            SCREEN_HEIGHT - Continue_height - SCREEN_HEIGHT * 0.02,
                            Continue_width, Continue_height)
    Continue_frame = pygame.transform.smoothscale(border_frame, (int(Continue_width), int(Continue_height)))
    Continue_green_frame = tint_surface(Continue_frame, (0, 200, 0))
    Continue_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.03))
    Continue_text = Continue_font.render("Continue", True, (255, 255, 255))
    Continue_text_rect = Continue_text.get_rect(center=Continue_rect.center)

    # Slider class
    class Slider:
        def __init__(self, x_frac, y_frac, w_frac, h_frac, min_val, max_val, start_val, label):
            self.x_frac = x_frac
            self.y_frac = y_frac
            self.w_frac = w_frac
            self.h_frac = h_frac
            self.rect = pygame.Rect(0, 0, 0, 0)
            self.update_rect()
            self.min_val = min_val
            self.max_val = max_val
            self.value = start_val
            self.label = label
            self.dragging = False

        def update_rect(self):
            self.rect.x = int(self.x_frac * WIDTH)
            self.rect.y = int(self.y_frac * HEIGHT)
            self.rect.w = int(self.w_frac * WIDTH)
            self.rect.h = int(self.h_frac * HEIGHT)

        def draw(self, surface):
            self.update_rect()
            pygame.draw.rect(surface, GRAY, self.rect)
            handle_x = self.rect.x + (self.rect.w * ((self.value - self.min_val) / (self.max_val - self.min_val)))
            handle_rect = pygame.Rect(handle_x - 5, self.rect.y, 10, self.rect.h)
            pygame.draw.rect(surface, BLUE, handle_rect)
            font = pygame.font.Font(None, int(0.04 * HEIGHT))
            text = font.render(f"{self.label}: {self.value:.2f}", True, BLACK)
            surface.blit(text, (self.rect.x, self.rect.y - int(0.05 * HEIGHT)))

        def update(self, event):
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.rect.collidepoint(event.pos):
                    self.dragging = True
            elif event.type == pygame.MOUSEBUTTONUP:
                self.dragging = False
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    rel_x = event.pos[0] - self.rect.x
                    self.value = self.min_val + (rel_x / self.rect.w) * (self.max_val - self.min_val)
                    self.value = max(self.min_val, min(self.max_val, self.value))
    Q_slider = Slider(0.15, 0.82, 0.3, 0.04, 0, 10000, 1000, 'Flow Rate Q (cfs)')
    h_slider = Slider(0.55, 0.82, 0.3, 0.04, 0, 100, 10, 'Head h (ft)')

    azim_angle = 225
    elev_angle = 30
    last_mouse_pos = (0, 0)
    is_dragging = False

    def mouse_over_slider(pos):
            return Q_slider.rect.collidepoint(pos) or h_slider.rect.collidepoint(pos)

    running = True
    first_run = True
    slow_run = 0
    UPDATE_INTERVAL = 6  # Update plot every 6 frames

    font_small = pygame.font.Font(None, int(0.045 * HEIGHT))
    font_large = pygame.font.Font(None, int(0.06 * HEIGHT))
    
    while running:
        Q = Q_slider.value
        h = h_slider.value
        P = 0.00007 * Q * h

        screen.fill(WHITE)

        blit_centered_text(screen, "Explore the fundamental equation of Hydropower by adjusting the flow rate and head!", font_small, int(0.05 * HEIGHT))
        blit_centered_text(screen, "Click and hold anywhere other than the sliders to rotate 3D-plot.", font_small, int(0.1 * HEIGHT))
        blit_centered_text(screen, "Click and drag sliders to adjust parameters.", font_small, int(0.9 * HEIGHT))
        blit_centered_text(screen, f"P = {P:.2f} MW", font_large, int(0.15 * HEIGHT))

        # Draw/update plot in the middle
        if first_run:
            plot1_surface = draw_3d_surface(Q, h, azim_angle, elev_angle) 
            plot2_surface = draw_colormap(Q, h)
            plot1_rect = plot1_surface.get_rect(center=(WIDTH // 4, int(0.5 * HEIGHT)))
            plot2_rect = plot2_surface.get_rect(center=(3 * WIDTH // 4, int(0.5 * HEIGHT)))
            first_run = False
        else:
            if slow_run % UPDATE_INTERVAL == 0:
                plot1_surface = update_3d_surface(Q, h, azim_angle, elev_angle)
                plot2_surface = update_colormap(Q, h)
        slow_run += 1

        screen.blit(plot1_surface, plot1_rect)
        screen.blit(plot2_surface, plot2_rect)

        # Draw sliders at bottom
        Q_slider.draw(screen)
        h_slider.draw(screen)

        # Draw Continue button
        screen.blit(Continue_green_frame, Continue_rect)
        screen.blit(Continue_text, Continue_text_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game_data()
                pygame.quit()
                sys.exit()
            Q_slider.update(event)
            h_slider.update(event)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                is_dragging = not mouse_over_slider(event.pos)
                last_mouse_pos = event.pos
                if Continue_rect.collidepoint(event.pos):
                    return
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                is_dragging = False
            elif event.type == pygame.MOUSEMOTION and is_dragging:
                dx = event.pos[0] - last_mouse_pos[0]
                dy = event.pos[1] - last_mouse_pos[1]
                azim_angle -= dx * 0.5
                elev_angle += dy * 0.5
                elev_angle = max(-90, min(90, elev_angle))
                last_mouse_pos = event.pos
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    azim_angle = 225
                    elev_angle = 30

        pygame.display.flip()
    if fig_3d: plt.close(fig_3d)
    if fig_colormap: plt.close(fig_colormap)

def Level1_intro():
    global selected_character, SCREEN_WIDTH, SCREEN_HEIGHT

    scene1_image = load_image(f"assets/Transitions/FirstEquation/{selected_character}_First.jpg")
    scene2_image = load_image("assets/RoRStatics/RoRStatic.jpg")
    # Scale both scenes
    scene1_image = pygame.transform.smoothscale(scene1_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    scene2_image = pygame.transform.smoothscale(scene2_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    # --- Dialogue Data ---
    dialogue_scene1 = [
        ("Tom",
         "For a Run-of-River Hydropower Plant, the power 'P' produced by a Hydropower Plant "
         "is roughly proportional to the flow rate 'Q' of the water through the turbine. "
         "Let me show you our plant!")
    ]
    dialogue_scene2 = [
        ("Tom",
         "This is our Run-of-River plant! You will attempt to match the electricity load curve for our city "
         "by opening and closing the wicket gate in the turbine. Go ahead and explore it before you get a chance to operate it!")
    ]
    scenes = [(scene1_image,dialogue_scene1),(scene2_image,dialogue_scene2)]
    run_dialogue(scenes)

def RoR_Exploration():
    static_image = load_image('assets/RoRStatics/RoRStatic.jpg')
    static_image = pygame.transform.smoothscale(static_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

    gate_image = load_image('assets/RoRStatics/Wicket_gate.png')
    turbine_image = load_image('assets/RoRStatics/Turbine.png')

    turbine_image = pygame.transform.smoothscale(turbine_image, (turbine_image.get_width() * 0.09 * (SCREEN_WIDTH / 1280),
                                                                 turbine_image.get_height() * 0.09 * (SCREEN_HEIGHT / 720)))

    caption_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Regular.ttf"), int(SCREEN_HEIGHT * 0.045))
    name_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.03))
    description_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Regular.ttf"), int(SCREEN_HEIGHT * 0.03))

    # Frame and gate scaling
    angles = [220 - i * 360 / NUM_OVALS for i in range(NUM_OVALS)]
    active_circle_radius = SCREEN_WIDTH * 0.0875

    frame_size = int(active_circle_radius * 2.7)
    frame_x = int(SCREEN_WIDTH * 0.018)
    frame_y = int(SCREEN_HEIGHT * 0.043)

    scaled_frame = pygame.transform.smoothscale(border_frame, (frame_size, frame_size))

    gate_scale_factor = 0.18
    gate_size = int(frame_size * gate_scale_factor)
    active_gate_image = pygame.transform.smoothscale(gate_image, (gate_size, gate_size))

    center_x, center_y = frame_x + frame_size / 2, frame_y + frame_size / 2
    positions = [
        (center_x + active_circle_radius * np.cos(2 * np.pi * i / NUM_OVALS),
         center_y + active_circle_radius * np.sin(2 * np.pi * i / NUM_OVALS))
        for i in range(NUM_OVALS)
    ]

    gate_caption = caption_font.render("Turbine Display", True, (255, 255, 255))
    exploration_directions = caption_font.render("Explore the components by clicking on them!", True, (255, 255, 255))

    graph_width = (1200 * SCREEN_WIDTH / 1920) / 2.8
    graph_height = (900 * SCREEN_HEIGHT / 1080) / 2.8
    graph_x = SCREEN_WIDTH - graph_width - SCREEN_WIDTH * 0.02
    graph_y = int(SCREEN_HEIGHT * 0.075)
    graph_border = pygame.transform.smoothscale(border_frame, (int(graph_width * 1.025), int(graph_height * 1.025)))

    graph_filename = update_RoR_graph()
    graph_image = load_image(graph_filename)
    scaled_graph_image = pygame.transform.scale(graph_image, (graph_width, graph_height))

    # Define the positions and radii of the 8 clickable circles
    clickable_circles = [
        {"name": "Load and Generation Plot", "pos": (SCREEN_WIDTH * 0.85, SCREEN_HEIGHT * 0.25), "radius": SCREEN_WIDTH * 0.01},
        {"name": "Turbine", "pos": (SCREEN_WIDTH * 0.65, SCREEN_HEIGHT * 0.495), "radius": SCREEN_WIDTH * 0.01},
        {"name": "Turbine", "pos": (SCREEN_WIDTH * 0.136, SCREEN_HEIGHT * 0.255), "radius": SCREEN_WIDTH * 0.01},
        {"name": "Wicket Gate Blade", "pos": (SCREEN_WIDTH * 0.136, SCREEN_HEIGHT * 0.0975), "radius": SCREEN_WIDTH * 0.01},
        {"name": "Generator", "pos": (SCREEN_WIDTH * 0.645, SCREEN_HEIGHT * 0.425), "radius": SCREEN_WIDTH * 0.01},
        {"name": "Control Valve", "pos": (SCREEN_WIDTH * 0.457, SCREEN_HEIGHT * 0.49), "radius": SCREEN_WIDTH * 0.01},
        {"name": "Tailrace", "pos": (SCREEN_WIDTH * 0.95, SCREEN_HEIGHT * 0.9), "radius": SCREEN_WIDTH * 0.01},
        {"name": "Penstock", "pos": (SCREEN_WIDTH * 0.2, SCREEN_HEIGHT * 0.5), "radius": SCREEN_WIDTH * 0.01},
    ]

    component_descriptions = {
        "Load and Generation Plot": "This plot shows the load demand and generation over time.",
        "Turbine": "The turbine converts the kinetic energy of water into mechanical energy.",
        "Wicket Gate Blade": "The wicket gate blade controls the flow of water to the turbine.",
        "Generator": "The generator converts mechanical energy into electrical energy.",
        "Control Valve": "The control valve regulates the flow of water in the system.",
        "Tailrace": "The tailrace is the channel that carries water away from the turbine.",
        "Penstock": "The penstock is the pipe that delivers water to the turbine."
    }

    # Text box setup
    text_box_width = SCREEN_WIDTH * 0.75
    text_box_height = SCREEN_HEIGHT * 0.15
    text_box_x = SCREEN_WIDTH * 0.02
    text_box_y = SCREEN_HEIGHT - text_box_height - SCREEN_HEIGHT * 0.02
    text_box_frame = pygame.transform.smoothscale(border_frame, (int(text_box_width), int(text_box_height)))

    # Variables to store the most recently clicked item's name and description
    clicked_name = ""
    clicked_description = ""
    clicked_circle = None  # Track the currently clicked circle

    # Continue button setup
    Continue_width = SCREEN_WIDTH * 0.15
    Continue_height = SCREEN_HEIGHT * 0.06
    Continue_rect = pygame.Rect(SCREEN_WIDTH - Continue_width - SCREEN_WIDTH * 0.02,
                            SCREEN_HEIGHT - Continue_height - SCREEN_HEIGHT * 0.02,
                            Continue_width, Continue_height)
    Continue_frame = pygame.transform.smoothscale(border_frame, (int(Continue_width), int(Continue_height)))
    Continue_green_frame = tint_surface(Continue_frame, (0, 200, 0))
    Continue_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.03))
    Continue_text = Continue_font.render("Continue", True, (255, 255, 255))
    Continue_text_rect = Continue_text.get_rect(center=Continue_rect.center)

    has_clicked = False  # Track if any circle has been clicked
    running = True
    while running:
        screen.blit(static_image, (0, 0))
        screen.blit(exploration_directions, (SCREEN_WIDTH / 2 - exploration_directions.get_width() / 2, SCREEN_HEIGHT * 0.15))
        screen.blit(gate_caption, (frame_x + frame_size / 2 - gate_caption.get_width() / 2, frame_y - SCREEN_HEIGHT * 0.05))
        screen.blit(scaled_frame, (frame_x, frame_y))
        screen.blit(graph_border, (graph_x, graph_y))
        screen.blit(scaled_graph_image, (graph_x, graph_y))

        # Draw rotating gates
        for i, (pos_x, pos_y) in enumerate(positions):
            rotated_image = pygame.transform.rotozoom(active_gate_image, angles[i], 1.0)
            rect = rotated_image.get_rect(center=(pos_x, pos_y))
            screen.blit(rotated_image, rect.topleft)
        screen.blit(turbine_image, (center_x - turbine_image.get_width() / 2, center_y - turbine_image.get_height() / 2))

        pygame.draw.line(screen, GREEN, (frame_x+frame_size, frame_y), (0.62*SCREEN_WIDTH, 0.49*SCREEN_HEIGHT))
        pygame.draw.line(screen, GREEN, (frame_x+frame_size, frame_y+(frame_size)), (0.62*SCREEN_WIDTH, 0.49*SCREEN_HEIGHT))

        # Draw the clickable circles with hover and click effects
        mouse_pos = pygame.mouse.get_pos()
        for circle in clickable_circles:
            distance = ((mouse_pos[0] - circle["pos"][0]) ** 2 + (mouse_pos[1] - circle["pos"][1]) ** 2) ** 0.5
            if circle == clicked_circle:  # Click effect
                pygame.draw.circle(screen, (0, 255, 0), circle["pos"], circle["radius"]*1.2)  # Green Fill
            elif distance <= circle["radius"]:  # Hover effect
                pygame.draw.circle(screen, (0, 255, 0), circle["pos"], circle["radius"])  # Semi-transparent fill
            else:
                pygame.draw.circle(screen, (0, 255, 0), circle["pos"], circle["radius"], 2)  # Default outline

        # Draw the text box
        if has_clicked:
            screen.blit(text_box_frame, (text_box_x, text_box_y))
            name_text = name_font.render(f"{clicked_name}", True, (255, 255, 255))
            description_text = description_font.render(f"{clicked_description}", True, (255, 255, 255))
            screen.blit(name_text, (text_box_x + SCREEN_WIDTH * 0.01, text_box_y + SCREEN_HEIGHT * 0.01))
            screen.blit(description_text, (text_box_x + SCREEN_WIDTH * 0.01, text_box_y + SCREEN_HEIGHT * 0.05))

        # Draw Continue button
        screen.blit(Continue_green_frame, Continue_rect)
        screen.blit(Continue_text, Continue_text_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game_data()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for circle in clickable_circles:
                    distance = ((mouse_pos[0] - circle["pos"][0]) ** 2 + (mouse_pos[1] - circle["pos"][1]) ** 2) ** 0.5
                    if distance <= circle["radius"]:
                        clicked_name = circle["name"]
                        clicked_description = component_descriptions[clicked_name]
                        clicked_circle = circle  # Update the clicked circle
                        has_clicked = True
                if Continue_rect.collidepoint(mouse_pos):
                    return  # Continue to the next part
            else:
                clicked_circle = None

        pygame.display.flip()
        clock.tick(60)

def Load_Instructions(level_number):
    if level_number == 1:
        background = load_image('assets/RoRStatics/RoRStatic.jpg')
    elif level_number == 2:
        background = load_image('assets/DamSequences/DamStatics/DamStatics.jpg')
    elif level_number == 3:
        background = load_image('assets/PSHSequences/PSHStatics/PSHStatics.jpg')
    background = pygame.transform.smoothscale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))

    caption_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Regular.ttf"), int(SCREEN_HEIGHT * 0.05))
    caption_text = caption_font.render("Use the hydropower generation to follow the electricity load!", True, (255, 255, 255))

    # Continue button setup
    Continue_width = SCREEN_WIDTH * 0.15
    Continue_height = SCREEN_HEIGHT * 0.06
    Continue_rect = pygame.Rect(SCREEN_WIDTH - Continue_width - SCREEN_WIDTH * 0.02,
                            SCREEN_HEIGHT - Continue_height - SCREEN_HEIGHT * 0.02,
                            Continue_width, Continue_height)
    Continue_frame = pygame.transform.smoothscale(border_frame, (int(Continue_width), int(Continue_height)))
    Continue_green_frame = tint_surface(Continue_frame, (0, 200, 0))
    Continue_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.03))
    Continue_text = Continue_font.render("Continue", True, (255, 255, 255))
    Continue_text_rect = Continue_text.get_rect(center=Continue_rect.center)
    example_input = []
    for i in range(len(LOAD_CURVE)-1):
        example_input.append(int(LOAD_CURVE[i]/30))
    example_data = []
    x_start = 0
    x_end = 5
    example_index = 13
    display = 0

    graph_width = (1200*SCREEN_WIDTH / 1920)/1.5
    graph_height = (900*SCREEN_HEIGHT / 1080)/1.5
    graph_x = SCREEN_WIDTH//2 - graph_width//2
    graph_y = SCREEN_HEIGHT//2 - graph_height//2
    graph_border = pygame.transform.smoothscale(border_frame, (int(graph_width*1.025), int(graph_height*1.025)))
    graph_border = tint_surface(graph_border,(50,50,50))
    graph_border.set_alpha(230)

    clock = pygame.time.Clock()
    running = True
    while running:
        screen.blit(background, (0, 0))
        screen.blit(caption_text, (SCREEN_WIDTH / 2 - caption_text.get_width() / 2, SCREEN_HEIGHT * 0.1))

        example_data.append(example_input[example_index])

        graph_filename = Example_Graph(x_start,x_end,example_data,display,2)
        graph_image = load_image(graph_filename)

        scaled_graph_image = pygame.transform.scale(graph_image, (graph_width, graph_height))
        screen.blit(graph_border, (graph_x, graph_y))
        screen.blit(scaled_graph_image, (graph_x, graph_y))
        if len(example_data) > 10:
                example_data = example_data[-10:]

        x_start += 0.05
        x_end += 0.05

        example_index = example_index % (len(example_input)-1)
        example_index += 1
        
        display = display % (len(LOAD_CURVE)-1)
        display += 1
        
        # Draw Continue button
        screen.blit(Continue_green_frame, Continue_rect)
        screen.blit(Continue_text, Continue_text_rect)

        os.remove(graph_filename)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game_data()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if Continue_rect.collidepoint(event.pos):
                    return  # Continue to the next part
        pygame.display.flip()
        clock.tick(60)

def RoR_Controls():
    show_pressed_keys = True
    show_blinking_rect = True
    blink_timer = 0
    blink_interval = 500

    # Continue button setup
    Continue_width = SCREEN_WIDTH * 0.15
    Continue_height = SCREEN_HEIGHT * 0.06
    Continue_rect = pygame.Rect(SCREEN_WIDTH - Continue_width - SCREEN_WIDTH * 0.02,
                            SCREEN_HEIGHT - Continue_height - SCREEN_HEIGHT * 0.02,
                            Continue_width, Continue_height)
    Continue_frame = pygame.transform.smoothscale(border_frame, (int(Continue_width), int(Continue_height)))
    Continue_green_frame = tint_surface(Continue_frame, (0, 200, 0))
    Continue_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.03))
    Continue_text = Continue_font.render("Continue", True, (255, 255, 255))
    Continue_text_rect = Continue_text.get_rect(center=Continue_rect.center)

    caption_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Regular.ttf"), int(SCREEN_HEIGHT * 0.045))
    loading_text = caption_font.render("Loading...", True, (255, 255, 255))

    clock = pygame.time.Clock()
    running = True
    while running:
        blink_timer += clock.get_time()
        if blink_timer >= blink_interval:
            show_pressed_keys = not show_pressed_keys
            show_blinking_rect = not show_blinking_rect
            blink_timer = 0

        draw_controls_page_ROR(screen, show_pressed_keys, show_blinking_rect)
        screen.blit(Continue_green_frame, Continue_rect)
        screen.blit(Continue_text, Continue_text_rect)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game_data()
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if Continue_rect.collidepoint(event.pos):
                    screen.blit(loading_text, (SCREEN_WIDTH / 2 - loading_text.get_width() / 2, SCREEN_HEIGHT / 2 - loading_text.get_height() / 2))
                    pygame.display.flip()
                    return  # Continue to the next part
        pygame.display.flip()
        clock.tick(60)

def RoR_Level():
    global NUM_ROR_FRAMES, WATER_PATH_TEMPLATE, TUBE_PATH_TEMPLATE, ROR_LEVEL_DURATION, MAX_ROTATION, ROTATION_ANGLE, NUM_OVALS 
    global SCREEN_WIDTH, SCREEN_HEIGHT, level_completed, level_scores, border_frame, control_panel, up_active, up_inactive, down_active, down_inactive
    static_image = load_image('assets/RoRStatics/RoRStatic.jpg')
    gate_image = load_image('assets/RoRStatics/Wicket_gate.png')
    water_image = load_image('assets/Water.png')
    swirl_image = load_image('assets/RoRStatics/Swirl.png')
    turbine_image = load_image('assets/RoRStatics/Turbine.png')
    water_frames = load_ROR_frames(NUM_ROR_FRAMES, WATER_LOWER_PATH_TEMPLATE)
    tube_frames = load_ROR_frames(NUM_ROR_FRAMES, TUBE_PATH_TEMPLATE)
    frame_index = 0
    game_state = reset_RoR()
    game_state['angles'] = [220 - i * 360 / NUM_OVALS for i in range(NUM_OVALS)]
    active_circle_radius = SCREEN_WIDTH * 0.0875

    statics_image = pygame.transform.smoothscale(static_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    water_image = pygame.transform.smoothscale(water_image, (water_image.get_width()*0.03*(SCREEN_WIDTH/1280), water_image.get_height()*0.03*(SCREEN_HEIGHT/720)))
    swirl_image = pygame.transform.smoothscale(swirl_image, (swirl_image.get_width()*0.45*(SCREEN_WIDTH/1280), swirl_image.get_height()*0.45*(SCREEN_HEIGHT/720)))
    turbine_image = pygame.transform.smoothscale(turbine_image, (turbine_image.get_width()*0.09*(SCREEN_WIDTH/1280), turbine_image.get_height()*0.09*(SCREEN_HEIGHT/720)))

    graph_width = (1200*SCREEN_WIDTH / 1920)/2.8
    graph_height = (900*SCREEN_HEIGHT / 1080)/2.8
    graph_x = SCREEN_WIDTH - graph_width - SCREEN_WIDTH * 0.02 
    graph_y = int(SCREEN_HEIGHT * 0.075) 
    graph_border = pygame.transform.smoothscale(border_frame, (int(graph_width*1.025), int(graph_height*1.025)))

    # Button positioning
    button_width = up_active.get_width() * SCREEN_WIDTH / 1920
    button_height = up_active.get_height() * SCREEN_HEIGHT / 1080
    button_x = SCREEN_WIDTH * 0.45
    up_button_y = SCREEN_HEIGHT * 0.83
    down_button_y = SCREEN_HEIGHT * 0.93

    up_active_ror = pygame.transform.smoothscale(up_active, (int(button_width), int(button_height)))
    up_inactive_ror = pygame.transform.smoothscale(up_inactive, (int(button_width), int(button_height)))
    down_active_ror = pygame.transform.smoothscale(down_active, (int(button_width), int(button_height)))
    down_inactive_ror = pygame.transform.smoothscale(down_inactive, (int(button_width), int(button_height)))

    # --- Draw Wicket Gate Frame and Label ---
    frame_size = int(active_circle_radius * 2.7)
    frame_x = int(SCREEN_WIDTH * 0.018)
    frame_y = int(SCREEN_HEIGHT * 0.043)
    
    scaled_frame = pygame.transform.smoothscale(border_frame, (frame_size, frame_size))

    scaled_panel = pygame.transform.smoothscale(control_panel, ((control_panel.get_size()[0] * SCREEN_WIDTH / 1920)/2, 
                                                                      (control_panel.get_size()[1] * SCREEN_HEIGHT / 1080)/2))
    scaled_panel.set_alpha(127)

    # Define gate size as a fraction of the frame
    gate_scale_factor = 0.18  # 20% of the frame size

    gate_size = int(frame_size * gate_scale_factor)
    active_gate_image = pygame.transform.smoothscale(gate_image, (gate_size, gate_size))

    game_state['center_x'], game_state['center_y'] = frame_x + frame_size / 2, frame_y + frame_size / 2
    game_state['positions'] = [
        (game_state['center_x'] + active_circle_radius * np.cos(2 * np.pi * i / NUM_OVALS),
            game_state['center_y'] + active_circle_radius * np.sin(2 * np.pi * i / NUM_OVALS))
        for i in range(NUM_OVALS)
    ]

    if SCREEN_WIDTH == 960:
        performance_font = pygame.font.Font(resource_path("assets/Fonts/Electrolize-Regular.ttf"), 20)
        complete_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Regular.ttf"), 42)
    elif SCREEN_WIDTH == 1280:
        performance_font = pygame.font.Font(resource_path("assets/Fonts/Electrolize-Regular.ttf"), 30)
        complete_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Regular.ttf"), 64)
    elif SCREEN_WIDTH == 1600:
        performance_font = pygame.font.Font(resource_path("assets/Fonts/Electrolize-Regular.ttf"), 40)
        complete_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Regular.ttf"), 84)

    # Exit button setup (bottom right)
    exit_width = SCREEN_WIDTH * 0.15
    exit_height = SCREEN_HEIGHT * 0.06
    exit_rect = pygame.Rect(SCREEN_WIDTH - exit_width - SCREEN_WIDTH * 0.02,
                            SCREEN_HEIGHT - exit_height - SCREEN_HEIGHT * 0.02,
                            exit_width, exit_height)
    exit_frame = pygame.transform.smoothscale(border_frame, (int(exit_width), int(exit_height)))
    exit_red_frame = tint_surface(exit_frame, (255, 0, 0))
    exit_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.03))
    exit_text = exit_font.render("Exit", True, (255, 255, 255))
    exit_text_rect = exit_text.get_rect(center=exit_rect.center)

    # Skip button setup
    skip_width = SCREEN_WIDTH * 0.15
    skip_height = SCREEN_HEIGHT * 0.06
    skip_rect = pygame.Rect(SCREEN_WIDTH * 0.65,
                            SCREEN_HEIGHT - skip_height - SCREEN_HEIGHT * 0.02,
                            skip_width, skip_height)
    skip_frame = pygame.transform.smoothscale(border_frame, (int(skip_width), int(skip_height)))
    skip_green_frame = tint_surface(skip_frame, (0, 200, 0))
    skip_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.03))
    skip_text = skip_font.render("Skip", True, (255, 255, 255))
    skip_text_rect = skip_text.get_rect(center=skip_rect.center)

    turbine_rotation = 0
    water_rotation = 0
    
    display = 190
    power_index = 0
    clock = pygame.time.Clock()
    running = True

    while running:
        if game_state['level_complete']:
            screen.blit(statics_image, (0,0))

            # Draw the overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)  # Semi-transparent
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))

            complete_text = "Level complete! Your score was:"
            complete_label = complete_font.render(complete_text, True, (255, 255, 255))
            score_text = f"{int(calculate_score(game_state['score']))}"
            score_label = complete_font.render(score_text, True, (255, 255, 255))

            screen.blit(complete_label, ((SCREEN_WIDTH - complete_label.get_width()) // 2, SCREEN_HEIGHT // 3))
            screen.blit(score_label, ((SCREEN_WIDTH - score_label.get_width()) // 2, SCREEN_HEIGHT // 2))
        else:
            active_water_frame = water_frames[frame_index]
            active_tube_frame = tube_frames[frame_index]
            frame_index = (frame_index + 1) % (NUM_ROR_FRAMES-1)
            screen.blit(statics_image, (0, 0))
            screen.blit(active_water_frame, (int(SCREEN_WIDTH*.5256), int(SCREEN_HEIGHT*.72779)))
            screen.blit(active_tube_frame, (1, SCREEN_HEIGHT*.3286))
            
            game_state['release'] = 60*game_state['rotation']
            power_generated = truncate_float(0.001 * game_state['release'],2)
            game_state['power_data'].append(power_generated)

            graph_filename = update_RoR_graph(game_state['x_start'], game_state['x_end'], game_state['power_data'], display)
            graph_image = load_image(graph_filename)
            
            display = display % (len(LOAD_CURVE)-1)
            display += 1
                
            scaled_graph_image = pygame.transform.scale(graph_image, (graph_width, graph_height))
            screen.blit(graph_border, (graph_x, graph_y))
            screen.blit(scaled_graph_image, (graph_x, graph_y))
            if len(game_state['power_data']) > 10:
                game_state['power_data'] = game_state['power_data'][-10:]

            game_state['x_start'] += 0.05
            game_state['x_end'] += 0.05

            screen.blit(scaled_panel, (0, SCREEN_HEIGHT * .8))

            rotation_status = f"Wicket Gate Angle: {game_state['rotation']}°"
            release_status = f"Current Release: {game_state['release']} cfs"
            power_status = f"Power Generated: {power_generated} MW"

            screen.blit(performance_font.render(rotation_status, True, (255, 255, 255)), (SCREEN_WIDTH * 0.02, SCREEN_HEIGHT * 0.85))
            screen.blit(performance_font.render(release_status, True, (255, 255, 255)), (SCREEN_WIDTH * 0.02, SCREEN_HEIGHT * 0.90))
            screen.blit(performance_font.render(power_status, True, (255, 255, 255)), (SCREEN_WIDTH * 0.02, SCREEN_HEIGHT * 0.95))

            up_button = up_active_ror if game_state['rotation'] < 90 else up_inactive_ror
            down_button = down_active_ror if game_state['rotation'] > 10 else down_inactive_ror

            up_button_rect = up_button.get_rect(topleft=(button_x, up_button_y))
            down_button_rect = down_button.get_rect(topleft=(button_x, down_button_y))

            screen.blit(up_button, up_button_rect.topleft)
            screen.blit(down_button, down_button_rect.topleft)

            screen.blit(scaled_frame, (frame_x, frame_y))

            label_surface = performance_font.render("Turbine Display", True, (255, 255, 255))
            label_rect = label_surface.get_rect(center=(frame_x + frame_size / 2, frame_y - SCREEN_HEIGHT * 0.015))
            screen.blit(label_surface, label_rect)

            # Draw water images
            swirled_image = pygame.transform.rotozoom(swirl_image, water_rotation, 1.0)
            water_rotation = (water_rotation - 15*game_state['release']/5400) % 360
            screen.blit(swirled_image, (game_state['center_x'] - swirled_image.get_width() / 2, game_state['center_y'] - swirled_image.get_height() / 2))

            # --- Draw the rotating gates ---
            for i, (pos_x, pos_y) in enumerate(game_state['positions']):
                rotated_image = pygame.transform.rotozoom(active_gate_image, game_state['angles'][i], 1.0)
                rect = rotated_image.get_rect(center=(pos_x, pos_y))
                screen.blit(rotated_image, rect.topleft)

            turbine_rotation = (turbine_rotation-20*game_state['release']/5400) % 360
            rotated_turbine = pygame.transform.rotozoom(turbine_image, turbine_rotation, 1.0)
            screen.blit(rotated_turbine, (game_state['center_x'] - rotated_turbine.get_width() / 2, game_state['center_y'] - rotated_turbine.get_height() / 2))

            # Draw connecting lines
            pygame.draw.line(screen, GREEN, (frame_x+frame_size, frame_y), (0.62*SCREEN_WIDTH, 0.49*SCREEN_HEIGHT))
            pygame.draw.line(screen, GREEN, (frame_x+frame_size, frame_y+(frame_size)), (0.62*SCREEN_WIDTH, 0.49*SCREEN_HEIGHT))

            # Draw exit button
            screen.blit(exit_red_frame, exit_rect)
            screen.blit(exit_text, exit_text_rect)

            # Draw skip button
            screen.blit(skip_green_frame, skip_rect)
            screen.blit(skip_text, skip_text_rect)

            # Score Calculation
            load_difference = abs(power_generated - (LOAD_CURVE[(display+10)%(240)]/110))
            power_index += 1
            game_state['score'] += load_difference

            screen.blit(performance_font.render(f"Average Power Imbalance: {(game_state['score']/power_index):.2f} MW", True, (255, 255, 255)), (SCREEN_WIDTH * 0.55, frame_y - SCREEN_HEIGHT * 0.04))
            screen.blit(performance_font.render(f"Time Remaining: {ROR_LEVEL_DURATION-int(game_state['elapsed_time'])} sec", True, (255, 255, 255)), (SCREEN_WIDTH * 0.25, frame_y - SCREEN_HEIGHT * 0.04))
            game_state['elapsed_time'] += clock.tick(60) / 1000.0
            # Check for level completion
            if game_state['elapsed_time'] >= ROR_LEVEL_DURATION:
                game_state['level_complete'] = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game_data()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    if game_state['rotation'] < 90:
                        game_state['angles'] = [angle - ROTATION_ANGLE for angle in game_state['angles']]
                        game_state['rotation'] += ROTATION_ANGLE
                elif event.key == pygame.K_DOWN:
                    if game_state['rotation'] > 10:
                        game_state['angles'] = [angle + ROTATION_ANGLE for angle in game_state['angles']]
                        game_state['rotation'] -= ROTATION_ANGLE
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if game_state['level_complete']:
                    calc_score = calculate_score(game_state['score'])
                    if level_scores[1] < calc_score:
                        level_scores[1] = calc_score
                    level_completed[1] = True
                    save_game_data()
                    return
                if down_button_rect.collidepoint(event.pos):
                    if game_state['rotation'] > 10:
                        game_state['angles'] = [angle + ROTATION_ANGLE for angle in game_state['angles']]
                        game_state['rotation'] -= ROTATION_ANGLE
                elif up_button_rect.collidepoint(event.pos):
                    if game_state['rotation'] < 90:
                        game_state['angles'] = [angle - ROTATION_ANGLE for angle in game_state['angles']]
                        game_state['rotation'] += ROTATION_ANGLE
                elif exit_rect.collidepoint(event.pos):
                    return  # Exit this level
                elif skip_rect.collidepoint(event.pos):
                    level_completed[1] = True
                    save_game_data()
                    return
            elif event.type == pygame.MOUSEWHEEL:
                if event.y < 0 and game_state['rotation'] > 10:
                    game_state['angles'] = [angle + ROTATION_ANGLE for angle in game_state['angles']]
                    game_state['rotation'] -= ROTATION_ANGLE
                elif event.y > 0 and game_state['rotation'] < 90:
                    game_state['angles'] = [angle - ROTATION_ANGLE for angle in game_state['angles']]
                    game_state['rotation'] += ROTATION_ANGLE

        pygame.display.flip()

def Level2_intro():
    global selected_character, SCREEN_WIDTH, SCREEN_HEIGHT

    scene1_image = load_image(f"assets/Transitions/SecondEquation/{selected_character}_Second.jpg")
    scene2_image = load_image("assets/Transitions/DamGraphic.png")

    # Scale both scenes
    scene1_image = pygame.transform.smoothscale(scene1_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    scene2_image = pygame.transform.smoothscale(scene2_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

    # --- Dialogue Data ---
    dialogue_scene1 = [
        ("Tom",
         "There is more to hydropower than just the flow rate! "
         "The power 'P' produced by a Hydropower Plant is also proportional to the hydraulic head 'H' of the water. "
         "This is important for the Dam Hydropower Plant, where the head changes with hydrology conditions.")
    ]
    dialogue_scene2 = [
        ("Tom",
         "Here you can see a schematic of our Dam Hydropower Plant! "
         "It demonstrates how the water flows from the reservoir through the penstock tubes to the turbines, generating electricity. "
         "The electricity generated is proportional to the flow rate 'Q' and the hydraulic head 'H', as shown here. "
         ),
         ("Tom",
          "We've developed a tool to help you visualize this relationship. Go ahead and try it out for a while, then once you're done I'll "
          "show you our Dam Hydropower Plant!")
    ]

    scenes = [(scene1_image,dialogue_scene1),(scene2_image,dialogue_scene2)]
    run_dialogue(scenes)

def Level2_intro_cont():
    global SCREEN_WIDTH, SCREEN_HEIGHT

    scene1_image = load_image("assets/DamSequences/DamStatics/DamClosed.jpg")

    # Scale scene
    scene1_image = pygame.transform.smoothscale(scene1_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

    # --- Dialogue Data ---
    dialogue_scene1 = [
        ("Tom",
         "This is our Dam Hydropower Plant. Let's explore its main components.")
    ]
    scenes = [(scene1_image,dialogue_scene1)]
    run_dialogue(scenes)

def Dam_Exploration():
    cover_image = load_image('assets/DamSequences/DamStatics/DamClosed.jpg')
    cover_image = pygame.transform.smoothscale(cover_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    static_image = load_image('assets/DamSequences/DamStatics/DamStatics.jpg')
    static_image = pygame.transform.smoothscale(static_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

    covered = True

    caption_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Regular.ttf"), int(SCREEN_HEIGHT * 0.045))
    name_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.03))
    description_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Regular.ttf"), int(SCREEN_HEIGHT * 0.03))

    exploration_directions = caption_font.render("Explore the components by clicking on them!", True, (255, 255, 255))

    graph_width = (1200*screen.get_size()[0] / 1920)/2.8
    graph_height = (900*screen.get_size()[1] / 1080)/2.8
    graph_x = SCREEN_WIDTH - graph_width - SCREEN_WIDTH * 0.02
    graph_y = int(SCREEN_HEIGHT * 0.05) 
    graph_border = pygame.transform.smoothscale(border_frame, (int(graph_width*1.025), int(graph_height*1.025)))

    graph_filename = update_dam_graph()
    graph_image = load_image(graph_filename)
    scaled_graph_image = pygame.transform.scale(graph_image, (graph_width, graph_height))

    # Define the positions and radii of the 8 clickable circles
    clickable_circles = [
        {"name": "Load and Generation Plot", "pos": (SCREEN_WIDTH * 0.85, SCREEN_HEIGHT * 0.26), "radius": SCREEN_WIDTH * 0.01},
        {"name": "Reservoir", "pos": (SCREEN_WIDTH * 0.15, SCREEN_HEIGHT * 0.2), "radius": SCREEN_WIDTH * 0.01},
        {"name": "Spillway", "pos": (SCREEN_WIDTH * 0.7, SCREEN_HEIGHT * 0.205), "radius": SCREEN_WIDTH * 0.01},
        {"name": "Dam", "pos": (SCREEN_WIDTH * 0.43, SCREEN_HEIGHT * 0.3), "radius": SCREEN_WIDTH * 0.01},
        {"name": "Power Lines", "pos": (SCREEN_WIDTH * 0.385, SCREEN_HEIGHT * 0.8), "radius": SCREEN_WIDTH * 0.01},
        {"name": "Generator", "pos": (SCREEN_WIDTH * 0.545, SCREEN_HEIGHT * 0.745), "radius": SCREEN_WIDTH * 0.01},
        {"name": "Turbine", "pos": (SCREEN_WIDTH * 0.545, SCREEN_HEIGHT * 0.79), "radius": SCREEN_WIDTH * 0.01},
        {"name": "Control Gate", "pos": (SCREEN_WIDTH * 0.5, SCREEN_HEIGHT * 0.48), "radius": SCREEN_WIDTH * 0.01},
        {"name": "Penstock", "pos": (SCREEN_WIDTH * 0.578, SCREEN_HEIGHT * 0.6), "radius": SCREEN_WIDTH * 0.01},
        {"name": "Tail Race", "pos": (SCREEN_WIDTH * 0.7, SCREEN_HEIGHT * 0.8), "radius": SCREEN_WIDTH * 0.01}
    ]

    component_descriptions = {
        "Load and Generation Plot": "This plot shows the load demand and generation over time.",
        "Turbine": "Converts the kinetic energy of water into mechanical energy.",
        "Reservoir": "Stores water for the system. When the reservoir reaches 'dead pool', the water can no longer flow downstream.",
        "Generator": "Converts mechanical energy into electrical energy.",
        "Control Gate": "Regulates the flow of water in the system.",
        "Tail Race": "The channel that carries water away from the turbine.",
        "Penstock": "The pipe that delivers water to the turbine.",
        "Power Lines": "Transport electricity from the generator to the grid.",
        "Dam": "Holds back water to create a reservoir.",
        "Spillway": "Allows excess water to flow out of the reservoir."
    }

    # Text box setup
    text_box_width = SCREEN_WIDTH * 0.75
    text_box_height = SCREEN_HEIGHT * 0.15
    text_box_x = SCREEN_WIDTH * 0.02
    text_box_y = SCREEN_HEIGHT - text_box_height - SCREEN_HEIGHT * 0.02
    text_box_frame = pygame.transform.smoothscale(border_frame, (int(text_box_width), int(text_box_height)))

    # Variables to store the most recently clicked item's name and description
    clicked_name = ""
    clicked_description = ""
    clicked_circle = None  # Track the currently clicked circle

    # Continue button setup
    Continue_width = SCREEN_WIDTH * 0.15
    Continue_height = SCREEN_HEIGHT * 0.06
    Continue_rect = pygame.Rect(SCREEN_WIDTH - Continue_width - SCREEN_WIDTH * 0.02,
                            SCREEN_HEIGHT - Continue_height - SCREEN_HEIGHT * 0.02,
                            Continue_width, Continue_height)
    Continue_frame = pygame.transform.smoothscale(border_frame, (int(Continue_width), int(Continue_height)))
    Continue_green_frame = tint_surface(Continue_frame, (0, 200, 0))
    Continue_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.03))
    Continue_text = Continue_font.render("Continue", True, (255, 255, 255))
    Continue_text_rect = Continue_text.get_rect(center=Continue_rect.center)

    i = 255
    has_clicked = False
    running = True
    while running:
        if covered:
            screen.blit(static_image, (0, 0))
            screen.blit(cover_image, (0, 0))
            cover_image.set_alpha(i)
            i -= 2
            if i <= 0:
                covered = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    save_game_data()
                    pygame.quit()
                    sys.exit()
        else:
            screen.blit(static_image, (0, 0))
            screen.blit(exploration_directions, (SCREEN_WIDTH / 2 - exploration_directions.get_width() / 2, SCREEN_HEIGHT * 0.07))
            screen.blit(graph_border, (graph_x, graph_y))
            screen.blit(scaled_graph_image, (graph_x, graph_y))

            # Draw the clickable circles with hover and click effects
            mouse_pos = pygame.mouse.get_pos()
            for circle in clickable_circles:
                distance = ((mouse_pos[0] - circle["pos"][0]) ** 2 + (mouse_pos[1] - circle["pos"][1]) ** 2) ** 0.5
                if circle == clicked_circle:  # Click effect
                    pygame.draw.circle(screen, (0, 255, 0), circle["pos"], circle["radius"]*1.2)  # Green Fill
                elif distance <= circle["radius"]:  # Hover effect
                    pygame.draw.circle(screen, (0, 255, 0), circle["pos"], circle["radius"])  # Semi-transparent fill
                else:
                    pygame.draw.circle(screen, (0, 255, 0), circle["pos"], circle["radius"], 2)  # Default outline

            # Draw the text box
            if has_clicked:
                screen.blit(text_box_frame, (text_box_x, text_box_y))
                name_text = name_font.render(f"{clicked_name}", True, (255, 255, 255))
                description_text = description_font.render(f"{clicked_description}", True, (255, 255, 255))
                screen.blit(name_text, (text_box_x + SCREEN_WIDTH * 0.01, text_box_y + SCREEN_HEIGHT * 0.01))
                screen.blit(description_text, (text_box_x + SCREEN_WIDTH * 0.01, text_box_y + SCREEN_HEIGHT * 0.05))

            # Draw Continue button
            screen.blit(Continue_green_frame, Continue_rect)
            screen.blit(Continue_text, Continue_text_rect)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    save_game_data()
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    for circle in clickable_circles:
                        distance = ((mouse_pos[0] - circle["pos"][0]) ** 2 + (mouse_pos[1] - circle["pos"][1]) ** 2) ** 0.5
                        if distance <= circle["radius"]:
                            clicked_name = circle["name"]
                            clicked_description = component_descriptions[clicked_name]
                            clicked_circle = circle  # Update the clicked circle
                            has_clicked = True
                    if Continue_rect.collidepoint(mouse_pos):
                        return  # Continue to the next part
                else:
                    clicked_circle = None
        pygame.display.flip()
        clock.tick(60)

def Dam_Controls():
    show_pressed_keys = True
    show_blinking_rect = True
    blink_timer = 0
    blink_interval = 500

    # Continue button setup
    Continue_width = SCREEN_WIDTH * 0.15
    Continue_height = SCREEN_HEIGHT * 0.06
    Continue_rect = pygame.Rect(SCREEN_WIDTH - Continue_width - SCREEN_WIDTH * 0.02,
                            SCREEN_HEIGHT - Continue_height - SCREEN_HEIGHT * 0.02,
                            Continue_width, Continue_height)
    Continue_frame = pygame.transform.smoothscale(border_frame, (int(Continue_width), int(Continue_height)))
    Continue_green_frame = tint_surface(Continue_frame, (0, 200, 0))
    Continue_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.03))
    Continue_text = Continue_font.render("Continue", True, (255, 255, 255))
    Continue_text_rect = Continue_text.get_rect(center=Continue_rect.center)

    caption_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Regular.ttf"), int(SCREEN_HEIGHT * 0.045))
    loading_text = caption_font.render("Loading...", True, (255, 255, 255))

    clock = pygame.time.Clock()
    running = True
    while running:
        blink_timer += clock.get_time()
        if blink_timer >= blink_interval:
            show_pressed_keys = not show_pressed_keys
            show_blinking_rect = not show_blinking_rect
            blink_timer = 0

        draw_controls_page_dam(screen, show_pressed_keys, show_blinking_rect)
        screen.blit(Continue_green_frame, Continue_rect)
        screen.blit(Continue_text, Continue_text_rect)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game_data()
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if Continue_rect.collidepoint(event.pos):
                    screen.blit(loading_text, (SCREEN_WIDTH / 2 - loading_text.get_width() / 2, SCREEN_HEIGHT / 2 - loading_text.get_height() / 2))
                    pygame.display.flip()
                    return  # Continue to the next part
        pygame.display.flip()
        clock.tick(60)

def Dam_Level():
    global SCREEN_WIDTH, SCREEN_HEIGHT, border_frame, level_completed, level_scores
    global control_panel, up_active, up_inactive, down_active, down_inactive
    spillway_index = 0
    spillway_frames = load_dam_frames(NUM_SPILLWAY_FRAMES, SPILLWAY_PATH_TEMPLATE)
    water_frames = load_dam_frames(NUM_WATER_FRAMES, WATER_PATH_TEMPLATE)
    flow1_index = 0
    flow2_index = 0
    flow3_index = 0
    flow4_index = 0
    flow1_frames = load_dam_frames(NUM_FLOW_FRAMES, FLOW_PATH_TEMPLATE)
    flow2_frames = load_dam_frames(NUM_FLOW_FRAMES, FLOW2_PATH_TEMPLATE)
    flow3_frames = load_dam_frames(NUM_FLOW_FRAMES, FLOW3_PATH_TEMPLATE)
    flow4_frames = load_dam_frames(NUM_FLOW_FRAMES, FLOW4_PATH_TEMPLATE)
    turbine1_index = 0
    turbine2_index = 0
    turbine3_index = 0
    turbine4_index = 0
    turbine1_frames = load_dam_frames(NUM_TURBINE_FRAMES, TURBINE_PATH_TEMPLATE)
    turbine2_frames = load_dam_frames(NUM_TURBINE_FRAMES, TURBINE2_PATH_TEMPLATE)
    turbine3_frames = load_dam_frames(NUM_TURBINE_FRAMES, TURBINE3_PATH_TEMPLATE)
    turbine4_frames = load_dam_frames(NUM_TURBINE_FRAMES, TURBINE4_PATH_TEMPLATE)
    bar_frames = load_bar_frames()
    static_background_image = load_image('assets/DamSequences/DamStatics/DamStatics.jpg')
    static_tube_1_image = load_image('assets/DamSequences/DamStatics/FullTube1.jpg')
    static_tube_2_image = load_image('assets/DamSequences/DamStatics/FullTube2.jpg')
    open_gate_image = load_image('assets/DamSequences/Gate Cuts/OpenGates.jpg')
    open_gate2_image = load_image('assets/DamSequences/Gate Cuts 2/OpenGates2.jpg')
    open_gate3_image = load_image('assets/DamSequences/Gate Cuts 3/OpenGates3.jpg')
    open_gate4_image = load_image('assets/DamSequences/Gate Cuts 4/OpenGates4.jpg')
    closed_gate_image = load_image('assets/DamSequences/Gate Cuts/ClosedGates.jpg')
    closed_gate2_image = load_image('assets/DamSequences/Gate Cuts 2/ClosedGates2.jpg')
    closed_gate3_image = load_image('assets/DamSequences/Gate Cuts 3/ClosedGates3.jpg')
    closed_gate4_image = load_image('assets/DamSequences/Gate Cuts 4/ClosedGates4.jpg')
    border_frame_image = border_frame.copy()
    control_panel_image = control_panel.copy()
    up_active_image = up_active.copy()
    up_inactive_image = up_inactive.copy()
    down_active_image = down_active.copy()
    down_inactive_image = down_inactive.copy()

    static_background_image = pygame.transform.scale(static_background_image, (static_background_image.get_size()[0]*SCREEN_WIDTH/1920, static_background_image.get_size()[1]*SCREEN_HEIGHT/1080))
    static_tube_1_image = pygame.transform.scale(static_tube_1_image, (static_tube_1_image.get_size()[0]*SCREEN_WIDTH/1920, static_tube_1_image.get_size()[1]*SCREEN_HEIGHT/1080))
    static_tube_2_image = pygame.transform.scale(static_tube_2_image, (static_tube_2_image.get_size()[0]*SCREEN_WIDTH/1920, static_tube_2_image.get_size()[1]*SCREEN_HEIGHT/1080))
    open_gate_image = pygame.transform.scale(open_gate_image, (open_gate_image.get_size()[0]*SCREEN_WIDTH/1920, open_gate_image.get_size()[1]*SCREEN_HEIGHT/1080))
    open_gate2_image = pygame.transform.scale(open_gate2_image, (open_gate2_image.get_size()[0]*SCREEN_WIDTH/1920, open_gate2_image.get_size()[1]*SCREEN_HEIGHT/1080))
    open_gate3_image = pygame.transform.scale(open_gate3_image, (open_gate3_image.get_size()[0]*SCREEN_WIDTH/1920, open_gate3_image.get_size()[1]*SCREEN_HEIGHT/1080))
    open_gate4_image = pygame.transform.scale(open_gate4_image, (open_gate4_image.get_size()[0]*SCREEN_WIDTH/1920, open_gate4_image.get_size()[1]*SCREEN_HEIGHT/1080))
    closed_gate_image = pygame.transform.scale(closed_gate_image, (closed_gate_image.get_size()[0]*SCREEN_WIDTH/1920, closed_gate_image.get_size()[1]*SCREEN_HEIGHT/1080))
    closed_gate2_image = pygame.transform.scale(closed_gate2_image, (closed_gate2_image.get_size()[0]*SCREEN_WIDTH/1920, closed_gate2_image.get_size()[1]*SCREEN_HEIGHT/1080))
    closed_gate3_image = pygame.transform.scale(closed_gate3_image, (closed_gate3_image.get_size()[0]*SCREEN_WIDTH/1920, closed_gate3_image.get_size()[1]*SCREEN_HEIGHT/1080))
    closed_gate4_image = pygame.transform.scale(closed_gate4_image, (closed_gate4_image.get_size()[0]*SCREEN_WIDTH/1920, closed_gate4_image.get_size()[1]*SCREEN_HEIGHT/1080))

    # Initialize game state
    game_state = reset_Dam()
    clock = pygame.time.Clock()

    # Button positioning
    button_width = up_active_image.get_width() * SCREEN_WIDTH / 1920
    button_height = up_active_image.get_height() * SCREEN_HEIGHT / 1080
    button_x = SCREEN_WIDTH * 0.45
    up_button_y = SCREEN_HEIGHT * 0.83
    down_button_y = SCREEN_HEIGHT * 0.93

    up_active_image = pygame.transform.smoothscale(up_active_image, (int(button_width), int(button_height)))
    up_inactive_image = pygame.transform.smoothscale(up_inactive_image, (int(button_width), int(button_height)))
    down_active_image = pygame.transform.smoothscale(down_active_image, (int(button_width), int(button_height)))
    down_inactive_image = pygame.transform.smoothscale(down_inactive_image, (int(button_width), int(button_height)))

    up_button_rect = pygame.Rect(button_x, up_button_y, button_width, button_height)
    down_button_rect = pygame.Rect(button_x, down_button_y, button_width, button_height)

    graph_width = (1200*screen.get_size()[0] / 1920)/2.8
    graph_height = (900*screen.get_size()[1] / 1080)/2.8
    graph_x = SCREEN_WIDTH - graph_width - SCREEN_WIDTH * 0.02
    graph_y = int(SCREEN_HEIGHT * 0.05) 
    graph_border = pygame.transform.smoothscale(border_frame_image, (int(graph_width*1.025), int(graph_height*1.025)))

    panel_width = (control_panel_image.get_size()[0] * SCREEN_WIDTH / 1920)/2
    panel_height = (control_panel_image.get_size()[1] * SCREEN_HEIGHT / 1080)/2
    scaled_panel = pygame.transform.smoothscale(control_panel_image, (panel_width, panel_height))
    panel_x = 0
    panel_y = int(SCREEN_HEIGHT * 0.8)
    orange_panel = tint_surface(scaled_panel, (255, 100, 0))
    orange_panel.set_alpha(127)
    red_panel = tint_surface(scaled_panel, (255, 0, 0))
    red_panel.set_alpha(127)
    scaled_panel.set_alpha(127)

    # Set the font size relative to control panel height
    panel_font_size = int(panel_height * 0.1)
    panel_font = pygame.font.Font(resource_path("assets/Fonts/Electrolize-Regular.ttf"), panel_font_size)

    water_level_text = "Reservoir Water Level"

    level_surface = panel_font.render(water_level_text, True, (255, 255, 255))

    square_size = int(panel_height * 0.15)  # Adjust as needed
    spacing_between_squares = int(square_size * 0.3)

    # Exit button setup (bottom right)
    exit_width = SCREEN_WIDTH * 0.15
    exit_height = SCREEN_HEIGHT * 0.06
    exit_rect = pygame.Rect(SCREEN_WIDTH - exit_width - SCREEN_WIDTH * 0.02,
                            SCREEN_HEIGHT - exit_height - SCREEN_HEIGHT * 0.02,
                            exit_width, exit_height)
    exit_frame = pygame.transform.smoothscale(border_frame, (int(exit_width), int(exit_height)))
    exit_red_frame = tint_surface(exit_frame, (255, 0, 0))
    exit_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.03))
    exit_text = exit_font.render("Exit", True, (255, 255, 255))
    exit_text_rect = exit_text.get_rect(center=exit_rect.center)

    # Skip button setup
    skip_width = SCREEN_WIDTH * 0.15
    skip_height = SCREEN_HEIGHT * 0.06
    skip_rect = pygame.Rect(SCREEN_WIDTH * 0.65,
                            SCREEN_HEIGHT - skip_height - SCREEN_HEIGHT * 0.02,
                            skip_width, skip_height)
    skip_frame = pygame.transform.smoothscale(border_frame, (int(skip_width), int(skip_height)))
    skip_green_frame = tint_surface(skip_frame, (0, 200, 0))
    skip_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.03))
    skip_text = skip_font.render("Skip", True, (255, 255, 255))
    skip_text_rect = skip_text.get_rect(center=skip_rect.center)

    performance_x = SCREEN_WIDTH*0.01
    performance_y = SCREEN_HEIGHT*0.05  

    score_x = SCREEN_WIDTH*0.01
    score_y = SCREEN_HEIGHT*0.09

    # Load electricity image
    light_image = load_image("assets/Light.png")
    light_image = pygame.transform.smoothscale(light_image, (light_image.get_size()[0]*0.05*(SCREEN_WIDTH/1280),light_image.get_size()[1]*0.05*(SCREEN_HEIGHT/720)))
    # Define light animation positions
    light_positions = [
        (SCREEN_WIDTH*0.444, SCREEN_HEIGHT*0.71),
        (SCREEN_WIDTH*0.438, SCREEN_HEIGHT*0.71),
        (SCREEN_WIDTH*0.432, SCREEN_HEIGHT*0.705),
        (SCREEN_WIDTH*0.426, SCREEN_HEIGHT*0.70),
        (SCREEN_WIDTH*0.42, SCREEN_HEIGHT*0.695),
        (SCREEN_WIDTH*0.414, SCREEN_HEIGHT*0.69),
        (SCREEN_WIDTH*0.408, SCREEN_HEIGHT*0.685),
        (SCREEN_WIDTH*0.402, SCREEN_HEIGHT*0.68),
        (SCREEN_WIDTH*0.399, SCREEN_HEIGHT*0.69),
        (SCREEN_WIDTH*0.396, SCREEN_HEIGHT*0.70),
        (SCREEN_WIDTH*0.393, SCREEN_HEIGHT*0.71),
        (SCREEN_WIDTH*0.39, SCREEN_HEIGHT*0.72),
        (SCREEN_WIDTH*0.387, SCREEN_HEIGHT*0.73),
        (SCREEN_WIDTH*0.384, SCREEN_HEIGHT*0.74),
        (SCREEN_WIDTH*0.381, SCREEN_HEIGHT*0.75),
        (SCREEN_WIDTH*0.379, SCREEN_HEIGHT*0.76),
        (SCREEN_WIDTH*0.377, SCREEN_HEIGHT*0.77),
        (SCREEN_WIDTH*0.374, SCREEN_HEIGHT*0.78),
        (SCREEN_WIDTH*0.371, SCREEN_HEIGHT*0.79),
        (SCREEN_WIDTH*0.3685, SCREEN_HEIGHT*0.80),
        (SCREEN_WIDTH*0.366, SCREEN_HEIGHT*0.81),
        (SCREEN_WIDTH*0.3625, SCREEN_HEIGHT*0.82),
        (SCREEN_WIDTH*0.358, SCREEN_HEIGHT*0.83),
        (SCREEN_WIDTH*0.352, SCREEN_HEIGHT*0.835),
        (SCREEN_WIDTH*0.345, SCREEN_HEIGHT*0.84),
        (SCREEN_WIDTH*0.339, SCREEN_HEIGHT*0.8455),
        (SCREEN_WIDTH*0.333, SCREEN_HEIGHT*0.85),
        (SCREEN_WIDTH*0.326, SCREEN_HEIGHT*0.855),
        (SCREEN_WIDTH*0.32, SCREEN_HEIGHT*0.86),
        (SCREEN_WIDTH*0.314, SCREEN_HEIGHT*0.865),
        (SCREEN_WIDTH*0.316, SCREEN_HEIGHT*0.87),
        (SCREEN_WIDTH*0.319, SCREEN_HEIGHT*0.88),
        (SCREEN_WIDTH*0.322, SCREEN_HEIGHT*0.89),
        (SCREEN_WIDTH*0.3255, SCREEN_HEIGHT*0.90),
        (SCREEN_WIDTH*0.329, SCREEN_HEIGHT*0.91),
        (SCREEN_WIDTH*0.332, SCREEN_HEIGHT*0.92),
        (SCREEN_WIDTH*0.3355, SCREEN_HEIGHT*0.93),
        (SCREEN_WIDTH*0.3385, SCREEN_HEIGHT*0.94),
        (SCREEN_WIDTH*0.3415, SCREEN_HEIGHT*0.95),
        (SCREEN_WIDTH*0.3445, SCREEN_HEIGHT*0.96),
        (SCREEN_WIDTH*0.349, SCREEN_HEIGHT*0.97),
        (SCREEN_WIDTH*0.352, SCREEN_HEIGHT*0.98),
        (SCREEN_WIDTH*0.356, SCREEN_HEIGHT*0.99)
    ]
    light2_positions = [
        (SCREEN_WIDTH*0.446, SCREEN_HEIGHT*0.714),
        (SCREEN_WIDTH*0.438, SCREEN_HEIGHT*0.71),
        (SCREEN_WIDTH*0.432, SCREEN_HEIGHT*0.705),
        (SCREEN_WIDTH*0.426, SCREEN_HEIGHT*0.70),
        (SCREEN_WIDTH*0.42, SCREEN_HEIGHT*0.695),
        (SCREEN_WIDTH*0.414, SCREEN_HEIGHT*0.69),
        (SCREEN_WIDTH*0.407, SCREEN_HEIGHT*0.685),
        (SCREEN_WIDTH*0.404, SCREEN_HEIGHT*0.69),
        (SCREEN_WIDTH*0.401, SCREEN_HEIGHT*0.7),
        (SCREEN_WIDTH*0.398, SCREEN_HEIGHT*0.71),
        (SCREEN_WIDTH*0.395, SCREEN_HEIGHT*0.72),
        (SCREEN_WIDTH*0.392, SCREEN_HEIGHT*0.73),
        (SCREEN_WIDTH*0.39, SCREEN_HEIGHT*0.74),
        (SCREEN_WIDTH*0.387, SCREEN_HEIGHT*0.75),
        (SCREEN_WIDTH*0.3845, SCREEN_HEIGHT*0.76),
        (SCREEN_WIDTH*0.3822, SCREEN_HEIGHT*0.77),
        (SCREEN_WIDTH*0.3805, SCREEN_HEIGHT*0.78),
        (SCREEN_WIDTH*0.378, SCREEN_HEIGHT*0.79),
        (SCREEN_WIDTH*0.3744, SCREEN_HEIGHT*0.8),
        (SCREEN_WIDTH*0.3722, SCREEN_HEIGHT*0.81),
        (SCREEN_WIDTH*0.3695, SCREEN_HEIGHT*0.82),
        (SCREEN_WIDTH*0.367, SCREEN_HEIGHT*0.83),
        (SCREEN_WIDTH*0.361, SCREEN_HEIGHT*0.84),
        (SCREEN_WIDTH*0.353, SCREEN_HEIGHT*0.845),
        (SCREEN_WIDTH*0.345, SCREEN_HEIGHT*0.85),
        (SCREEN_WIDTH*0.338, SCREEN_HEIGHT*0.855),
        (SCREEN_WIDTH*0.331, SCREEN_HEIGHT*0.86),
        (SCREEN_WIDTH*0.324, SCREEN_HEIGHT*0.865),
        (SCREEN_WIDTH*0.324, SCREEN_HEIGHT*0.875),
        (SCREEN_WIDTH*0.328, SCREEN_HEIGHT*0.885),
        (SCREEN_WIDTH*0.331, SCREEN_HEIGHT*0.895),
        (SCREEN_WIDTH*0.3345, SCREEN_HEIGHT*0.905),
        (SCREEN_WIDTH*0.338, SCREEN_HEIGHT*0.915),
        (SCREEN_WIDTH*0.341, SCREEN_HEIGHT*0.925),
        (SCREEN_WIDTH*0.344, SCREEN_HEIGHT*0.935),
        (SCREEN_WIDTH*0.349, SCREEN_HEIGHT*0.939)
    ]
    light3_positions = [
        (SCREEN_WIDTH*0.446, SCREEN_HEIGHT*0.718),
        (SCREEN_WIDTH*0.438, SCREEN_HEIGHT*0.71),
        (SCREEN_WIDTH*0.432, SCREEN_HEIGHT*0.705),
        (SCREEN_WIDTH*0.426, SCREEN_HEIGHT*0.70),
        (SCREEN_WIDTH*0.42, SCREEN_HEIGHT*0.695),
        (SCREEN_WIDTH*0.416, SCREEN_HEIGHT*0.69),
        (SCREEN_WIDTH*0.41, SCREEN_HEIGHT*0.685),
        (SCREEN_WIDTH*0.408, SCREEN_HEIGHT*0.69),
        (SCREEN_WIDTH*0.406, SCREEN_HEIGHT*0.7),
        (SCREEN_WIDTH*0.404, SCREEN_HEIGHT*0.71),
        (SCREEN_WIDTH*0.402, SCREEN_HEIGHT*0.72),
        (SCREEN_WIDTH*0.399, SCREEN_HEIGHT*0.73),
        (SCREEN_WIDTH*0.396, SCREEN_HEIGHT*0.74),
        (SCREEN_WIDTH*0.394, SCREEN_HEIGHT*0.75),
        (SCREEN_WIDTH*0.391, SCREEN_HEIGHT*0.76),
        (SCREEN_WIDTH*0.389, SCREEN_HEIGHT*0.77),
        (SCREEN_WIDTH*0.386, SCREEN_HEIGHT*0.78),
        (SCREEN_WIDTH*0.384, SCREEN_HEIGHT*0.79),
        (SCREEN_WIDTH*0.381, SCREEN_HEIGHT*0.8),
        (SCREEN_WIDTH*0.378, SCREEN_HEIGHT*0.81),
        (SCREEN_WIDTH*0.375, SCREEN_HEIGHT*0.82),
        (SCREEN_WIDTH*0.372, SCREEN_HEIGHT*0.83),
        (SCREEN_WIDTH*0.369, SCREEN_HEIGHT*0.84),
        (SCREEN_WIDTH*0.36, SCREEN_HEIGHT*0.85),
        (SCREEN_WIDTH*0.355, SCREEN_HEIGHT*0.86),
        (SCREEN_WIDTH*0.36, SCREEN_HEIGHT*0.87),
        (SCREEN_WIDTH*0.364, SCREEN_HEIGHT*0.88),
        (SCREEN_WIDTH*0.367, SCREEN_HEIGHT*0.89),
        (SCREEN_WIDTH*0.37, SCREEN_HEIGHT*0.9),
        (SCREEN_WIDTH*0.374, SCREEN_HEIGHT*0.91),
        (SCREEN_WIDTH*0.378, SCREEN_HEIGHT*0.92),
        (SCREEN_WIDTH*0.382, SCREEN_HEIGHT*0.93),
        (SCREEN_WIDTH*0.386, SCREEN_HEIGHT*0.94),
        (SCREEN_WIDTH*0.39, SCREEN_HEIGHT*0.95),
        (SCREEN_WIDTH*0.394, SCREEN_HEIGHT*0.96),
        (SCREEN_WIDTH*0.398, SCREEN_HEIGHT*0.97),
        (SCREEN_WIDTH*0.405, SCREEN_HEIGHT*0.97),
    ]
    light4_positions = [
        (SCREEN_WIDTH*0.446, SCREEN_HEIGHT*0.718),
        (SCREEN_WIDTH*0.438, SCREEN_HEIGHT*0.71),
        (SCREEN_WIDTH*0.432, SCREEN_HEIGHT*0.705),
        (SCREEN_WIDTH*0.426, SCREEN_HEIGHT*0.70),
        (SCREEN_WIDTH*0.42, SCREEN_HEIGHT*0.695),
        (SCREEN_WIDTH*0.416, SCREEN_HEIGHT*0.69),
        (SCREEN_WIDTH*0.4125, SCREEN_HEIGHT*0.695),
        (SCREEN_WIDTH*0.411, SCREEN_HEIGHT*0.7),
        (SCREEN_WIDTH*0.40875, SCREEN_HEIGHT*0.71),
        (SCREEN_WIDTH*0.4065, SCREEN_HEIGHT*0.72),
        (SCREEN_WIDTH*0.40425, SCREEN_HEIGHT*0.73),
        (SCREEN_WIDTH*0.402, SCREEN_HEIGHT*0.74),
        (SCREEN_WIDTH*0.39975, SCREEN_HEIGHT*0.75),
        (SCREEN_WIDTH*0.3975, SCREEN_HEIGHT*0.76),
        (SCREEN_WIDTH*0.39525, SCREEN_HEIGHT*0.77),
        (SCREEN_WIDTH*0.39275, SCREEN_HEIGHT*0.78),
        (SCREEN_WIDTH*0.390, SCREEN_HEIGHT*0.79),
        (SCREEN_WIDTH*0.388, SCREEN_HEIGHT*0.8),
        (SCREEN_WIDTH*0.386, SCREEN_HEIGHT*0.81),
        (SCREEN_WIDTH*0.3835, SCREEN_HEIGHT*0.82),
        (SCREEN_WIDTH*0.381, SCREEN_HEIGHT*0.83),
        (SCREEN_WIDTH*0.379, SCREEN_HEIGHT*0.84),
        (SCREEN_WIDTH*0.37, SCREEN_HEIGHT*0.85),
        (SCREEN_WIDTH*0.363, SCREEN_HEIGHT*0.86),
        (SCREEN_WIDTH*0.366, SCREEN_HEIGHT*0.87),
        (SCREEN_WIDTH*0.37, SCREEN_HEIGHT*0.88),
        (SCREEN_WIDTH*0.374, SCREEN_HEIGHT*0.89),
        (SCREEN_WIDTH*0.3775, SCREEN_HEIGHT*0.90),
        (SCREEN_WIDTH*0.381, SCREEN_HEIGHT*0.91),
        (SCREEN_WIDTH*0.386, SCREEN_HEIGHT*0.91)
    ]
    light_index = 0
    light2_index = 4
    light3_index = 8
    light4_index = 12
    light5_index = 16

    light6_index = 0
    light7_index = 4
    light8_index = 8
    light9_index = 12
    light10_index = 16

    light11_index = 0
    light12_index = 4
    light13_index = 8
    light14_index = 12
    light15_index = 16

    light16_index = 0
    light17_index = 4
    light18_index = 8
    light19_index = 12
    light20_index = 16

    if SCREEN_WIDTH == 960:
        performance_font = pygame.font.Font(resource_path("assets/Fonts/Electrolize-Regular.ttf"), 18)
        complete_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Regular.ttf"), 42)
        warning_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), 20)
    elif SCREEN_WIDTH == 1280:
        performance_font = pygame.font.Font(resource_path("assets/Fonts/Electrolize-Regular.ttf"), 27)
        complete_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Regular.ttf"), 64)
        warning_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), 30)
    elif SCREEN_WIDTH == 1600:
        performance_font = pygame.font.Font(resource_path("assets/Fonts/Electrolize-Regular.ttf"), 36)
        complete_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Regular.ttf"), 84)
        warning_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), 40)

    heatmap_frame = pygame.transform.smoothscale(border_frame, (SCREEN_WIDTH*0.25, SCREEN_HEIGHT*0.35))
    scaled_score = 0

    display = 0
    power_info_counter = 0
    first_run = True
    running = True
    while running:
        if game_state['level_complete']:
            screen.blit(static_background_image, (0,0))

            # Draw the overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)  # Semi-transparent
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))

            complete_text = "Level complete! Your score was:"
            complete_label = complete_font.render(complete_text, True, (255, 255, 255))
            score_text = f"{int(calculate_score((game_state['score']), (game_state['wasted_water']), factor=7000))}"
            score_label = complete_font.render(score_text, True, (255, 255, 255))

            screen.blit(complete_label, ((SCREEN_WIDTH - complete_label.get_width()) // 2, SCREEN_HEIGHT // 3))
            screen.blit(score_label, ((SCREEN_WIDTH - score_label.get_width()) // 2, SCREEN_HEIGHT // 2))
        else:
            delta_time = clock.tick(60) / 1000.0
            # Update elapsed time
            game_state['elapsed_time'] += delta_time
            # Check for level completion
            if game_state['elapsed_time'] >= DAM_LEVEL_DURATION:
                game_state['level_complete'] = True
            # Calculate the number of open gates
            open_gates = sum(game_state['gates'])
            game_state['active_outer_flow'] = (open_gates / 4) * game_state['base_outer_flow']
            # Update the water level
            if game_state['water_level'] > WATER_LEVEL_THRESHOLD and game_state['water_level'] < MAX_WATER_LEVEL:
                # Apply outflow only if water level is above the threshold
                game_state['spillway_rate'] = 0
                game_state['water_volume'] = max(0, game_state['water_volume'] + (game_state['intake_rate'] - game_state['active_outer_flow']) * delta_time)
            elif game_state['water_level'] >= MAX_WATER_LEVEL and game_state['active_outer_flow']<game_state['intake_rate']:
                game_state['spillway_rate'] = game_state['intake_rate'] - game_state['active_outer_flow']
                game_state['water_volume'] = ((MAX_WATER_LEVEL) ** 2)*2
            elif game_state['water_level'] >= MAX_WATER_LEVEL:
                game_state['spillway_rate'] = 0
                game_state['water_volume'] = game_state['water_volume'] + (game_state['intake_rate'] - game_state['active_outer_flow']) * delta_time
            elif game_state['water_level'] <= WATER_LEVEL_THRESHOLD and game_state['active_outer_flow'] > game_state['intake_rate']:
                game_state['spillway_rate'] = 0
                game_state['active_outer_flow'] = game_state['intake_rate']
                game_state['water_volume'] = max(0, game_state['water_volume'])
            else:
                game_state['spillway_rate'] = 0
                game_state['water_volume'] = max(0, game_state['water_volume'] + game_state['intake_rate'] * delta_time)

            game_state['water_level'] = volume_to_elevation(game_state['water_volume'],0.5,0)

            bar_index = int((game_state['water_level']/MAX_WATER_LEVEL)*100)
            bar_index = min(100,bar_index)
            bar_image = bar_frames[bar_index]

            # Calculate wasted water via spillway
            game_state['wasted_water'] = game_state['wasted_water']+(game_state['spillway_rate']*delta_time)

            # Calculate power generated
            power_generated = 4.3 * (game_state['water_level']) * game_state['active_outer_flow']
            game_state['power_data'].append(power_generated)
            power_info_counter += 1

            
            screen.blit(static_background_image, (0, 0))

            # Draw the static tubes
            water_index = min(int((game_state['water_level']/MAX_WATER_LEVEL) * (126)), 126)
            water_level_image = water_frames[water_index]
            screen.blit(water_level_image, (int(SCREEN_WIDTH*0.0255), 0))
            if game_state['spillway_rate'] > 0:
                spillway_index = spillway_index % 24
                spillway_index += 1
                spillway_image = spillway_frames[spillway_index]
                screen.blit(spillway_image, (int(SCREEN_WIDTH*.6172),int(SCREEN_HEIGHT*.1657)))
            else:
                spillway_index = 0
                screen.blit(spillway_frames[spillway_index], (int(SCREEN_WIDTH*.6172),int(SCREEN_HEIGHT*.1657)))
            screen.blit(static_tube_1_image, (int(SCREEN_WIDTH * 0.4025), int(SCREEN_HEIGHT * 0.3480)))
            screen.blit(static_tube_2_image, (int(SCREEN_WIDTH * 0.4737), int(SCREEN_HEIGHT * 0.5771)))
            
            if game_state['gates'][3] == 0:
                screen.blit(closed_gate4_image, (int(SCREEN_WIDTH * 0.553), int(SCREEN_HEIGHT * 0.3478)))
                screen.blit(flow4_frames[36], (int(SCREEN_WIDTH * 0.6881), int(SCREEN_HEIGHT * 0.7714)))
                screen.blit(turbine4_frames[turbine4_index], (int(SCREEN_WIDTH * 0.645), int(SCREEN_HEIGHT * 0.6223)))
                light_index = 0
                light2_index = 4
                light3_index = 8
                light4_index = 12
                light5_index = 16
            else:
                screen.blit(open_gate4_image, (int(SCREEN_WIDTH * 0.553), int(SCREEN_HEIGHT * 0.3478)))
                screen.blit(flow4_frames[flow4_index], (int(SCREEN_WIDTH * 0.6881), int(SCREEN_HEIGHT * 0.7714)))
                flow4_index += 1
                flow4_index = flow4_index % 35
                screen.blit(turbine4_frames[turbine4_index], (int(SCREEN_WIDTH * 0.645), int(SCREEN_HEIGHT * 0.6223)))
                turbine4_index += 1
                turbine4_index = turbine4_index % 33
                light_index = (light_index + 1) % len(light_positions)
                light2_index = (light2_index + 1) % len(light_positions)
                light3_index = (light3_index + 1) % len(light_positions)
                light4_index = (light4_index + 1) % len(light_positions)
                light5_index = (light5_index + 1) % len(light_positions)
                screen.blit(light_image, light_positions[light_index])
                screen.blit(light_image, light_positions[light2_index])
                screen.blit(light_image, light_positions[light3_index])
                screen.blit(light_image, light_positions[light4_index])
                screen.blit(light_image, light_positions[light5_index])

            if game_state['gates'][2] == 0:
                screen.blit(closed_gate3_image, (int(SCREEN_WIDTH * 0.511), int(SCREEN_HEIGHT * 0.3611)))
                screen.blit(flow3_frames[36], (int(SCREEN_WIDTH * 0.6595), int(SCREEN_HEIGHT * 0.81805)))
                screen.blit(turbine3_frames[turbine3_index], (int(SCREEN_WIDTH * 0.6051), int(SCREEN_HEIGHT * 0.6486)))
                light6_index = 0
                light7_index = 4
                light8_index = 8
                light9_index = 12
                light10_index = 16
            else:
                screen.blit(open_gate3_image, (int(SCREEN_WIDTH * 0.511), int(SCREEN_HEIGHT * 0.3611)))
                screen.blit(flow3_frames[flow3_index], (int(SCREEN_WIDTH * 0.6595), int(SCREEN_HEIGHT * 0.81805)))
                flow3_index += 1
                flow3_index = flow3_index % 35
                screen.blit(turbine3_frames[turbine3_index], (int(SCREEN_WIDTH * 0.6051), int(SCREEN_HEIGHT * 0.6486)))
                turbine3_index += 1
                turbine3_index = turbine3_index % 33
                light6_index = (light6_index + 1) % len(light2_positions)
                light7_index = (light7_index + 1) % len(light2_positions)
                light8_index = (light8_index + 1) % len(light2_positions)
                light9_index = (light9_index + 1) % len(light2_positions)
                light10_index = (light10_index + 1) % len(light2_positions)
                screen.blit(light_image, light2_positions[light6_index])
                screen.blit(light_image, light2_positions[light7_index])
                screen.blit(light_image, light2_positions[light8_index])
                screen.blit(light_image, light2_positions[light9_index])
                screen.blit(light_image, light2_positions[light10_index])

            if game_state['gates'][1] == 0:
                screen.blit(closed_gate2_image, (int(SCREEN_WIDTH * 0.475), int(SCREEN_HEIGHT * 0.3767)))
                screen.blit(flow2_frames[36], (int(SCREEN_WIDTH * 0.6131), int(SCREEN_HEIGHT * 0.8406)))
                screen.blit(turbine2_frames[turbine2_index], (int(SCREEN_WIDTH * 0.564), int(SCREEN_HEIGHT * 0.6714)))
                light11_index = 0
                light12_index = 4
                light13_index = 8
                light14_index = 12
                light15_index = 16
            else:
                screen.blit(open_gate2_image, (int(SCREEN_WIDTH * 0.475), int(SCREEN_HEIGHT * 0.3767)))
                screen.blit(flow2_frames[flow2_index], (int(SCREEN_WIDTH * 0.6131), int(SCREEN_HEIGHT * 0.8406)))
                flow2_index += 1
                flow2_index = flow2_index % 35
                screen.blit(turbine2_frames[turbine2_index], (int(SCREEN_WIDTH * 0.564), int(SCREEN_HEIGHT * 0.6714)))
                turbine2_index += 1
                turbine2_index = turbine2_index % 33
                light11_index = (light11_index + 1) % len(light3_positions)
                light12_index = (light12_index + 1) % len(light3_positions)
                light13_index = (light13_index + 1) % len(light3_positions)
                light14_index = (light14_index + 1) % len(light3_positions)
                light15_index = (light15_index + 1) % len(light3_positions)
                screen.blit(light_image, light3_positions[light11_index])
                screen.blit(light_image, light3_positions[light12_index])
                screen.blit(light_image, light3_positions[light13_index])
                screen.blit(light_image, light3_positions[light14_index])
                screen.blit(light_image, light3_positions[light15_index])

            if game_state['gates'][0] == 0:
                screen.blit(closed_gate_image, (int(SCREEN_WIDTH * 0.4340), int(SCREEN_HEIGHT * 0.3914)))
                screen.blit(flow1_frames[36], (int(SCREEN_WIDTH * 0.5767), int(SCREEN_HEIGHT * 0.8764)))
                screen.blit(turbine1_frames[turbine1_index], (int(SCREEN_WIDTH * 0.5247), int(SCREEN_HEIGHT * 0.7006)))
                light16_index = 0
                light17_index = 4
                light18_index = 8
                light19_index = 12
                light20_index = 16
            else:
                screen.blit(open_gate_image, (int(SCREEN_WIDTH * 0.4340), int(SCREEN_HEIGHT * 0.3914)))
                screen.blit(flow1_frames[flow1_index], (int(SCREEN_WIDTH * 0.5767), int(SCREEN_HEIGHT * 0.8764)))
                flow1_index += 1
                flow1_index = flow1_index % 35
                screen.blit(turbine1_frames[turbine1_index], (int(SCREEN_WIDTH * 0.5247), int(SCREEN_HEIGHT * 0.7006)))
                turbine1_index += 1
                turbine1_index = turbine1_index % 33
                light16_index = (light16_index + 1) % len(light4_positions)
                light17_index = (light17_index + 1) % len(light4_positions)
                light18_index = (light18_index + 1) % len(light4_positions)
                light19_index = (light19_index + 1) % len(light4_positions)
                light20_index = (light20_index + 1) % len(light4_positions)
                screen.blit(light_image, light4_positions[light16_index])
                screen.blit(light_image, light4_positions[light17_index])
                screen.blit(light_image, light4_positions[light18_index])
                screen.blit(light_image, light4_positions[light19_index])
                screen.blit(light_image, light4_positions[light20_index])

            # Update the graph with new x range and power data
            graph_filename = update_dam_graph(game_state['x_start'], game_state['x_end'], game_state['power_data'], display)
            graph_image = load_image(graph_filename)

            display = display % (len(LOAD_CURVE)-1)
            display += 1

            scaled_graph_image = pygame.transform.scale(graph_image, (graph_width, graph_height))
            screen.blit(graph_border, (graph_x, graph_y))
            screen.blit(scaled_graph_image, (graph_x, graph_y))

             # Trim power data to match the visible window
            if len(game_state['power_data']) > 10:
                game_state['power_data'] = game_state['power_data'][-10:]

            # Update the x range to simulate movement
            game_state['x_start'] += 0.05
            game_state['x_end'] += 0.05

            # Display the water wasted
            waste_status = f"Average Water Spilled: {int(2000*(game_state['wasted_water']/game_state['elapsed_time']))} cfs"
            waste_label = performance_font.render(waste_status, True, (255, 255, 255))
            screen.blit(waste_label, (SCREEN_WIDTH*0.01, SCREEN_HEIGHT*0.13))

            # Display elapsed time
            time_status = f"Time Remaining: {DAM_LEVEL_DURATION - int(game_state['elapsed_time'])} sec"
            time_label = performance_font.render(time_status, True, (255, 255, 255))
            screen.blit(time_label, (SCREEN_WIDTH*0.01, SCREEN_HEIGHT*0.01))

            # Calculate the load difference
            load_difference = truncate_float(power_generated - ((LOAD_CURVE[(display+10)%240]/6)-15), 2)
            # We did a massive rescaling of the visible values so this line fixes that, delete if any functional retooling is done
            scaled_load_difference = 0.14 * bar_index * truncate_float(power_generated - ((LOAD_CURVE[(display+10)%240]/6)-15), 2) / 4.3 / game_state['water_level']

            # Render the load difference text
            performance_text = f"Real-Time Power Imbalance: {scaled_load_difference:.2f} MW"
            performance_label = performance_font.render(performance_text, True, (255, 255, 255))

            # Blit the performance label to the screen
            screen.blit(performance_label, (performance_x, performance_y))

            # Update the score
            game_state['score'] += abs(load_difference)
            # Update the scaled difference without numerical back end changes
            scaled_score += abs(scaled_load_difference)

            # Render the score text
            score_text = f"Average Power Imbalance: {(scaled_score/power_info_counter):.2f} MW"
            score_label = performance_font.render(score_text, True, (255, 255, 255))

            # Blit the score label to the screen
            screen.blit(score_label, (score_x, score_y))
            
            # Draw the control panel
            if game_state['water_level'] == 0:
                screen.blit(red_panel, (panel_x, panel_y))
                screen.blit(warning_font.render("Warning: The reservoir has reached dead pool!", True, (255, 255, 255)), (SCREEN_WIDTH * 0.02, SCREEN_HEIGHT * 0.75))
            elif game_state['spillway_rate'] > 0:
                screen.blit(orange_panel, (panel_x, panel_y))
                screen.blit(warning_font.render("Warning: Water is being spilled!", True, (255, 255, 255)), (SCREEN_WIDTH * 0.02, SCREEN_HEIGHT * 0.75))
            else:
                screen.blit(scaled_panel, (panel_x, panel_y))

            # Prepare the lines
            outer_flow_text = f"Turbine Flow: {2000*int(game_state['active_outer_flow'])} cfs"
            power_text = f"Power Generated: {(0.14*int(game_state['active_outer_flow']) * bar_index):.2f} MW"  # Swapped order
            open_gates_text = f"Open Gates: {open_gates}"

            left_panel_lines = [outer_flow_text, power_text, open_gates_text]

            # Layout calculations
            left_spacing = (panel_height / (len(left_panel_lines) + 1)) / 1.75

            # Draw left column of text
            for i, line in enumerate(left_panel_lines):
                text_surface = panel_font.render(line, True, (255, 255, 255))
                if first_run:
                    text_x = panel_x + panel_width * 0.05  # Left margin
                text_y = panel_y + left_spacing * (i + 1) + SCREEN_HEIGHT*0.01
                screen.blit(text_surface, (text_x, text_y))

            screen.blit(level_surface, (SCREEN_WIDTH * 0.235, SCREEN_HEIGHT * 0.82))

            start_x = panel_x + panel_width * 0.05
            start_y = panel_y + left_spacing * (len(left_panel_lines) + 1)

            for i in range(4):
                gate_open = game_state['gates'][i] == 1
                alpha = 255 if gate_open else 64  # Full opacity if open, transparent if closed

                # Create a surface with per-pixel alpha
                gate_surface = pygame.Surface((square_size, square_size), pygame.SRCALPHA)
                gate_surface.fill((0, 206, 244, alpha))  # Blue with variable transparency

                x = start_x + i * (square_size + spacing_between_squares)
                screen.blit(gate_surface, (x, start_y))

            screen.blit(bar_image, (int(SCREEN_WIDTH * 0.285), int(SCREEN_HEIGHT * 0.83)))

            # Decide whether buttons should be active
            all_open = all(g == 1 for g in game_state['gates'])
            all_closed = all(g == 0 for g in game_state['gates'])

            up_image = up_inactive_image if all_open else up_active_image
            down_image = down_inactive_image if all_closed else down_active_image

            # Scale and draw buttons
            screen.blit(up_image, up_button_rect.topleft)
            screen.blit(down_image, down_button_rect.topleft)

            # Draw exit button
            screen.blit(exit_red_frame, exit_rect)
            screen.blit(exit_text, exit_text_rect)

            # Draw skip button
            screen.blit(skip_green_frame, skip_rect)
            screen.blit(skip_text, skip_text_rect)

            if first_run:
                dam_heatmap = draw_dam_colormap(game_state['active_outer_flow'], bar_index)
            else:
                dam_heatmap = update_dam_colormap(game_state['active_outer_flow'], bar_index)
            heatmap_rect = dam_heatmap.get_rect(center=(SCREEN_WIDTH // 7, int(0.57 * SCREEN_HEIGHT)))
            if SCREEN_WIDTH == 960:
                screen.blit(heatmap_frame, (heatmap_rect.x - heatmap_frame.get_width()//2 + dam_heatmap.get_width()//2 - SCREEN_WIDTH*.0025, heatmap_rect.y - heatmap_frame.get_height()//2 + dam_heatmap.get_height()//2))
            elif SCREEN_WIDTH == 1280:
                screen.blit(heatmap_frame, (heatmap_rect.x - heatmap_frame.get_width()//2 + dam_heatmap.get_width()//2 - SCREEN_WIDTH*.0075, heatmap_rect.y - heatmap_frame.get_height()//2 + dam_heatmap.get_height()//2))
            else:
                screen.blit(heatmap_frame, (heatmap_rect.x - heatmap_frame.get_width()//2 + dam_heatmap.get_width()//2 - SCREEN_WIDTH*.01, heatmap_rect.y - heatmap_frame.get_height()//2 + dam_heatmap.get_height()//2 - SCREEN_HEIGHT*.01))
            screen.blit(dam_heatmap, heatmap_rect)
            

            if first_run:
                first_run = False
            # Clean up the temporary file
            os.remove(graph_filename)

        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game_data()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    for i in range(len(game_state['gates'])):
                        if game_state['gates'][i] == 0:
                            game_state['gates'][i] = 1
                            break
                elif event.key == pygame.K_DOWN:
                    for i in reversed(range(len(game_state['gates']))):
                        if game_state['gates'][i] == 1:
                            game_state['gates'][i] = 0
                            break
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if game_state['level_complete']:
                    calc_score = calculate_score(game_state['score'], game_state['wasted_water'], factor=7000)
                    if level_scores[2] < calc_score:
                        level_scores[2] = calc_score
                    level_completed[2] = True
                    save_game_data()
                    return
                if up_button_rect.collidepoint(event.pos):
                    for i in range(len(game_state['gates'])):
                        if game_state['gates'][i] == 0:
                            game_state['gates'][i] = 1
                            break
                elif down_button_rect.collidepoint(event.pos):
                    for i in reversed(range(len(game_state['gates']))):
                        if game_state['gates'][i] == 1:
                            game_state['gates'][i] = 0
                            break
                elif exit_rect.collidepoint(event.pos):
                    return  # Exit this level
                elif skip_rect.collidepoint(event.pos):
                    level_completed[2] = True
                    save_game_data()
                    return
            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    for i in range(len(game_state['gates'])):
                        if game_state['gates'][i] == 0:
                            game_state['gates'][i] = 1
                            break
                elif event.y < 0:
                    for i in reversed(range(len(game_state['gates']))):
                        if game_state['gates'][i] == 1:
                            game_state['gates'][i] = 0
                            break

        pygame.display.flip()

def Level3_intro():
    global selected_character, SCREEN_WIDTH, SCREEN_HEIGHT

    scene1_image = load_image(f"assets/Transitions/SecondEquation/{selected_character}_Second.jpg")
    scene2_image = load_image("assets/Transitions/PSHGraphic.png")
    scene3_image = load_image("assets/PSHSequences/PSHStatics/UpperReservoirStatics.jpg")
    scene4_image = load_image("assets/PSHSequences/PSHStatics/PSHStatics.jpg")
    
    # Scale both scenes
    scene1_image = pygame.transform.smoothscale(scene1_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    scene2_image = pygame.transform.smoothscale(scene2_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    scene3_image = pygame.transform.smoothscale(scene3_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    scene4_image = pygame.transform.smoothscale(scene4_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    # --- Dialogue Data ---
    dialogue_scene1 = [
        ("Tom",
         "Pumped Storage Hydropower Plants are similar to Hydropower Dams, but they can use a pump "
         "that can take energy from the grid to move the water back to the upper reservoir. "
         "They basically act like a giant battery, storing energy when there is excess and releasing it when needed. ")
    ]
    dialogue_scene2 = [
        ("Tom",
         "Here you can see a schematic of our Pumped Storage Hydropower Plant! "
         "The two reservoirs form a closed loop, so the volume of water in the system is constant. "
         "You will need to balance the volume of the reservoirs while also matching the electricity demand of the city. "
         "Now come with me to the upper reservoir, where we will start!")
    ]
    dialogue_scene3 = [
        ("Tom",
         "This is the upper reservoir, where we store the water for release to generate power. "
         "When it is empty, we cannot generate power, so we need to pump water back up from the lower reservoir. "
         "Let's go look at our lower reservoir, where you will be controlling the flow of water!")
    ]
    dialogue_scene4 = [
        ("Tom",
         "This is the lower reservoir, where we have the turbines that generate power. "
         "This is your base of operations, where you can change the flow of water to be either pumping or releasing. "
         "If the upper reservoir is empty, you will need to pump water back up to it - keep this in mind as you try to follow the electricity demand! "
         ),
         ("Tom","You can control the flow using the arrow keys, buttons on the control panel, and by scrolling your mouse - give it a try!")
    ]
    scenes = [(scene1_image,dialogue_scene1),(scene2_image,dialogue_scene2),(scene3_image,dialogue_scene3),(scene4_image,dialogue_scene4)]
    run_dialogue(scenes)

def PSH_Exploration():
    static_background_image = load_image('assets/PSHSequences/PSHStatics/PSHStatics.jpg')
    static_background_image = pygame.transform.scale(static_background_image, (static_background_image.get_width() * SCREEN_WIDTH / 1920, static_background_image.get_height() * SCREEN_HEIGHT / 1080))
    upper_reservoir_image = load_image('assets/PSHSequences/PSHStatics/UpperReservoirStatics.jpg')
    upper_reservoir_image = pygame.transform.scale(upper_reservoir_image, ((upper_reservoir_image.get_width() * SCREEN_WIDTH / 1920)/2.5, (upper_reservoir_image.get_height() * SCREEN_HEIGHT / 1080)/2.5))

    caption_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Regular.ttf"), int(SCREEN_HEIGHT * 0.045))
    name_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.03))
    description_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Regular.ttf"), int(SCREEN_HEIGHT * 0.03))

    exploration_directions = caption_font.render("Explore the components by clicking on them!", True, (255, 255, 255))

    # PSH Upper Reservoir Frame Positioning (LEFT)
    upper_edge_y = int(SCREEN_HEIGHT * 0.08)
    left_edge_x = int(SCREEN_WIDTH * 0.01)
    border_width = upper_reservoir_image.get_width()*1.005
    border_height = upper_reservoir_image.get_height()*1.013
    border_x = left_edge_x*0.975
    border_y = upper_edge_y*0.975

    scaled_border = pygame.transform.smoothscale(border_frame, (border_width, border_height))

    graph_width = (1200*screen.get_size()[0] / 1920)/2.8
    graph_height = (900*screen.get_size()[1] / 1080)/2.8
    graph_x = SCREEN_WIDTH - graph_width - SCREEN_WIDTH * 0.01
    graph_y = int(SCREEN_HEIGHT * 0.1) 
    graph_border = pygame.transform.smoothscale(border_frame, (int(graph_width*1.025), int(graph_height*1.025)))

    graph_filename = update_psh_graph()
    graph_image = load_image(graph_filename)
    scaled_graph_image = pygame.transform.scale(graph_image, (graph_width, graph_height))

    # Define the positions and radii of the 9 clickable circles
    clickable_circles = [
        {"name": "Load and Generation Plot", "pos": (SCREEN_WIDTH * 0.85, SCREEN_HEIGHT * 0.25), "radius": SCREEN_WIDTH * 0.01},
        {"name": "Upper Reservoir", "pos": (SCREEN_WIDTH * 0.136, SCREEN_HEIGHT * 0.255), "radius": SCREEN_WIDTH * 0.01},
        {"name": "Lower Reservoir", "pos": (SCREEN_WIDTH * 0.95, SCREEN_HEIGHT * 0.6), "radius": SCREEN_WIDTH * 0.01},
        {"name": "Turbine Feed Pipes", "pos": (SCREEN_WIDTH * 0.325, SCREEN_HEIGHT * 0.6), "radius": SCREEN_WIDTH * 0.01},
        {"name": "Generator", "pos": (SCREEN_WIDTH * 0.5425, SCREEN_HEIGHT * 0.61), "radius": SCREEN_WIDTH * 0.01},
        {"name": "Turbine", "pos": (SCREEN_WIDTH * 0.5425, SCREEN_HEIGHT * 0.71), "radius": SCREEN_WIDTH * 0.01},
        {"name": "Valves", "pos": (SCREEN_WIDTH * 0.475, SCREEN_HEIGHT * 0.69), "radius": SCREEN_WIDTH * 0.01},
        {"name": "Frequency Converter", "pos": (SCREEN_WIDTH * 0.435, SCREEN_HEIGHT * 0.61), "radius": SCREEN_WIDTH * 0.01},
        {"name": "Step-up Transformer", "pos": (SCREEN_WIDTH * 0.53, SCREEN_HEIGHT * 0.49), "radius": SCREEN_WIDTH * 0.01}
    ]

    component_descriptions = {
        "Load and Generation Plot": "Shows the electricity demand of the city (white) and the power generated by the PSH plant (red).",
        "Upper Reservoir": "Stores water that can be released to generate electricity.",
        "Lower Reservoir": "Collects water that has been released from the upper reservoir.",
        "Turbine Feed Pipes": "Carries water from the upper reservoir down to the turbine.",
        "Generator": "Converts mechanical energy from the turbine into electrical energy that can be sent to the grid.",
        "Turbine": "Is turned by the flow of water from the upper reservoir to generate electricity.",
        "Valves": "Controls the flow of water between the reservoirs and through the turbine.",
        "Frequency Converter": "Matches the frequency of the electricity generated by the plant to the grid frequency.",
        "Step-up Transformer": "Increases the voltage of generated electricity so it can be transmitted over long distances through power lines."
    }

    # Text box setup
    text_box_width = SCREEN_WIDTH * 0.75
    text_box_height = SCREEN_HEIGHT * 0.15
    text_box_x = SCREEN_WIDTH * 0.02
    text_box_y = SCREEN_HEIGHT - text_box_height - SCREEN_HEIGHT * 0.02
    text_box_frame = pygame.transform.smoothscale(border_frame, (int(text_box_width), int(text_box_height)))

    # Variables to store the most recently clicked item's name and description
    clicked_name = ""
    clicked_description = ""
    clicked_circle = None  # Track the currently clicked circle

    # Continue button setup
    Continue_width = SCREEN_WIDTH * 0.15
    Continue_height = SCREEN_HEIGHT * 0.06
    Continue_rect = pygame.Rect(SCREEN_WIDTH - Continue_width - SCREEN_WIDTH * 0.02,
                            SCREEN_HEIGHT - Continue_height - SCREEN_HEIGHT * 0.02,
                            Continue_width, Continue_height)
    Continue_frame = pygame.transform.smoothscale(border_frame, (int(Continue_width), int(Continue_height)))
    Continue_green_frame = tint_surface(Continue_frame, (0, 200, 0))
    Continue_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.03))
    Continue_text = Continue_font.render("Continue", True, (255, 255, 255))
    Continue_text_rect = Continue_text.get_rect(center=Continue_rect.center)

    has_clicked = False  # Track if any circle has been clicked
    running = True
    while running:
        screen.blit(static_background_image, (0, 0))
        screen.blit(scaled_border, (border_x, border_y))
        screen.blit(upper_reservoir_image, (left_edge_x, upper_edge_y))
        screen.blit(exploration_directions, (SCREEN_WIDTH / 2 - exploration_directions.get_width() / 2, SCREEN_HEIGHT * 0.02))
        screen.blit(graph_border, (graph_x, graph_y))
        screen.blit(scaled_graph_image, (graph_x, graph_y))

        # Draw the clickable circles with hover and click effects
        mouse_pos = pygame.mouse.get_pos()
        for circle in clickable_circles:
            distance = ((mouse_pos[0] - circle["pos"][0]) ** 2 + (mouse_pos[1] - circle["pos"][1]) ** 2) ** 0.5
            if circle == clicked_circle:  # Click effect
                pygame.draw.circle(screen, (0, 255, 0), circle["pos"], circle["radius"]*1.2)  # Green Fill
            elif distance <= circle["radius"]:  # Hover effect
                pygame.draw.circle(screen, (0, 255, 0), circle["pos"], circle["radius"])  # Semi-transparent fill
            else:
                pygame.draw.circle(screen, (0, 255, 0), circle["pos"], circle["radius"], 2)  # Default outline

        # Draw the text box
        if has_clicked:
            screen.blit(text_box_frame, (text_box_x, text_box_y))
            name_text = name_font.render(f"{clicked_name}", True, (255, 255, 255))
            description_text = description_font.render(f"{clicked_description}", True, (255, 255, 255))
            screen.blit(name_text, (text_box_x + SCREEN_WIDTH * 0.01, text_box_y + SCREEN_HEIGHT * 0.01))
            screen.blit(description_text, (text_box_x + SCREEN_WIDTH * 0.01, text_box_y + SCREEN_HEIGHT * 0.05))

        # Draw Continue button
        screen.blit(Continue_green_frame, Continue_rect)
        screen.blit(Continue_text, Continue_text_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game_data()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for circle in clickable_circles:
                    distance = ((mouse_pos[0] - circle["pos"][0]) ** 2 + (mouse_pos[1] - circle["pos"][1]) ** 2) ** 0.5
                    if distance <= circle["radius"]:
                        clicked_name = circle["name"]
                        clicked_description = component_descriptions[clicked_name]
                        clicked_circle = circle  # Update the clicked circle
                        has_clicked = True
                if Continue_rect.collidepoint(mouse_pos):
                    return  # Continue to the next part
            else:
                clicked_circle = None

        pygame.display.flip()
        clock.tick(60)

def PSH_Controls():
    show_pressed_keys = True
    show_blinking_rect = True
    blink_timer = 0
    blink_interval = 500

    # Continue button setup
    Continue_width = SCREEN_WIDTH * 0.15
    Continue_height = SCREEN_HEIGHT * 0.06
    Continue_rect = pygame.Rect(SCREEN_WIDTH - Continue_width - SCREEN_WIDTH * 0.02,
                            SCREEN_HEIGHT - Continue_height - SCREEN_HEIGHT * 0.02,
                            Continue_width, Continue_height)
    Continue_frame = pygame.transform.smoothscale(border_frame, (int(Continue_width), int(Continue_height)))
    Continue_green_frame = tint_surface(Continue_frame, (0, 200, 0))
    Continue_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.03))
    Continue_text = Continue_font.render("Continue", True, (255, 255, 255))
    Continue_text_rect = Continue_text.get_rect(center=Continue_rect.center)

    caption_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Regular.ttf"), int(SCREEN_HEIGHT * 0.045))
    loading_text = caption_font.render("Loading...", True, (255, 255, 255))

    clock = pygame.time.Clock()
    running = True
    while running:
        blink_timer += clock.get_time()
        if blink_timer >= blink_interval:
            show_pressed_keys = not show_pressed_keys
            show_blinking_rect = not show_blinking_rect
            blink_timer = 0

        draw_controls_page_PSH(screen, show_pressed_keys, show_blinking_rect)
        # Draw Continue button
        screen.blit(Continue_green_frame, Continue_rect)
        screen.blit(Continue_text, Continue_text_rect)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game_data()
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if Continue_rect.collidepoint(event.pos):
                    screen.blit(loading_text, (SCREEN_WIDTH / 2 - loading_text.get_width() / 2, SCREEN_HEIGHT / 2 - loading_text.get_height() / 2))
                    pygame.display.flip()
                    return  # Continue to the next part
        pygame.display.flip()
        clock.tick(60)

def PSH_Level():
    global SCREEN_WIDTH, SCREEN_HEIGHT, border_frame, level_completed, level_scores
    global control_panel, up_active, up_inactive, down_active, down_inactive
    frames = load_psh_frames(NUM_PSH_FRAMES, PSH_PATH_TEMPLATE)
    turbine_frames = load_psh_frames(POWERHOUSE_NUM_FRAMES, POWERHOUSE_PATH_TEMPLATE)
    upper_reservoir_frames = load_upper_reservoir_frames(NUM_PSH_FRAMES, UPPER_RESERVOIR_PATH_TEMPLATE)
    noflow_frames = load_psh_frames(FLOW_CUT_NUM_FRAMES, FLOW_CUT_PATH_TEMPLATE)
    bar_frames = load_bar_frames()
    game_state = reset_PSH()

    turbine_index = 0

    static_background_image = load_image('assets/PSHSequences/PSHStatics/PSHStatics.jpg')
    static_background_image = pygame.transform.scale(static_background_image, (static_background_image.get_width() * SCREEN_WIDTH / 1920, static_background_image.get_height() * SCREEN_HEIGHT / 1080))
    upper_reservoir_image = load_image('assets/PSHSequences/PSHStatics/UpperReservoirStatics.jpg')
    upper_reservoir_image = pygame.transform.scale(upper_reservoir_image, ((upper_reservoir_image.get_width() * SCREEN_WIDTH / 1920)/2.5, (upper_reservoir_image.get_height() * SCREEN_HEIGHT / 1080)/2.5))
    border_frame_image = load_image('assets/IKM_Assets/BorderFrame.png')
    control_panel_image = load_image('assets/IKM_Assets/ControlPanel.png')

    up_active_image = up_active.copy()
    up_inactive_image = up_inactive.copy()
    down_active_image = down_active.copy()
    down_inactive_image = down_inactive.copy()

    blue_arrow_image = load_image("assets/BlueArrow.png")
    blue_arrow_image = pygame.transform.scale(blue_arrow_image, (blue_arrow_image.get_size()[0]*SCREEN_WIDTH*0.000125, blue_arrow_image.get_size()[1]*SCREEN_HEIGHT*0.000111))

    upper_reservoir_frame_index = 100

    # Button positioning
    button_width = up_active_image.get_width() * SCREEN_WIDTH / 1920
    button_height = up_active_image.get_height() * SCREEN_HEIGHT / 1080
    button_x = SCREEN_WIDTH * 0.45
    up_button_y = SCREEN_HEIGHT * 0.83
    down_button_y = SCREEN_HEIGHT * 0.93

    up_active_image = pygame.transform.smoothscale(up_active_image, (int(button_width), int(button_height)))
    up_inactive_image = pygame.transform.smoothscale(up_inactive_image, (int(button_width), int(button_height)))
    down_active_image = pygame.transform.smoothscale(down_active_image, (int(button_width), int(button_height)))
    down_inactive_image = pygame.transform.smoothscale(down_inactive_image, (int(button_width), int(button_height)))

    up_button_rect = pygame.Rect(button_x, up_button_y, button_width, button_height)
    down_button_rect = pygame.Rect(button_x, down_button_y, button_width, button_height)

    # PSH Upper Reservoir Frame Positioning (LEFT)
    upper_edge_y = int(SCREEN_HEIGHT * 0.08)
    left_edge_x = int(SCREEN_WIDTH * 0.01)
    border_width = upper_reservoir_image.get_width()*1.005
    border_height = upper_reservoir_image.get_height()*1.013
    border_x = left_edge_x*0.975
    border_y = upper_edge_y*0.975

    scaled_border = pygame.transform.smoothscale(border_frame_image, (border_width, border_height))

    panel_width = (control_panel_image.get_size()[0] * SCREEN_WIDTH / 1920)/2
    panel_height = (control_panel_image.get_size()[1] * SCREEN_HEIGHT / 1080)/2
    scaled_panel = pygame.transform.smoothscale(control_panel_image, (panel_width, panel_height))
    red_panel = tint_surface(scaled_panel, (255, 0, 0))
    red_panel.set_alpha(127)
    scaled_panel.set_alpha(127)

    panel_font_size = int(panel_height * 0.1)
    panel_font = pygame.font.Font(resource_path("assets/Fonts/Electrolize-Regular.ttf"), panel_font_size)

    label_text = panel_font.render("Upper Reservoir Water Level", True, (255, 255, 255))
    label_x = SCREEN_WIDTH * 0.235
    label_y = SCREEN_HEIGHT * 0.82

    graph_width = (1200*screen.get_size()[0] / 1920)/2.8
    graph_height = (900*screen.get_size()[1] / 1080)/2.8
    graph_x = SCREEN_WIDTH - graph_width - SCREEN_WIDTH * 0.01
    graph_y = int(SCREEN_HEIGHT * 0.1) 
    graph_border = pygame.transform.smoothscale(border_frame_image, (int(graph_width*1.025), int(graph_height*1.025)))

    # Load electricity image
    light_image = load_image("assets/Light.png")
    light_image = pygame.transform.smoothscale(light_image, (light_image.get_size()[0]*0.05*(SCREEN_WIDTH/1280),light_image.get_size()[1]*0.05*(SCREEN_HEIGHT/720)))
    # Define light animation positions
    light_positions = [
        (SCREEN_WIDTH * 0.402, 0),
        (SCREEN_WIDTH * 0.405, SCREEN_HEIGHT * 0.01),
        (SCREEN_WIDTH * 0.41, SCREEN_HEIGHT * 0.02),
        (SCREEN_WIDTH * 0.415, SCREEN_HEIGHT * 0.035),
        (SCREEN_WIDTH * 0.42, SCREEN_HEIGHT * 0.05),
        (SCREEN_WIDTH * 0.425, SCREEN_HEIGHT * 0.0625),
        (SCREEN_WIDTH * 0.43, SCREEN_HEIGHT * 0.075),
        (SCREEN_WIDTH * 0.435, SCREEN_HEIGHT * 0.0875),
        (SCREEN_WIDTH * 0.44, SCREEN_HEIGHT * 0.1),
        (SCREEN_WIDTH * 0.444, SCREEN_HEIGHT * 0.1125),
        (SCREEN_WIDTH * 0.448, SCREEN_HEIGHT * 0.125),
        (SCREEN_WIDTH * 0.453, SCREEN_HEIGHT * 0.1375),
        (SCREEN_WIDTH * 0.458, SCREEN_HEIGHT * 0.15),
        (SCREEN_WIDTH * 0.463, SCREEN_HEIGHT * 0.1625),
        (SCREEN_WIDTH * 0.468, SCREEN_HEIGHT * 0.175),
        (SCREEN_WIDTH * 0.473, SCREEN_HEIGHT * 0.1875),
        (SCREEN_WIDTH * 0.478, SCREEN_HEIGHT * 0.2),
        (SCREEN_WIDTH * 0.483, SCREEN_HEIGHT * 0.2125),
        (SCREEN_WIDTH * 0.488, SCREEN_HEIGHT * 0.225),
        (SCREEN_WIDTH * 0.493, SCREEN_HEIGHT * 0.2375),
        (SCREEN_WIDTH * 0.498, SCREEN_HEIGHT * 0.25),
        (SCREEN_WIDTH * 0.503, SCREEN_HEIGHT * 0.2625),
        (SCREEN_WIDTH * 0.508, SCREEN_HEIGHT * 0.275),
        (SCREEN_WIDTH * 0.513, SCREEN_HEIGHT * 0.2875),
        (SCREEN_WIDTH * 0.519, SCREEN_HEIGHT * 0.3),
        (SCREEN_WIDTH * 0.524, SCREEN_HEIGHT * 0.3125),
        (SCREEN_WIDTH * 0.529, SCREEN_HEIGHT * 0.325),
        (SCREEN_WIDTH * 0.534, SCREEN_HEIGHT * 0.3375),
        (SCREEN_WIDTH * 0.54, SCREEN_HEIGHT * 0.35),
        (SCREEN_WIDTH * 0.545, SCREEN_HEIGHT * 0.3625),
        (SCREEN_WIDTH * 0.551, SCREEN_HEIGHT * 0.375),
        (SCREEN_WIDTH * 0.558, SCREEN_HEIGHT * 0.3875),
        (SCREEN_WIDTH * 0.5655, SCREEN_HEIGHT * 0.4),
        (SCREEN_WIDTH * 0.575, SCREEN_HEIGHT * 0.415),
        (SCREEN_WIDTH * 0.584, SCREEN_HEIGHT * 0.43)
    ]
    light2_positions = [
        (SCREEN_WIDTH * 0.2685, SCREEN_HEIGHT * 0.0001),
        (SCREEN_WIDTH * 0.273, SCREEN_HEIGHT * 0.008),
        (SCREEN_WIDTH * 0.28, SCREEN_HEIGHT * 0.02),
        (SCREEN_WIDTH * 0.315, SCREEN_HEIGHT * 0.035),
        (SCREEN_WIDTH * 0.32, SCREEN_HEIGHT * 0.05),
        (SCREEN_WIDTH * 0.325, SCREEN_HEIGHT * 0.0625),
        (SCREEN_WIDTH * 0.33, SCREEN_HEIGHT * 0.075),
        (SCREEN_WIDTH * 0.335, SCREEN_HEIGHT * 0.0875),
        (SCREEN_WIDTH * 0.34, SCREEN_HEIGHT * 0.1),
        (SCREEN_WIDTH * 0.344, SCREEN_HEIGHT * 0.1125),
        (SCREEN_WIDTH * 0.348, SCREEN_HEIGHT * 0.125),
        (SCREEN_WIDTH * 0.353, SCREEN_HEIGHT * 0.1375),
        (SCREEN_WIDTH * 0.358, SCREEN_HEIGHT * 0.15),
        (SCREEN_WIDTH * 0.363, SCREEN_HEIGHT * 0.1625),
        (SCREEN_WIDTH * 0.368, SCREEN_HEIGHT * 0.175),
        (SCREEN_WIDTH * 0.373, SCREEN_HEIGHT * 0.1875),
        (SCREEN_WIDTH * 0.378, SCREEN_HEIGHT * 0.2),
        (SCREEN_WIDTH * 0.383, SCREEN_HEIGHT * 0.2125),
        (SCREEN_WIDTH * 0.388, SCREEN_HEIGHT * 0.225),
        (SCREEN_WIDTH * 0.393, SCREEN_HEIGHT * 0.2375),
        (SCREEN_WIDTH * 0.398, SCREEN_HEIGHT * 0.25),
        (SCREEN_WIDTH * 0.403, SCREEN_HEIGHT * 0.2625),
        (SCREEN_WIDTH * 0.408, SCREEN_HEIGHT * 0.275),
        (SCREEN_WIDTH * 0.4, SCREEN_HEIGHT * 0.2875),
        (SCREEN_WIDTH * 0.425, SCREEN_HEIGHT * 0.3),
        (SCREEN_WIDTH * 0.43, SCREEN_HEIGHT * 0.3125),
        (SCREEN_WIDTH * 0.437, SCREEN_HEIGHT * 0.325),
        (SCREEN_WIDTH * 0.445, SCREEN_HEIGHT * 0.3375),
        (SCREEN_WIDTH * 0.454, SCREEN_HEIGHT * 0.35),
        (SCREEN_WIDTH * 0.462, SCREEN_HEIGHT * 0.3625),
        (SCREEN_WIDTH * 0.472, SCREEN_HEIGHT * 0.375),
        (SCREEN_WIDTH * 0.482, SCREEN_HEIGHT * 0.3875),
        (SCREEN_WIDTH * 0.492, SCREEN_HEIGHT * 0.4),
        (SCREEN_WIDTH * 0.506, SCREEN_HEIGHT * 0.415),
        (SCREEN_WIDTH * 0.52, SCREEN_HEIGHT * 0.43)
    ]
    light_index = 0
    light2_index = 4
    light3_index = 8
    light4_index = 12
    light5_index = 16

    # Exit button setup (bottom right)
    exit_width = SCREEN_WIDTH * 0.15
    exit_height = SCREEN_HEIGHT * 0.06
    exit_rect = pygame.Rect(SCREEN_WIDTH - exit_width - SCREEN_WIDTH * 0.02,
                            SCREEN_HEIGHT - exit_height - SCREEN_HEIGHT * 0.02,
                            exit_width, exit_height)
    exit_frame = pygame.transform.smoothscale(border_frame, (int(exit_width), int(exit_height)))
    exit_red_frame = tint_surface(exit_frame, (255, 0, 0))
    exit_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.03))
    exit_text = exit_font.render("Exit", True, (255, 255, 255))
    exit_text_rect = exit_text.get_rect(center=exit_rect.center)

    # Skip button setup
    skip_width = SCREEN_WIDTH * 0.15
    skip_height = SCREEN_HEIGHT * 0.06
    skip_rect = pygame.Rect(SCREEN_WIDTH * 0.65,
                            SCREEN_HEIGHT - skip_height - SCREEN_HEIGHT * 0.02,
                            skip_width, skip_height)
    skip_frame = pygame.transform.smoothscale(border_frame, (int(skip_width), int(skip_height)))
    skip_green_frame = tint_surface(skip_frame, (0, 200, 0))
    skip_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), int(SCREEN_HEIGHT * 0.03))
    skip_text = skip_font.render("Skip", True, (255, 255, 255))
    skip_text_rect = skip_text.get_rect(center=skip_rect.center)

    if SCREEN_WIDTH == 960:
        performance_font = pygame.font.Font(resource_path("assets/Fonts/Electrolize-Regular.ttf"), 20)
        complete_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Regular.ttf"), 42)
        warning_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), 20)
    elif SCREEN_WIDTH == 1280:
        performance_font = pygame.font.Font(resource_path("assets/Fonts/Electrolize-Regular.ttf"), 30)
        complete_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Regular.ttf"), 64)
        warning_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), 30)
    elif SCREEN_WIDTH == 1600:
        performance_font = pygame.font.Font(resource_path("assets/Fonts/Electrolize-Regular.ttf"), 40)
        complete_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Regular.ttf"), 84)
        warning_font = pygame.font.Font(resource_path("assets/Fonts/Gudea-Bold.ttf"), 40)

    rotated_blue_arrow_1 = pygame.transform.rotozoom(blue_arrow_image, -55, 1.0)
    rotated_blue_arrow_2 = pygame.transform.rotozoom(blue_arrow_image, 125, 1.0)

    power_index = 0
    display = 60
    clock = pygame.time.Clock()
    running = True

    while running:
        if game_state['level_complete']:
            screen.blit(static_background_image, (0,0))

            # Draw the overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)  # Semi-transparent
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))

            complete_text = "Level complete! Your score was:"
            complete_label = complete_font.render(complete_text, True, (255, 255, 255))
            score_text = f"{int(calculate_score(game_state['score'],factor=1200))}"
            score_label = complete_font.render(score_text, True, (255, 255, 255))

            screen.blit(complete_label, ((SCREEN_WIDTH - complete_label.get_width()) // 2, SCREEN_HEIGHT // 3))
            screen.blit(score_label, ((SCREEN_WIDTH - score_label.get_width()) // 2, SCREEN_HEIGHT // 2))
        else:
            game_state['elapsed_time'] += clock.tick(60) / 1000.0  # Convert milliseconds to seconds
            if game_state['elapsed_time'] >= PSH_LEVEL_DURATION:
                game_state['level_complete'] = True
            screen.blit(static_background_image, (0, 0))

            # Update upper reservoir frame index scaled by release %
            release_factor = abs(game_state['release']) / 50.0
            previous_upper_reservoir_index = upper_reservoir_frame_index

            if game_state['release'] > 0 and upper_reservoir_frame_index < NUM_PSH_FRAMES - 1:
                upper_reservoir_frame_index += release_factor
                if upper_reservoir_frame_index > NUM_PSH_FRAMES - 1:
                    upper_reservoir_frame_index = NUM_PSH_FRAMES - 1
            elif game_state['release'] < 0 and upper_reservoir_frame_index > 0:
                upper_reservoir_frame_index -= release_factor
                if upper_reservoir_frame_index < 0:
                    upper_reservoir_frame_index = 0

            # Convert to int for indexing frames
            upper_reservoir_frame_index_int = int(upper_reservoir_frame_index)
            # Convert to int for index comparison
            current_index_int = int(upper_reservoir_frame_index)
            previous_index_int = int(previous_upper_reservoir_index)

            if game_state['release'] > 0:
                turbine_index += int(release_factor*5)
                turbine_index = turbine_index % 46
            elif game_state['release'] < 0:
                turbine_index -= int(release_factor*5)
                if turbine_index < 0:
                        turbine_index = 45


            # If we just overflowed the reservoir
            if previous_index_int < NUM_PSH_FRAMES - 1 and current_index_int >= NUM_PSH_FRAMES - 1:
                game_state['release'] = 0  # Stop the flow
            # If we just emptied the reservoir
            elif previous_index_int > 0 and current_index_int <= 0:
                game_state['release'] = 0  # Stop the flow

            if current_index_int >= NUM_PSH_FRAMES - 1:
                allow_release = False
                allow_pump = True
            elif current_index_int <= 0:
                allow_release = True
                allow_pump = False
            else:
                allow_release = True
                allow_pump = True

            
            #light animation
            if game_state['release'] != 0:
                    if game_state['release'] < 0:
                        light_index = (light_index + 1) % len(light_positions)
                        light2_index = (light2_index + 1) % len(light_positions)
                        light3_index = (light3_index + 1) % len(light_positions)
                        light4_index = (light4_index + 1) % len(light_positions)
                        light5_index = (light5_index + 1) % len(light_positions)
                        screen.blit(light_image, light_positions[light_index])
                        screen.blit(light_image, light_positions[light2_index])
                        screen.blit(light_image, light_positions[light3_index])
                        screen.blit(light_image, light_positions[light4_index])
                        screen.blit(light_image, light_positions[light5_index])
                        screen.blit(light_image, light2_positions[light_index])
                        screen.blit(light_image, light2_positions[light2_index])
                        screen.blit(light_image, light2_positions[light3_index])
                        screen.blit(light_image, light2_positions[light4_index])
                        screen.blit(light_image, light2_positions[light5_index])
                    else:
                        light_index = (light_index - 1) % len(light_positions)
                        light2_index = (light2_index - 1) % len(light_positions)
                        light3_index = (light3_index - 1) % len(light_positions)
                        light4_index = (light4_index - 1) % len(light_positions)
                        light5_index = (light5_index - 1) % len(light_positions)
                        screen.blit(light_image, light_positions[light_index])
                        screen.blit(light_image, light_positions[light2_index])
                        screen.blit(light_image, light_positions[light3_index])
                        screen.blit(light_image, light_positions[light4_index])
                        screen.blit(light_image, light_positions[light5_index])
                        screen.blit(light_image, light2_positions[light_index])
                        screen.blit(light_image, light2_positions[light2_index])
                        screen.blit(light_image, light2_positions[light3_index])
                        screen.blit(light_image, light2_positions[light4_index])
                        screen.blit(light_image, light2_positions[light5_index])
            else:
                light_index = 0
                light2_index = 4
                light3_index = 8
                light4_index = 12
                light5_index = 16

            screen.blit(turbine_frames[turbine_index], (SCREEN_WIDTH*0.3855, SCREEN_HEIGHT*0.5389))
            screen.blit(frames[upper_reservoir_frame_index_int], (SCREEN_WIDTH*0.5925, SCREEN_HEIGHT*0.431))
            if game_state['release'] == 0:
                    screen.blit(noflow_frames[int((NUM_PSH_FRAMES-upper_reservoir_frame_index_int)*0.73)], (SCREEN_WIDTH*0.5925, SCREEN_HEIGHT*0.431))
            screen.blit(scaled_border, (border_x, border_y))
            screen.blit(upper_reservoir_image, (left_edge_x, upper_edge_y))
            screen.blit(upper_reservoir_frames[upper_reservoir_frame_index_int], (left_edge_x, upper_edge_y+SCREEN_HEIGHT*0.09))
            if current_index_int >= NUM_PSH_FRAMES - 1 or current_index_int <= 0:
                screen.blit(red_panel, (0, SCREEN_HEIGHT * 0.8))
                screen.blit(warning_font.render("Warning: Reservoir below pump/turbine intake!", True, (255, 255, 255)), (SCREEN_WIDTH * 0.02, SCREEN_HEIGHT * 0.75))
            else:
                screen.blit(scaled_panel, (0, SCREEN_HEIGHT * 0.8))

            # Text displays
            if game_state['release'] > 0:
                power_generated = 0.65 * game_state['release']
                game_state['power_data'].append(power_generated)
                release_status = f"Current Release Rate: {int(26.67*game_state['release'])} cfs"
            elif game_state['release'] < 0:
                power_generated = 0
                excess_power = 0.65 * game_state['release']
                game_state['power_data'].append(excess_power)
                release_status = f"Current Pump Rate: {int(abs(26.67*game_state['release']))} cfs"
            else:
                power_generated = 0
                game_state['power_data'].append(power_generated)
                release_status = f"No Current Flow"
            
            if game_state['release'] >= 0:
                power_status = f"Power Generated: {int(0.025*26.67*power_generated/0.65)} MW"
            else:
                power_status = f"Power Consumed: {int(abs(0.025*26.67*excess_power/0.65))} MW"

            graph_filename = update_psh_graph(game_state['x_start'], game_state['x_end'], game_state['power_data'], display)
            graph_image = load_image(graph_filename)

            display = display % (len(LOAD_CURVE)-1)
            display += 1
                

            scaled_graph_image = pygame.transform.scale(graph_image, (graph_width, graph_height))
            screen.blit(graph_border, (graph_x, graph_y))
            screen.blit(scaled_graph_image, (graph_x, graph_y))

            if len(game_state['power_data']) > 10:
                game_state['power_data'] = game_state['power_data'][-10:]

            game_state['x_start'] += 0.05
            game_state['x_end'] += 0.05

            screen.blit(panel_font.render(release_status, True, (255, 255, 255)), (SCREEN_WIDTH * 0.02, SCREEN_HEIGHT * 0.85))
            screen.blit(panel_font.render(power_status, True, (255, 255, 255)), (SCREEN_WIDTH * 0.02, SCREEN_HEIGHT * 0.90))

            # Upper Reservoir Water Level bar
            bar_index = int((300 - upper_reservoir_frame_index_int) * (1/3))
            bar_index = min(100,bar_index)
            bar_image = bar_frames[bar_index]
            screen.blit(bar_image, (int(SCREEN_WIDTH * 0.31), int(SCREEN_HEIGHT * 0.83)))

            # Label
            screen.blit(label_text, (label_x, label_y))

            # Buttons
            up_image = up_active_image if game_state['release'] < MAX_PSH_RELEASE and allow_release else up_inactive_image
            down_image = down_active_image if game_state['release'] > MIN_PSH_RELEASE and allow_pump else down_inactive_image

            screen.blit(up_image, up_button_rect.topleft)
            screen.blit(down_image, down_button_rect.topleft)

            # Get target load value from sine wave at this point in time
            target_load = (PSH_LOAD[(display+10)%len(PSH_LOAD)]/6)-20

            # Actual power is power_generated or pumping (negative power)
            actual_power = 0.65 * game_state['release']

            # Calculate imbalance and store
            imbalance = abs(actual_power - target_load)
            game_state['score'] += imbalance
            power_index += 1

            avg_imbalance = game_state['score'] / power_index
            imbalance_text = f"Average Power Imbalance: {(1.026*avg_imbalance):.2f} MW"
            text_surface = performance_font.render(imbalance_text, True, (255, 255, 255))
            screen.blit(text_surface, (SCREEN_WIDTH * 0.01, SCREEN_HEIGHT * 0.02))

            screen.blit(performance_font.render(f"Time Remaining: {PSH_LEVEL_DURATION-int(game_state['elapsed_time'])} sec", True, (255, 255, 255)), (SCREEN_WIDTH * 0.5, SCREEN_HEIGHT * 0.02))

            release_alpha = int(min(255, max(0, abs(release_factor/3) * 255)))

            # Determine rotation angle based on release factor
            if game_state['release'] >= 0:
                rotated_blue_arrow = rotated_blue_arrow_1
            elif game_state['release'] < 0:
                rotated_blue_arrow = rotated_blue_arrow_2

            # Set alpha transparency based on release factor
            rotated_blue_arrow.set_alpha(release_alpha)

            # Draw the arrow on screen
            screen.blit(rotated_blue_arrow, (SCREEN_WIDTH*0.18,SCREEN_HEIGHT*0.5))

            # Draw exit button
            screen.blit(exit_red_frame, exit_rect)
            screen.blit(exit_text, exit_text_rect)

            # Draw skip button
            screen.blit(skip_green_frame, skip_rect)
            screen.blit(skip_text, skip_text_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game_data()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if game_state['level_complete']:
                    calc_score = calculate_score(game_state['score'], factor=1200)
                    if level_scores[3] < calc_score:
                        level_scores[3] = calc_score
                    level_completed[3] = True
                    save_game_data()
                    return
                if up_button_rect.collidepoint(event.pos):
                    if game_state['release'] < MAX_PSH_RELEASE and allow_release:
                        game_state['release'] += RELEASE_STEP
                elif down_button_rect.collidepoint(event.pos):
                    if game_state['release'] > MIN_PSH_RELEASE and allow_pump:
                        game_state['release'] -= RELEASE_STEP
                elif exit_rect.collidepoint(event.pos):
                    return  # Exit this level
                elif skip_rect.collidepoint(event.pos):
                    level_completed[3] = True
                    save_game_data()
                    return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    if game_state['release'] < MAX_PSH_RELEASE and allow_release:
                        game_state['release'] += RELEASE_STEP
                elif event.key == pygame.K_DOWN:
                    if game_state['release'] > MIN_PSH_RELEASE and allow_pump:
                        game_state['release'] -= RELEASE_STEP
            elif event.type == pygame.MOUSEWHEEL:
                if event.y < 0:
                    if game_state['release'] > MIN_PSH_RELEASE and allow_pump:
                        game_state['release'] -= RELEASE_STEP
                elif event.y > 0:
                    if game_state['release'] < MAX_PSH_RELEASE and allow_release:
                        game_state['release'] += RELEASE_STEP
                    
        pygame.display.flip()

def Level4_intro():
    global selected_character, SCREEN_WIDTH, SCREEN_HEIGHT

    scene1_image = load_image(f"assets/Transitions/FishHealth/{selected_character}_Fish.jpg")
    # Scale scenes
    scene1_image = pygame.transform.smoothscale(scene1_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    # --- Dialogue Data ---
    dialogue_scene1 = [
        ("Tom",
         "Unregulated hydropower operations can have a significant negative impact on local aquatic "
         "ecosystems, affecting fish populations. We need to follow some operational guidelines to "
         "minimize these impacts."),
         ("Tom", "I'm going to have you manage a release schedule for the day while learning about "
         "the various constraining factors we need to consider while operating a hydropower plant. "),
         ("Tom",
          "Hydropower operators limit the release rate to avoid flooding downstream areas and to protect habitats that depend on stable river flows. "
          "The ramping rate needs to be controlled so we don't shock aquatic ecosystems or cause sudden erosion — rivers don't like surprises. "),
         ("Tom",
          "Operators also keep an eye on daily volumes; "
          "over-releasing can drain the reservoir faster than planned and put us out of compliance with water agreements."),
         ("Tom", "Your task is to find the best hydropower revenue by changing the hourly releases, you can click and drag the bars on the screen "
         "to adjust. The curve on your monitor represents the price of energy at each hour, and is your guide to maximizing revenue. "),
         ("Tom", "Ensure all environmental rules are met: daily target, minimum release, "
         "maximum ramp up, and maximum ramp down. To complete the level, you must obtain "
         "both a feasible solution and at least a 90% optimality, then check your solution.")
    ]
    scenes = [(scene1_image,dialogue_scene1)]
    run_dialogue(scenes)

def Environment_Level():
    game = reset_env()
    game['screen'] = pygame.display.set_mode((game['window_width'], game['window_height']))
    game['clock'] =  pygame.time.Clock()
    while game['running']:
        update_layout(game) 
        handle_events_env(game)
        update_metrics(game)
        game['screen'].fill(get_bg_color(game))
        draw_buttons(game)
        draw_bar_graph(game)
        draw_total_bars(game)
        draw_timer(game)
        draw_message(game)
        pygame.display.flip()
        game['clock'].tick(30)

# --- MAIN PROGRAM ---
has_save_file = load_game_data()
opening_screen(background2, argonne_logo, nrel_logo, doe_logo)
del argonne_logo
del nrel_logo
del doe_logo
main_menu()