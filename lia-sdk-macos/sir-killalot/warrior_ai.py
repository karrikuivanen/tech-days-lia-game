import asyncio
import random

from lia.math_util import *
from lia.enums import *
from lia import constants
from lia import math_util
from lia.bot import Bot
from lia.networking_client import connect

TARGETING_THRESHOLD = 1
TARGET_SQUARE = {"x": 40, "y": 80}
SAFETY_MARGIN = 10
YELL = ["DIE!", "VICTORY IS OURS!", "I AM YOUR FATHER!"]
MOVING_UNITS = set()


def spawn(state, api):
    if state["resources"] >= constants.WARRIOR_PRICE:
        api.spawn_unit(UnitType.WARRIOR)


def act(state, api, unit):
    move(state, api, unit)
    shoot_enemy(state, api, unit)


def move(state, api, unit, defender=False):
    if defender:
        # TODO: move to home square
    else:
        if unit["speed"] == "NONE" and unit["rotation"] == "NONE":
            api.set_rotation(unit["id"], random.choice(["LEFT", "RIGHT"]))
        if not unit["id"] in MOVING_UNITS:
            MOVING_UNITS.add(unit["id"])
            api.say_something(unit["id"], random.choice(YELL))
            move_into_position(api, unit)


def calculate_target():
    starting_pos = get_starting_pos()
    if starting_pos == "TOP":
        x = random.randint(SAFETY_MARGIN, TARGET_SQUARE["x"])
        y = random.randint(SAFETY_MARGIN, TARGET_SQUARE["y"])
        if constants.MAP[x][y] is False:
            return x, y
        return calculate_target()
    else:
        x = random.randint(
            constants.MAP_WIDTH - TARGET_SQUARE["x"],
            constants.MAP_WIDTH - SAFETY_MARGIN,
        )
        y = random.randint(
            constants.MAP_HEIGHT - TARGET_SQUARE["y"],
            constants.MAP_HEIGHT - SAFETY_MARGIN,
        )
        if constants.MAP[x][y] is False:
            return x, y
        return calculate_target()


def move_into_position(api, unit):
    x, y = calculate_target()
    api.navigation_start(unit["id"], x, y)


def shoot_at_enemy(api, this_unit, enemy_unit):
    angle = angle_between_unit_and_point(this_unit, enemy_unit["x"], enemy_unit["y"])
    if angle < TARGETING_THRESHOLD and angle > -TARGETING_THRESHOLD:
        api.set_rotation(this_unit["id"], "NONE")
        api.shoot(this_unit["id"])
    if angle > 0:
        api.set_rotation(this_unit["id"], "LEFT")
    elif angle < 0:
        api.set_rotation(this_unit["id"], "RIGHT")


def shoot_enemy(state, api, unit):
    if len(unit["opponentsInView"]) > 0:
        api.navigation_stop(unit["id"])
        target_enemy = random.choice(unit["opponentsInView"])
        shoot_at_enemy(api, unit, target_enemy)


def get_nearby_enemies(unit):
    MAX_DISTANCE = constants.VIEWING_AREA_LENGTH
    return list(
        filter(
            lambda enemy: distance(unit["x"], unit["y"], enemy["x"], enemy["y"])
            < MAX_DISTANCE,
            unit["opponentsInView"],
        )
    )


def get_starting_pos():
    if constants.SPAWN_POINT.y > constants.MAP_HEIGHT / 2:
        return "TOP"
    else:
        return "BOTTOM"


def get_enemy_spawn_point():
    x = constants.MAP_WIDTH - constants.SPAWN_POINT.x
    y = constants.MAP_HEIGHT - constants.SPAWN_POINT.y
    return (x, y)
