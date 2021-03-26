import asyncio
import random
from game_globals import *
from lia.enums import *
from lia.api import *
from lia import constants
from lia import math_util
from lia.bot import Bot
from lia.networking_client import connect

from warrior_ai import act as act_warrior, spawn as spawn_warrior
from worker_ai import act as act_worker, spawn as spawn_worker

MIN_WORKERS = 3
MAX_WORKERS = 10
WARRIORS_IN_HOME = set()

HOME_SQUARE = {"x": 10, "y": 10}


def get_starting_pos():
    if constants.SPAWN_POINT.y > constants.MAP_HEIGHT / 2:
        return "TOP"
    else:
        return "BOTTOM"


def unit_in_home(api, unit):
    if get_starting_pos() == "BOTTOM":
        return unit["x"] < HOME_SQUARE["x"] and unit["y"] < HOME_SQUARE["y"]
    else:
        return (
            unit["x"] > constants.MAP_WIDTH - HOME_SQUARE["x"]
            and unit["y"] > constants.MAP_HEIGHT - HOME_SQUARE["y"]
        )


def assign_warrior_into_home(api, warrior_unit):
    if unit_in_home(api, warrior_unit):
        WARRIORS_IN_HOME.add(warrior_unit["id"])


def get_unit_count_by_type(state, unit_type):
    return len(list(filter(lambda unit: unit["type"] == unit_type, state["units"])))


# Initial implementation keeps picking random locations on the map
# and sending units there. Worker units collect resources if they
# see them while warrior units shoot if they see opponents.
class MyBot(Bot):

    # This method is called 10 times per game second and holds current
    # game state. Use Api object to call actions on your units.
    # - GameState reference: https://docs.liagame.com/api/#gamestate
    # - Api reference:       https://docs.liagame.com/api/#api-object
    def update(self, state, api):
        WARRIORS_IN_HOME.clear()
        worker_count = get_unit_count_by_type(state, UnitType.WORKER)

        if worker_count < MIN_WORKERS:
            spawn_worker(state, api)
        elif (
            worker_count < MAX_WORKERS and state["resources"] >= constants.WARRIOR_PRICE
        ):
            random.choice([spawn_worker, spawn_warrior])(state, api)
        else:
            spawn_warrior(state, api)

        # We iterate through all of our units that are still alive.
        for unit in state["units"]:
            # If the unit is a worker and it sees at least one resource
            # then make it go to the first resource to collect it.
            if unit["type"] == UnitType.WORKER:
                act_worker(state, api, unit)

            # If the unit is a warrior and it sees an opponent then make it shoot.
            if unit["type"] == UnitType.WARRIOR:
                assign_warrior_into_home(api, unit)
                act_warrior(state, api, unit)
        defend_home(state)


def defend_home(state):
    if len(WARRIORS_IN_HOME) == 0:
        closest_warrior = (None, 10000000000000)
        for unit in state["units"]:
            if unit["type"] == UnitType.WARRIOR:
                warrior_distance = math_util.distance(
                    unit["x"],
                    unit["y"],
                    constants.SPAWN_POINT.x,
                    constants.SPAWN_POINT.y,
                )
                if warrior_distance < closest_warrior[1]:
                    closest_warrior = (unit["id"], warrior_distance)

        DEFENDING_WARRIORS.add(closest_warrior[0])


# Connects your bot to Lia game engine, don't change it.
if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(connect(MyBot()))
