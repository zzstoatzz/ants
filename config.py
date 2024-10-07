from pydantic import BaseModel, computed_field


class AnimationConfig(BaseModel):
    figsize: tuple[int, int] = (8, 6)
    step_interval: float = 0.1  # in seconds


class SimulationConfig(BaseModel):
    grid_size: tuple[int, int] = (100, 100)
    num_ants: int = 50
    simulation_duration: float = 1000.0  # in seconds

    # Food spawning configuration
    food_spawn_chance: float = (
        0.1  # Probability of attempting to spawn food each update
    )
    food_spawn_baseline: int = 3  # Baseline number of food items to spawn
    food_spawn_variance: int = 2  # Variance in the number of food items spawned
    food_value_baseline: int = 5  # Baseline value (amount) of each food item
    food_value_variance: int = 3  # Variance in the value of each food item

    food_threshold_return: float = 10.0
    food_required_to_lay_egg: float = 50.0
    egg_gestation_period: float = 10.0
    pheromone_initial_intensity: float = 1.0
    pheromone_evaporation_rate: float = 0.1  # Decay rate per time unit
    pheromone_max_opacity: float = 0.5
    randomness_factor: float = 0.5
    animation: AnimationConfig = AnimationConfig()

    @computed_field
    @property
    def perception_radius(self) -> int:
        avg_dimension = (self.grid_size[0] + self.grid_size[1]) / 2
        perception = max(2, int(avg_dimension / 5))
        return perception
