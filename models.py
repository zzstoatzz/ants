import random
from typing import Optional, Self, TypeAlias

import numpy as np
from pydantic import (
    BaseModel,
    ConfigDict,
    NonNegativeFloat,
    NonNegativeInt,
    PositiveInt,
)

from config import SimulationConfig
from environment import Environment

Position: TypeAlias = tuple[int, int]


class Ant(BaseModel):
    position: Position
    previous_position: Optional[Position] = None
    food: NonNegativeFloat = 0
    returning_to_queen: bool = False
    id: int  # Unique identifier for each ant

    def __hash__(self) -> int:
        return self.id

    def update(
        self,
        environment: Environment,
        colony: "Colony",
        config: SimulationConfig,
        current_time: float,
    ):
        if self.returning_to_queen:
            self.move_towards(colony.queen.position, config.grid_size)
            if self.position == colony.queen.position:
                self.deposit_food(colony)
        else:
            self.move(environment, config)
            self.collect_food(environment, config)
        self.leave_pheromone(environment, current_time)

    def move(self, environment: Environment, config: SimulationConfig):
        grid_size = config.grid_size
        perception_radius = config.perception_radius

        # Check for food within perception radius
        food_positions = environment.get_food_positions_within_radius(
            self.position, perception_radius
        )
        if food_positions:
            # Move towards the closest food
            closest_food = min(
                food_positions,
                key=lambda pos: self.manhattan_distance(self.position, pos, grid_size),
            )
            self.previous_position = self.position
            self.move_towards(closest_food, grid_size)
        else:
            # Existing movement logic
            possible_moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            # Calculate new positions and exclude previous position
            new_positions = []
            for move in possible_moves:
                new_x = (self.position[0] + move[0]) % grid_size[0]
                new_y = (self.position[1] + move[1]) % grid_size[1]
                new_pos = (new_x, new_y)
                if new_pos != self.previous_position:
                    new_positions.append(new_pos)

            # If all moves lead back to the previous position, include it to avoid being stuck
            if not new_positions:
                for move in possible_moves:
                    new_x = (self.position[0] + move[0]) % grid_size[0]
                    new_y = (self.position[1] + move[1]) % grid_size[1]
                    new_positions.append((new_x, new_y))

            # Choose next move based on pheromones and randomness
            self.previous_position = self.position
            self.position = self.choose_move_based_on_pheromones(
                new_positions, environment, config
            )

    def choose_move_based_on_pheromones(
        self,
        new_positions: list[Position],
        environment: Environment,
        config: SimulationConfig,
    ):
        pheromone_levels = []
        for pos in new_positions:
            pheromone_level = environment.get_pheromone_level(pos)
            pheromone_levels.append(pheromone_level + 1e-6)  # Avoid zero probabilities

        total_pheromone = sum(pheromone_levels)
        chaos = config.randomness_factor
        probabilities = []
        for level in pheromone_levels:
            probabilities.append(
                ((1 - chaos) * (level / total_pheromone) if total_pheromone > 0 else 0)
                + (chaos / len(new_positions))
            )

        # return a random position based on normalized probabilities
        return random.choices(
            new_positions, weights=[prob / sum(probabilities) for prob in probabilities]
        )[0]

    def move_towards(
        self: Self,
        target_position: Position,
        grid_size: tuple[PositiveInt, PositiveInt],
    ):
        x, y = self.position
        tx, ty = target_position

        dx = (tx - x + grid_size[0]) % grid_size[0]
        dy = (ty - y + grid_size[1]) % grid_size[1]

        if dx > grid_size[0] // 2:
            dx -= grid_size[0]
        if dy > grid_size[1] // 2:
            dy -= grid_size[1]

        if dx != 0:
            x = (x + int(np.sign(dx))) % grid_size[0]
        if dy != 0:
            y = (y + int(np.sign(dy))) % grid_size[1]

        self.previous_position = self.position
        self.position = (x, y)

    def collect_food(self, environment: Environment, config: SimulationConfig):
        food_found = environment.get_food(self.position)
        self.food += food_found
        if self.food >= config.food_threshold_return:
            self.returning_to_queen = True

    def deposit_food(self, colony: "Colony"):
        colony.food_store += self.food
        self.food = 0
        self.returning_to_queen = False

    def leave_pheromone(self, environment: Environment, current_time: float):
        environment.add_pheromone(self.position, current_time)

    def manhattan_distance(
        self, pos1: Position, pos2: Position, grid_size: tuple[int, int]
    ) -> int:
        dx = abs(pos1[0] - pos2[0])
        dy = abs(pos1[1] - pos2[1])
        dx = min(dx, grid_size[0] - dx)
        dy = min(dy, grid_size[1] - dy)
        return dx + dy


class Queen(BaseModel):
    position: Position


class Colony(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    ants: set[Ant]
    queen: Queen
    food_store: NonNegativeFloat = 0
    eggs: NonNegativeInt = 0
    egg_timers: list[float] = []

    def update(self, config: SimulationConfig, time_delta: float):
        self.hatch_eggs(config, time_delta)
        self.lay_eggs(config)

    def lay_eggs(self, config: SimulationConfig):
        eggs_to_lay = int(self.food_store // config.food_required_to_lay_egg)
        self.food_store %= config.food_required_to_lay_egg
        self.eggs += eggs_to_lay
        self.egg_timers.extend([0.0] * eggs_to_lay)

    def hatch_eggs(self, config: SimulationConfig, time_delta: float):
        self.egg_timers = [timer + time_delta for timer in self.egg_timers]
        hatched_indices = [
            i
            for i, timer in enumerate(self.egg_timers)
            if timer >= config.egg_gestation_period
        ]
        for index in sorted(hatched_indices, reverse=True):
            new_ant = Ant(
                position=self.queen.position,
                id=random.randint(0, int(1e9)),
            )
            self.ants.add(new_ant)
            del self.egg_timers[index]
            self.eggs -= 1
