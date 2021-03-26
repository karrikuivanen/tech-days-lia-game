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
    ":ruuskanen:",
    ":ruuskanen:",
]
MOVING_UNITS = set()
DEFENDERS_STATE = {}


def spawn(state, api):
    if state["resources"] >= constants.WARRIOR_PRICE:
        api.spawn_unit(UnitType.WARRIOR)


def act(state, api, unit):
    move(state, api, unit)
    shoot_enemy(state, api, unit)


def unit_in_zone(unit, zone):
    return (
        unit["orientationAngle"] >= zone["min"]
        and unit["orientationAngle"] <= zone["max"]
    )


def get_defender_state(unit):
    if unit["id"] not in DEFENDERS_STATE:
        return None
    return DEFENDERS_STATE[unit["id"]]


def set_defender_state(unit, state):
    DEFENDERS_STATE[unit["id"]] = state


def get_middle_zone():
    if get_starting_pos() == "BOTTOM":
        return {"min": 43, "max": 48}
    else:
        return {"min": 223, "max": 228}


def get_limit_angles():
    if get_starting_pos() == "BOTTOM":
        return (15, 75)
    else:
        return (195, 255)


def get_home_position(unit_id, state, x, y):
    distance = 5 if get_starting_pos() == "BOTTOM" else -5
    grow = list(DEFENDING_WARRIORS.keys()).index(unit_id) % 2 == 0
    if (x, y) not in DEFENDING_WARRIORS.values():
        return (x, y)
    else:
        return get_home_position(
            unit_id,
            state,
            x + distance if grow else x,
            y + distance if not grow else y
        )


def scan_opposite_corner(api, unit, starting_position):
    MIDDLE_ZONE = get_middle_zone()
    left_angle, right_angle = get_limit_angles()
    if not get_defender_state(unit):
        api.say_something(unit["id"], "Mitä perkelettä")
        set_defender_state(unit, "INITIALIZING")
    if get_defender_state(unit) == "INITIALIZING":
        api.set_rotation(
            unit["id"], "RIGHT" if get_starting_pos() == "BOTTOM" else "LEFT"
        )
        if (
            unit["orientationAngle"] >= MIDDLE_ZONE["min"]
            and unit["orientationAngle"] <= MIDDLE_ZONE["max"]
        ):
            set_defender_state(unit, "TURNING_RIGHT")
    if get_defender_state(unit) == "TURNING_RIGHT":
        api.set_rotation(unit["id"], "RIGHT")
        if unit["orientationAngle"] <= left_angle:
            set_defender_state(unit, "TURNING_LEFT")
    if get_defender_state(unit) == "TURNING_LEFT":
        api.set_rotation(unit["id"], "LEFT")
        if unit["orientationAngle"] >= right_angle:
            set_defender_state(unit, "TURNING_RIGHT")


def move(state, api, unit, defender=False):
    if unit["id"] in DEFENDING_WARRIORS:
        if not DEFENDING_WARRIORS[unit["id"]]:
            DEFENDING_WARRIORS[unit["id"]] = get_home_position(
                unit["id"],
                state,
                1 if get_starting_pos() == "BOTTOM" else constants.MAP_WIDTH - 1,
                1 if get_starting_pos() == "BOTTOM" else constants.MAP_HEIGHT - 1,
            )
        home_x, home_y = DEFENDING_WARRIORS[unit["id"]]
        api.navigation_start(unit["id"], home_x, home_y)

        if math_util.distance(unit["x"], unit["y"], home_x, home_y) <= 2:
            api.navigation_stop(unit["id"])
            scan_opposite_corner(api, unit, get_starting_pos())

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
    api.say_something(this_unit["id"], random.choice(YELL))
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
