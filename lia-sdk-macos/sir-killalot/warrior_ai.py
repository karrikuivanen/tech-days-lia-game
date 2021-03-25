import asyncio
import random

from lia.enums import *
from lia.api import *
from lia import constants
from lia import math_util
from lia.bot import Bot
from lia.networking_client import connect


class Tactic:
    LINEAR = "LINEAR"
    FLANK_RIGHT = "FLANK_RIGHT"


YELL = ["DIE!", "VICTORY IS OURS!", "I AM YOUR FATHER!"]


def spawn(state, api):
    if state["resources"] >= constants.WARRIOR_PRICE:
        api.spawn_unit(UnitType.WARRIOR)
        state["units"][-1]["tactic"] = Tactic.FLANK_RIGHT


def act(state, api, unit):
    move(state, api, unit)
    shoot_enemy(state, api, unit)


def move(state, api, unit):
    # If the unit is not going anywhere, we send it
    # to a random valid location on the map.
    if len(unit["navigationPath"]) == 0:
        api.say_something(unit["id"], random.choice(YELL))
        # Generate new x and y until you get a position on the map
        # where there is no obstacle.
        if not "tactic" in unit:
            unit["tactic"] = random.choice([Tactic.LINEAR, Tactic.FLANK_RIGHT])
        if unit["tactic"] == Tactic.FLANK_RIGHT:
            move_flank(api, unit)
        elif unit["tactic"] == Tactic.LINEAR:
            move_linear(api, unit)


def move_flank(api, unit):
    if get_starting_pos() == "BOTTOM":
        if unit["x"] >= constants.MAP_WIDTH / 2:
            api.navigation_stop(unit["id"])
        else:
            api.navigation_start(unit["id"], constants.MAP_WIDTH, unit["y"])
    else:
        if unit["x"] < constants.MAP_WIDTH / 2:
            api.navigation_stop(unit["id"])
        else:
            api.navigation_start(unit["id"], 0, unit["y"])


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
