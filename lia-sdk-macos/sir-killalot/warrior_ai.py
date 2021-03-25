from lia.enums import *
from lia.api import *
from lia import constants
from lia import math_util
from lia.bot import Bot
from lia.networking_client import connect

def move():
    # If the unit is not going anywhere, we send it
    # to a random valid location on the map.
    if len(unit["navigationPath"]) == 0:

        # Generate new x and y until you get a position on the map
        # where there is no obstacle.
        while True:
            x = random.randint(0, constants.MAP_WIDTH - 1)
            y = random.randint(0, constants.MAP_HEIGHT - 1)

            # If map[x][y] equals false it means that at (x,y) there is no obstacle.
            if constants.MAP[x][y] is False:
                # Send the unit to (x, y)
                api.navigation_start(unit["id"], x, y)
                break
