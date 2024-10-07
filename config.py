# config.py

from pydantic import Field, PositiveFloat, PositiveInt, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AnimationConfig(BaseSettings):
    figsize: tuple[int, int] = (8, 6)
    step_interval: PositiveFloat = 0.1  # in seconds


class FoodAllocationConfig(BaseSettings):
    spawn_chance: PositiveFloat = 0.2
    spawn_baseline: PositiveInt = 3
    spawn_variance: PositiveInt = 2
    value_baseline: PositiveFloat = 5.0
    value_variance: PositiveFloat = 3.0


class AntConfig(BaseSettings):
    carrying_capacity: PositiveFloat = 10.0
    initial_lifespan: PositiveFloat = 100.0
    lifespan_extension_on_contribution: PositiveFloat = 20.0


class SimulationConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ANTS_", extra="ignore")

    grid_size: tuple[PositiveInt, PositiveInt] = (200, 200)
    num_ants: PositiveInt = 100
    simulation_duration: PositiveFloat = 1000.0  # in seconds

    food: FoodAllocationConfig = Field(default_factory=FoodAllocationConfig)
    ant: AntConfig = Field(default_factory=AntConfig)

    # Colony behavior configuration
    food_required_to_lay_egg: PositiveFloat = 42.0
    egg_gestation_period: PositiveFloat = 10.0

    pheromone_initial_intensity: PositiveFloat = 1.0
    pheromone_evaporation_rate: PositiveFloat = 0.2
    pheromone_max_opacity: PositiveFloat = 0.5
    randomness_factor: PositiveFloat = 0.3
    enable_multiple_pheromones: bool = True

    animation: AnimationConfig = Field(default_factory=AnimationConfig)

    @computed_field
    @property
    def perception_radius(self) -> int:
        avg_dimension = (self.grid_size[0] + self.grid_size[1]) / 2
        perception = max(2, int(avg_dimension / 5))
        return perception
