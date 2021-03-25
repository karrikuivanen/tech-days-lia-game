import asyncio
import random

from lia.enums import *
from lia.api import *
from lia import constants
from lia import math_util
from lia.bot import Bot
from lia.networking_client import connect


YELL = ["DIE!", "VICTORY IS OURS!", "I AM YOUR FATHER!"]


def spawn(state, api):
    if state["resources"] >= constants.WARRIOR_PRICE:
        api.spawn_unit(UnitType.WARRIOR)


def act(state, api, unit):
    move(state, api, unit)
    shoot_enemy(state, api, unit)


def move(state, api, unit):
    unit["advancing"] = True
    api.say_something(unit["id"], random.choice(YELL))
    # Generate new x and y until you get a position on the map
    # where there is no obstacle
    move_linear(api, unit)


def move_linear(api, unit):
    x, y = get_enemy_spawn_point()
    api.navigation_start(unit["id"], x, y)


def shoot_enemy(state, api, unit):
    if len(unit["opponentsInView"]) > 0:
        api.shoot(unit["id"])
        api.say_something(unit["id"], random.choice(YELL))


def get_starting_pos():
    if constants.SPAWN_POINT.y > constants.MAP_HEIGHT / 2:
        return "TOP"
    else:
        return "BOTTOM"


def get_enemy_spawn_point():
    x = constants.MAP_WIDTH - constants.SPAWN_POINT.x
    y = constants.MAP_HEIGHT - constants.SPAWN_POINT.y
    return (x, y)
