import asyncio
import random

from lia.enums import *
from lia.api import *
from lia import constants
from lia import math_util
from lia.bot import Bot
from lia.networking_client import connect

from warrior_ai import act as act_warrior, spawn as spawn_warrior
from worker_ai import act as act_worker


# Initial implementation keeps picking random locations on the map
# and sending units there. Worker units collect resources if they
# see them while warrior units shoot if they see opponents.
class MyBot(Bot):

    # This method is called 10 times per game second and holds current
    # game state. Use Api object to call actions on your units.
    # - GameState reference: https://docs.liagame.com/api/#gamestate
    # - Api reference:       https://docs.liagame.com/api/#api-object
    def update(self, state, api):

        # If you have enough resources to spawn a new warrior unit then spawn it.
        if state["resources"] >= constants.WARRIOR_PRICE:
            spawn_warrior(state, api)

        # We iterate through all of our units that are still alive.
        for unit in state["units"]:
            # If the unit is a worker and it sees at least one resource
            # then make it go to the first resource to collect it.
            if unit["type"] == UnitType.WORKER:
                act_worker(state, api, unit)

            # If the unit is a warrior and it sees an opponent then make it shoot.
            if unit["type"] == UnitType.WARRIOR:
                act_warrior(state, api, unit)


# Connects your bot to Lia game engine, don't change it.
if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(connect(MyBot()))
