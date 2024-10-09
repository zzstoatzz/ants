from typing import Any

from prefect import flow, task
from prefect.logging import get_run_logger

from config import SimulationConfig
from simulation import Simulation


@flow(log_prints=True)
def animate_simulation(
    config: SimulationConfig | None = None, save_animation: bool = False
) -> dict[str, Any]:
    simulation = Simulation.from_config_or_default(config)
    try:
        animation = task(simulation.animate)()
        if save_animation:
            animation.save(
                "animation.gif",
                writer="pillow",
                fps=simulation.config.animation.fps,
            )
    except KeyboardInterrupt:
        get_run_logger().info("Simulation interrupted by Ctrl+C")
    return task(simulation.get_stats)()


if __name__ == "__main__":
    # animate_simulation.serve(
    #     parameters={"config": dict(grid_size=(50, 50), num_ants=10, steps=10_000)}
    # )
    animate_simulation(SimulationConfig())
