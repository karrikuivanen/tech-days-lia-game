import asyncio
import random

from lia.enums import *
from lia.api import *
from lia import constants
from lia import math_util
from lia.bot import Bot
from lia.networking_client import connect

def act(state, api, unit):
    move(state, api, unit)
    shoot_enemy(state, api, unit)
    
def move(state, api, unit):
    # If the unit is not going anywhere, we send it
    # to a random valid location on the map.
    if len(unit["navigationPath"]) == 0:
        # Generate new x and y until you get a position on the map
        # where there is no obstacle.
            x,y = get_enemy_spawn_point()

            api.navigation_start(unit["id"], x, y)

def shoot_enemy(state, api, unit):
    if len(unit["opponentsInView"]) > 0:
        api.shoot(unit["id"])
        api.say_something(unit["id"], "I see you!")

def get_enemy_spawn_point():
    x = constants.MAP_WIDTH - constants.SPAWN_POINT.x
    y = constants.MAP_HEIGHT - constants.SPAWN_POINT.y
    return (x, y)
