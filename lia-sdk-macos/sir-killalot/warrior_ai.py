import asyncio
import random
from game_globals import *

from lia.math_util import *
from lia.enums import *
from lia import constants
from lia import math_util
from lia.bot import Bot
from lia.networking_client import connect

TARGETING_THRESHOLD = 1
TARGET_SQUARE = {"x": 40, "y": 80}
SAFETY_MARGIN = 10
YELL = [
    "DIE!",
    "VICTORY IS OURS!",
    "I AM YOUR FATHER!",
    "FUBAR",
    "RUTABAGA",
    ":ruuskanen:",
]
MOVING_UNITS = set()


def spawn(state, api):
    if state["resources"] >= constants.WARRIOR_PRICE:
        api.spawn_unit(UnitType.WARRIOR)


def act(state, api, unit):
    move(state, api, unit)
    shoot_enemy(state, api, unit)


def _scan_opposite_corner(api, unit, starting_position):
    TURN_RIGHT_ZONE = {"min": 90, "max": 100}
    TURN_LEFT_ZONE = {"min": 350, "max": 359}
    if starting_position == "BOTTOM":
        if (
            unit["orientationAngle"] > TURN_RIGHT_ZONE["min"]
            and unit["orientationAngle"] < TURN_RIGHT_ZONE["max"]
        ):
            api.set_rotation(unit["id"], "RIGHT")
        if (
            unit["orientationAngle"] > TURN_LEFT_ZONE["min"]
            and unit["orientationAngle"] < TURN_LEFT_ZONE["max"]
        ):
            api.set_rotation(unit["id"], "LEFT")
        if (
            unit["orientationAngle"] > TURN_RIGHT_ZONE["max"]
            and unit["orientationAngle"] < TURN_LEFT_ZONE["min"]
        ):
            api.set_rotation(unit["id"], "LEFT")


def scan_opposite_corner(api, unit, starting_position):
    api.set_rotation(unit["id"], "LEFT")


def move(state, api, unit, defender=False):
    if unit["id"] in DEFENDING_WARRIORS:
        if get_starting_pos() == "BOTTOM":
            api.navigation_start(unit["id"], 2, 2)

            if math_util.distance(unit["x"], unit["y"], 2, 2) <= 2:
                api.navigation_stop(unit["id"])
                scan_opposite_corner(api, unit, get_starting_pos())
        else:
            api.navigation_start(
                unit["id"], constants.MAP_WIDTH - 2, constants.MAP_HEIGHT - 2
            )
    else:
        if unit["speed"] == "NONE" and unit["rotation"] == "NONE":
            api.set_rotation(unit["id"], random.choice(["LEFT", "RIGHT"]))
        if not unit["id"] in MOVING_UNITS:
            MOVING_UNITS.add(unit["id"])
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
