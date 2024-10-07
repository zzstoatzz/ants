import random
from typing import Self, TypeAlias

import numpy as np
from config import SimulationConfig

Position: TypeAlias = tuple[int, int]


class Environment:
    def __init__(self: Self, config: SimulationConfig):
        self.config: SimulationConfig = config
        self.grid_shape = (
            config.grid_size[0],
            config.grid_size[1],
            2,
        )  # Layers: 0 - Food, 1 - Pheromone
        self.grid = np.zeros(self.grid_shape, dtype=np.float32)
        self.food_positions = set()
        self.last_update_time: float = 0.0

    def update(self: Self, current_time: float) -> None:
        # Spawn new food
        if random.random() < self.config.food_spawn_chance:
            num_foods = self.calculate_number_of_foods_to_spawn()
            for _ in range(num_foods):
                pos = (
                    random.randint(0, self.config.grid_size[0] - 1),
                    random.randint(0, self.config.grid_size[1] - 1),
                )
                food_amount = self.calculate_food_value()
                self.grid[pos[0], pos[1], 0] += food_amount
                self.food_positions.add(pos)

        # Evaporate pheromones
        time_elapsed = current_time - self.last_update_time
        decay_factor = np.exp(-self.config.pheromone_evaporation_rate * time_elapsed)
        self.grid[:, :, 1] *= decay_factor
        self.grid[:, :, 1][self.grid[:, :, 1] < 1e-3] = (
            0.0  # Remove negligible pheromones
        )

        self.last_update_time = current_time

    def calculate_number_of_foods_to_spawn(self) -> int:
        baseline = self.config.food_spawn_baseline
        variance = self.config.food_spawn_variance
        num_foods = random.randint(baseline - variance, baseline + variance)
        num_foods = max(0, num_foods)  # Ensure non-negative
        return num_foods

    def calculate_food_value(self) -> float:
        baseline = self.config.food_value_baseline
        variance = self.config.food_value_variance
        food_value = random.uniform(baseline - variance, baseline + variance)
        food_value = max(1.0, food_value)  # Ensure minimum food value of 1.0
        return food_value

    def add_pheromone(self: Self, position: Position, current_time: float) -> None:
        self.grid[position[0], position[1], 1] = self.config.pheromone_initial_intensity

    def get_pheromone_level(self: Self, position: Position) -> float:
        return self.grid[position[0], position[1], 1]

    def get_food(self: Self, position: Position) -> float:
        food = self.grid[position[0], position[1], 0]
        if food > 0:
            self.grid[position[0], position[1], 0] = 0
            self.food_positions.discard(position)
        return food

    def get_food_positions(self: Self) -> list[Position]:
        return list(self.food_positions)

    def get_food_positions_within_radius(
        self, position: Position, radius: int
    ) -> list[Position]:
        grid_size = self.config.grid_size
        x0, y0 = position
        food_positions = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if abs(dx) + abs(dy) > radius:
                    continue  # Skip positions outside the Manhattan radius
                x = (x0 + dx) % grid_size[0]
                y = (y0 + dy) % grid_size[1]
                if (x, y) in self.food_positions:
                    food_positions.append((x, y))
        return food_positions

    def get_pheromone_grid(self: Self) -> np.ndarray:
        return self.grid[:, :, 1]
