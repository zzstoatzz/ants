import random
from typing import TypeAlias

import numpy as np
from pydantic import (
    BaseModel,
    ConfigDict,
    NonNegativeFloat,
    NonNegativeInt,
    PositiveFloat,
    PositiveInt,
)

from config import SimulationConfig
from environment import Environment

Position: TypeAlias = tuple[NonNegativeInt, NonNegativeInt]


class Ant(BaseModel):
    position: Position
    previous_position: Position | None = None
    food: NonNegativeFloat = 0.0
    returning_to_queen: bool = False
    id: int
    carrying_capacity: PositiveFloat
    source_has_more_food: bool = False
    food_source_position: Position | None = None

    # **Lifespan Attributes**
    age: NonNegativeFloat = 0.0
    lifespan: PositiveFloat

    def __hash__(self) -> int:
        return self.id

    def update(
        self,
        environment: Environment,
        colony: "Colony",
        config: SimulationConfig,
        current_time: float,
        time_delta: float,
    ):
        # Increment age
        self.age += time_delta
        if self.age >= self.lifespan:
            # Ant has died
            colony.remove_ant(self)
            return

        if self.returning_to_queen:
            self.move_towards(colony.queen.position, config.grid_size)
            if self.position == colony.queen.position:
                self.deposit_food(colony, config)
        else:
            self.move(environment, config)
            self.collect_food(environment, config)
        self.leave_pheromone(environment)

    def move(self, environment: "Environment", config: "SimulationConfig"):
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
            # Move based on pheromones and randomness
            self.random_move(environment, config)

    def random_move(self, environment: "Environment", config: "SimulationConfig"):
        possible_moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        grid_width, grid_height = config.grid_size

        # Calculate new positions and exclude previous position
        new_positions = []
        for dx, dy in possible_moves:
            x = (self.position[0] + dx) % grid_width
            y = (self.position[1] + dy) % grid_height
            new_pos = (x, y)
            if new_pos != self.previous_position:
                new_positions.append(new_pos)

        if not new_positions:
            # All moves lead back; include previous position to avoid being stuck
            new_positions = [
                (
                    (self.position[0] + dx) % grid_width,
                    (self.position[1] + dy) % grid_height,
                )
                for dx, dy in possible_moves
            ]

        # Choose next move based on pheromones and randomness
        self.previous_position = self.position
        self.position = self.choose_move_based_on_pheromones(
            new_positions, environment, config
        )

    def choose_move_based_on_pheromones(
        self,
        new_positions,
        environment: "Environment",
        config: "SimulationConfig",
    ) -> Position:
        pheromone_scores = []
        epsilon = 1e-6
        num_positions = len(new_positions)
        randomness_factor = config.randomness_factor

        for pos in new_positions:
            trail_pheromone = environment.get_pheromone_level(pos, "trail")
            if self.returning_to_queen:
                # Follow 'regular' pheromone trails when returning
                regular_pheromone = environment.get_pheromone_level(pos, "regular")
                score = (regular_pheromone + epsilon) / (1 + trail_pheromone)
            else:
                # Avoid 'regular' pheromones and prefer 'food' and 'rich' pheromones
                food_pheromone = environment.get_pheromone_level(pos, "food")
                rich_pheromone = environment.get_pheromone_level(pos, "rich")
                regular_pheromone = environment.get_pheromone_level(pos, "regular")
                score = (food_pheromone + rich_pheromone + epsilon) / (
                    1 + regular_pheromone + trail_pheromone
                )
            pheromone_scores.append(score)

        total_pheromone = sum(pheromone_scores)
        probabilities = []
        for score in pheromone_scores:
            pheromone_prob = (
                (1 - randomness_factor) * (score / total_pheromone)
                if total_pheromone > 0
                else 0.0
            )
            random_prob = randomness_factor / num_positions
            probabilities.append(pheromone_prob + random_prob)

        # Normalize probabilities
        prob_sum = sum(probabilities)
        probabilities = [prob / prob_sum for prob in probabilities]

        chosen_position = random.choices(new_positions, weights=probabilities, k=1)[0]
        return chosen_position

    def move_towards(
        self, target_position: Position, grid_size: tuple[PositiveInt, PositiveInt]
    ):
        x, y = self.position
        tx, ty = target_position
        grid_width, grid_height = grid_size

        dx = (tx - x + grid_width) % grid_width
        dy = (ty - y + grid_height) % grid_height

        if dx > grid_width // 2:
            dx -= grid_width
        if dy > grid_height // 2:
            dy -= grid_height

        if dx != 0:
            x = (x + int(np.sign(dx))) % grid_width
        if dy != 0:
            y = (y + int(np.sign(dy))) % grid_height

        self.previous_position = self.position
        self.position = (x, y)

    def collect_food(self, environment: "Environment", config: "SimulationConfig"):
        available_food = environment.get_food_amount(self.position)
        if available_food > 0:
            food_needed = self.carrying_capacity - self.food
            food_to_collect = min(food_needed, available_food)
            self.food += food_to_collect
            environment.remove_food(self.position, food_to_collect)
            self.food_source_position = self.position
            self.source_has_more_food = environment.get_food_amount(self.position) > 0
            if self.food >= self.carrying_capacity:
                self.returning_to_queen = True

    def deposit_food(self, colony: "Colony", config: SimulationConfig):
        colony.food_store += self.food
        self.food = 0.0
        self.returning_to_queen = False
        self.source_has_more_food = False
        self.food_source_position = None

        # **Extend lifespan upon contribution**
        self.lifespan += config.ant.lifespan_extension_on_contribution

    def leave_pheromone(self, environment: "Environment"):
        if self.returning_to_queen:
            if (
                self.source_has_more_food
                and environment.config.enable_multiple_pheromones
            ):
                pheromone_type = "rich"
            else:
                pheromone_type = "regular"
        else:
            pheromone_type = (
                "food" if environment.config.enable_multiple_pheromones else "regular"
            )
        environment.add_pheromone(self.position, pheromone_type=pheromone_type)
        environment.add_pheromone(self.position, pheromone_type="trail")

    def manhattan_distance(
        self, pos1: Position, pos2: Position, grid_size: tuple[int, int]
    ) -> int:
        grid_width, grid_height = grid_size
        dx = abs(pos1[0] - pos2[0])
        dy = abs(pos1[1] - pos2[1])
        dx = min(dx, grid_width - dx)
        dy = min(dy, grid_height - dy)
        return dx + dy


class Queen(BaseModel):
    position: Position


class Colony(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    ants: set[Ant]
    queen: Queen
    food_store: NonNegativeFloat = 0.0
    eggs: NonNegativeInt = 0
    egg_timers: list[float] = []

    def update(self, config: "SimulationConfig", time_delta: float):
        self.hatch_eggs(config, time_delta)
        self.lay_eggs(config)

    def lay_eggs(self, config: "SimulationConfig"):
        eggs_to_lay = int(self.food_store // config.food_required_to_lay_egg)
        self.food_store %= config.food_required_to_lay_egg
        self.eggs += eggs_to_lay
        self.egg_timers.extend([0.0] * eggs_to_lay)

    def hatch_eggs(self, config: "SimulationConfig", time_delta: float):
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
                lifespan=config.ant.initial_lifespan,
                carrying_capacity=config.ant.carrying_capacity,
            )
            self.ants.add(new_ant)
            del self.egg_timers[index]
            self.eggs -= 1

    def remove_ant(self, ant: Ant):
        self.ants.discard(ant)
