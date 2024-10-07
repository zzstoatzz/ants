import random
from typing import Self, TypeAlias

import numpy as np

from config import SimulationConfig

Position: TypeAlias = tuple[int, int]


class Environment:
    def __init__(self: Self, config: SimulationConfig):
        self.config: SimulationConfig = config
        grid_width, grid_height = config.grid_size
        # Layers: 0 - Food, 1 - Regular Pheromone, 2 - Food Pheromone, 3 - Rich Pheromone (if enabled)
        num_layers = 5 if config.enable_multiple_pheromones else 2
        self.grid = np.zeros((grid_width, grid_height, num_layers), dtype=np.float32)
        self.food_positions: set[Position] = set()
        self.last_update_time: float = 0.0

    def update(self: Self, current_time: float) -> None:
        self.spawn_food()
        self.evaporate_pheromones(current_time)
        self.last_update_time = current_time

    def spawn_food(self: Self) -> None:
        if random.random() < self.config.food.spawn_chance:
            num_foods = self.calculate_number_of_foods_to_spawn()
            for _ in range(num_foods):
                pos = (
                    random.randint(0, self.config.grid_size[0] - 1),
                    random.randint(0, self.config.grid_size[1] - 1),
                )
                food_amount = self.calculate_food_value()
                self.grid[pos[0], pos[1], 0] += food_amount
                self.food_positions.add(pos)

    def evaporate_pheromones(self: Self, current_time: float) -> None:
        time_elapsed = current_time - self.last_update_time
        decay_factor = np.exp(-self.config.pheromone_evaporation_rate * time_elapsed)
        # Evaporate pheromones in all layers except the food layer (layer 0)
        self.grid[:, :, 1:] *= decay_factor
        self.grid[:, :, 1:][self.grid[:, :, 1:] < 1e-3] = 0.0

    def calculate_number_of_foods_to_spawn(self) -> int:
        baseline = self.config.food.spawn_baseline
        variance = self.config.food.spawn_variance
        num_foods = random.randint(baseline - variance, baseline + variance)
        return max(0, num_foods)

    def calculate_food_value(self) -> float:
        baseline = self.config.food.value_baseline
        variance = self.config.food.value_variance
        food_value = random.uniform(baseline - variance, baseline + variance)
        return max(1.0, food_value)

    def add_pheromone(
        self: Self, position: Position, pheromone_type: str = "regular"
    ) -> None:
        layer_mapping = {"regular": 1, "food": 2, "rich": 3, "trail": 4}
        layer = layer_mapping.get(pheromone_type)
        if layer is not None and layer < self.grid.shape[2]:
            if pheromone_type == "trail":
                self.grid[position[0], position[1], layer] += (
                    self.config.pheromone_initial_intensity
                )

            else:
                self.grid[position[0], position[1], layer] = (
                    self.config.pheromone_initial_intensity
                )

    def get_pheromone_level(
        self: Self, position: Position, pheromone_type: str = "regular"
    ) -> float:
        layer_mapping = {"regular": 1, "food": 2, "rich": 3}
        layer = layer_mapping.get(pheromone_type)
        if layer is not None and layer < self.grid.shape[2]:
            return self.grid[position[0], position[1], layer]
        return 0.0

    def get_food_amount(self: Self, position: Position) -> float:
        return self.grid[position[0], position[1], 0]

    def remove_food(self: Self, position: Position, amount: float) -> None:
        current_amount = self.grid[position[0], position[1], 0]
        new_amount = current_amount - amount
        if new_amount <= 0:
            self.grid[position[0], position[1], 0] = 0.0
            self.food_positions.discard(position)
        else:
            self.grid[position[0], position[1], 0] = new_amount

    def get_food_positions(self: Self) -> list[Position]:
        return list(self.food_positions)

    def get_food_positions_within_radius(
        self, position: Position, radius: int
    ) -> list[Position]:
        grid_width, grid_height = self.config.grid_size
        x0, y0 = position
        positions = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if abs(dx) + abs(dy) > radius:
                    continue
                x = (x0 + dx) % grid_width
                y = (y0 + dy) % grid_height
                if (x, y) in self.food_positions:
                    positions.append((x, y))
        return positions

    def get_pheromone_grid(self: Self) -> np.ndarray:
        return self.grid[:, :, 1:]
