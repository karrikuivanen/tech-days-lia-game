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


def _scan_opposite_corner(api, unit, starting_position):
    TURN_RIGHT_ZONE = {"min": 90, "max": 100}
    TURN_LEFT_ZONE_A = {"min": 350, "max": 360}
    TURN_LEFT_ZONE_B = {"min": 0, "max": 10}
    # api.say_something(unit["id"], str(unit["orientationAngle"]))
    if starting_position == "BOTTOM":
        if unit_in_zone(unit, TURN_RIGHT_ZONE):
            # api.say_something(unit["id"], "TURN RIGHT")
            api.set_rotation(unit["id"], "RIGHT")
        elif unit_in_zone(unit, TURN_LEFT_ZONE_A) or unit_in_zone(unit, TURN_LEFT_ZONE_B):
            # api.say_something(unit["id"], "TURN LEFT")
            api.set_rotation(unit["id"], "LEFT")
        elif (
            unit["orientationAngle"] > TURN_RIGHT_ZONE["min"]
            # and unit["orientationAngle"] < TURN_LEFT_ZONE_A["min"]
        ):
            # api.say_something(unit["id"], "???")
            api.set_rotation(unit["id"], "RIGHT")
        elif unit["rotation"] == "NONE":
            api.say_something(unit["id"], "Mitä perkelettä")
            api.set_rotation(unit["id"], "RIGHT")
        # else:
        #     api.say_something(unit["id"], str(unit["orientationAngle"]))
        #     api.set_rotation(unit["id"], "LEFT")


def get_defender_state(unit):
    if unit["id"] not in DEFENDERS_STATE:
        return None
    return DEFENDERS_STATE[unit["id"]]


def set_defender_state(unit, state):
    DEFENDERS_STATE[unit["id"]] = state


def scan_opposite_corner(api, unit, starting_position):
    TURN_RIGHT_ZONE = {"min": 45, "max": 100}
    TURN_LEFT_ZONE_A = {"min": 350, "max": 360}
    TURN_LEFT_ZONE_B = {"min": 0, "max": 10}
    api.say_something(unit["id"], get_defender_state(unit))
    if (not get_defender_state(unit)):
        # api.say_something(unit["id"], "Mitä perkelettä")
        set_defender_state(unit, "INITIALIZING")
    if (get_defender_state(unit) == "INITIALIZING"):
        if unit["orientationAngle"] > TURN_RIGHT_ZONE["min"]:
            api.set_rotation(unit["id"], "RIGHT")
        else:
            api.set_rotation(unit["id"], "RIGHT")
            # api.say_something(unit["id"], "ELSE")
            set_defender_state(unit, "TURNING_RIGHT")
    elif (get_defender_state(unit) == "TURNING_RIGHT" and unit["orientationAngle"] <= 5):
        # api.say_something(unit["id"], "Left")
        api.set_rotation(unit["id"], "LEFT")
        set_defender_state(unit, "TURNING_LEFT")
    elif (get_defender_state(unit) == "TURNING_LEFT" and unit["orientationAngle"] >= 85):
        # api.say_something(unit["id"], "Right")
        api.set_rotation(unit["id"], "RIGHT")
        set_defender_state(unit, "TURNING_RIGHT")


def move(state, api, unit, defender=False):
    if unit["id"] in DEFENDING_WARRIORS:
        if get_starting_pos() == "BOTTOM":
            api.navigation_start(unit["id"], 8, 8)

            if math_util.distance(unit["x"], unit["y"], 8, 8) <= 2:
                api.navigation_stop(unit["id"])
                scan_opposite_corner(api, unit, get_starting_pos())
        else:
            api.navigation_start(
                unit["id"], constants.MAP_WIDTH - 2, constants.MAP_HEIGHT - 2
            )

            if (
                math_util.distance(
                    unit["x"],
                    unit["y"],
                    constants.MAP_WIDTH - 2,
                    constants.MAP_HEIGHT - 2,
                )
                <= 2
            ):
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
