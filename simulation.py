import random
from typing import Any, Self

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from config import SimulationConfig
from environment import Environment
from models import Ant, Colony, Position, Queen


class Simulation(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    colony: Colony
    environment: Environment
    config: SimulationConfig = Field(default_factory=SimulationConfig)
    ant_paths: dict[int, list[Position]] = Field(default_factory=dict)
    current_time: float = 0.0

    @classmethod
    def from_config_or_default(
        cls: type[Self],
        config: SimulationConfig | None = None,
        environment_type: type | None = None,
    ) -> Self:
        config = config or SimulationConfig()
        grid_width, grid_height = config.grid_size
        queen_position = (
            random.randint(grid_width // 4, 3 * grid_width // 4),
            random.randint(grid_height // 4, 3 * grid_height // 4),
        )
        environment = (environment_type or Environment)(config)

        ants = set()
        ant_paths = {}
        for i in range(config.num_ants):
            ant = Ant(
                position=(
                    random.randint(0, grid_width - 1),
                    random.randint(0, grid_height - 1),
                ),
                id=i,
                lifespan=config.ant.initial_lifespan,
                carrying_capacity=config.ant.carrying_capacity,
            )
            ants.add(ant)
            ant_paths[ant.id] = []

        simulation: Self = cls(
            config=config,
            colony=Colony(
                queen=Queen(position=queen_position),
                ants=ants,
            ),
            environment=environment,
            ant_paths=ant_paths,
        )
        return simulation

    def run(self, context: dict[str, Any] | None = None) -> dict[str, Any]:
        if context:
            print(f"Using context: {context}")

        while self.current_time < self.config.simulation_duration:
            self.step(self.config.animation.step_interval)
        return self.get_stats()

    def step(self, time_delta: float) -> None:
        self.current_time += time_delta
        self.environment.update(self.current_time)

        for ant in list(self.colony.ants):
            ant.update(
                self.environment,
                self.colony,
                self.config,
                self.current_time,
                time_delta,
            )
            if ant.id not in self.ant_paths:
                self.ant_paths[ant.id] = []
            self.ant_paths[ant.id].append(ant.position)

        self.colony.update(self.config, time_delta)

        # Remove paths of dead ants
        dead_ant_ids = set(self.ant_paths.keys()) - {ant.id for ant in self.colony.ants}
        for ant_id in dead_ant_ids:
            del self.ant_paths[ant_id]

    def get_stats(self) -> dict[str, Any]:
        return {
            "ants": len(self.colony.ants),
            "eggs": self.colony.eggs,
            "food": self.colony.food_store,
            "ant_paths": self.ant_paths,
            "queen_position": self.colony.queen.position,
            "current_time": self.current_time,
        }

    def animate(self) -> animation.FuncAnimation:
        fig, ax = plt.subplots(figsize=self.config.animation.figsize)
        plot_elements = self._initialize_plot_elements(ax)

        def init():
            grid_width, grid_height = self.config.grid_size
            ax.set_xlim(-0.5, grid_width - 0.5)
            ax.set_ylim(-0.5, grid_height - 0.5)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_xticklabels([])
            ax.set_yticklabels([])
            ax.set_aspect("equal", "box")
            ax.autoscale(enable=False)
            return self._get_artists(plot_elements)

        def update(frame):
            self.step(self.config.animation.step_interval)
            self._update_plot_elements(plot_elements, ax)
            return self._get_artists(plot_elements)

        ani = animation.FuncAnimation(
            fig,
            update,
            frames=int(
                self.config.simulation_duration / self.config.animation.step_interval
            ),
            init_func=init,
            interval=self.config.animation.step_interval * 1000,
            blit=False,
            repeat=False,
        )

        plt.tight_layout()
        plt.show()

        return ani

    def _initialize_plot_elements(self, ax):
        elements = {
            "ant_scatter": ax.scatter([], [], c="black", s=20),
            "queen_scatter": ax.scatter([], [], c="red", s=100),
            "food_scatter": ax.scatter([], [], c="green", alpha=0.5),
            "pheromone_im": ax.imshow(
                np.zeros((self.config.grid_size[1], self.config.grid_size[0], 4)),
                interpolation="nearest",
                extent=[0, self.config.grid_size[0], 0, self.config.grid_size[1]],
                origin="lower",
            ),
            "queen_annotation": ax.annotate(
                "",
                xy=(0, 0),
                fontsize=10,
                color="red",
                ha="center",
                va="bottom",
                clip_on=True,
            ),
            "ant_annotations": [],
            "food_annotations": [],
        }
        return elements

    def _update_plot_elements(self, elements, ax):
        # Update ant positions
        ant_positions = np.array([ant.position for ant in self.colony.ants])
        if len(ant_positions) > 0:
            elements["ant_scatter"].set_offsets(ant_positions)
        else:
            elements["ant_scatter"].set_offsets(np.empty((0, 2)))

        # Update ant annotations
        num_ants = len(self.colony.ants)
        current_annotations = len(elements["ant_annotations"])

        if num_ants > current_annotations:
            for _ in range(num_ants - current_annotations):
                annotation = elements["ant_scatter"].axes.annotate(
                    "",
                    xy=(0, 0),
                    fontsize=8,
                    ha="center",
                    va="bottom",
                    clip_on=True,
                )
                elements["ant_annotations"].append(annotation)
        elif num_ants < current_annotations:
            for _ in range(current_annotations - num_ants):
                annotation = elements["ant_annotations"].pop()
                annotation.remove()

        for ant, annotation in zip(self.colony.ants, elements["ant_annotations"]):
            x, y = ant.position
            annotation.set_position((x, y))
            annotation.set_text(f"{ant.food:.1f}")
            annotation.set_visible(True)

        # Update queen position
        elements["queen_scatter"].set_offsets([self.colony.queen.position])

        # Update queen annotation
        elements["queen_annotation"].set_position(self.colony.queen.position)
        resources_needed = self.config.food_required_to_lay_egg - self.colony.food_store
        elements["queen_annotation"].set_text(f"{resources_needed:.1f}")

        # Update food positions and sizes
        food_positions = self.environment.get_food_positions()
        if food_positions:
            food_positions_array = np.array(food_positions)
            food_sizes = [
                self.environment.grid[pos[0], pos[1], 0] * 5 for pos in food_positions
            ]
            elements["food_scatter"].set_offsets(food_positions_array)
            elements["food_scatter"].set_sizes(food_sizes)
        else:
            elements["food_scatter"].set_offsets(np.empty((0, 2)))
            elements["food_scatter"].set_sizes([])

        # Update food annotations
        num_food = len(food_positions)
        current_food_annotations = len(elements["food_annotations"])

        if num_food > current_food_annotations:
            for _ in range(num_food - current_food_annotations):
                annotation = elements["food_scatter"].axes.annotate(
                    "",
                    xy=(0, 0),
                    fontsize=8,
                    color="green",
                    ha="center",
                    va="bottom",
                    clip_on=True,
                )
                elements["food_annotations"].append(annotation)
        elif num_food < current_food_annotations:
            for _ in range(current_food_annotations - num_food):
                annotation = elements["food_annotations"].pop()
                annotation.remove()

        for pos, annotation in zip(food_positions, elements["food_annotations"]):
            x, y = pos
            annotation.set_position((x, y))
            food_amount = self.environment.grid[pos[0], pos[1], 0]
            annotation.set_text(f"{food_amount:.1f}")
            annotation.set_visible(True)

        # Update pheromone grid
        pheromone_grid = self.get_combined_pheromone_grid()
        elements["pheromone_im"].set_data(pheromone_grid)

        # Update title
        ax.set_title(
            f"Time: {self.current_time:.1f}s | Ants: {len(self.colony.ants)} | Eggs Waiting: {self.colony.eggs}",
            fontsize=12,
        )

    def get_combined_pheromone_grid(self) -> np.ndarray:
        grid_shape = self.environment.grid.shape
        pheromone_layers = self.environment.grid[:, :, 1:].copy()
        pheromone_layers = pheromone_layers.transpose(
            (1, 0, 2)
        )  # Transpose for display

        rgba_image = np.zeros((grid_shape[1], grid_shape[0], 4), dtype=np.float32)

        max_intensity = self.config.pheromone_initial_intensity
        max_opacity = self.config.pheromone_max_opacity

        # Regular pheromone (blue channel)
        regular_pheromone = (
            pheromone_layers[:, :, 0] if pheromone_layers.shape[2] > 0 else 0
        )
        # Food pheromone (green channel)
        food_pheromone = (
            pheromone_layers[:, :, 1] if pheromone_layers.shape[2] > 1 else 0
        )
        # Rich pheromone (purple: red + blue channels)
        rich_pheromone = (
            pheromone_layers[:, :, 2] if pheromone_layers.shape[2] > 2 else 0
        )

        # Normalize and limit opacity
        regular_opacity = np.clip(
            regular_pheromone / max_intensity * max_opacity, 0, max_opacity
        )
        food_opacity = np.clip(
            food_pheromone / max_intensity * max_opacity, 0, max_opacity
        )
        rich_opacity = np.clip(
            rich_pheromone / max_intensity * max_opacity, 0, max_opacity
        )

        # Combine pheromones into RGBA channels
        rgba_image[:, :, 2] += regular_opacity  # Blue channel
        rgba_image[:, :, 1] += food_opacity  # Green channel
        rgba_image[:, :, 0] += rich_opacity  # Red channel

        # Alpha channel: maximum of all pheromone opacities
        rgba_image[:, :, 3] = np.maximum.reduce(
            [regular_opacity, food_opacity, rich_opacity]
        )

        return rgba_image

    def _get_artists(self, elements):
        return (
            [
                elements["ant_scatter"],
                elements["queen_scatter"],
                elements["food_scatter"],
                elements["pheromone_im"],
                elements["queen_annotation"],
            ]
            + elements["ant_annotations"]
            + elements["food_annotations"]
        )
