# Ant Colony Simulation

![Ants](./assets/animation.gif)

## tl;dr

```
gh repo clone zzstoatzz/ants
cd ants
make setup
make run
```

> [!IMPORTANT]
> I might try and port the core of this simulation to Rust to see if it can run faster.
> The rest here is just AI yapping.

## Introduction

This project is an **Ant Colony Simulation** that models the behavior of ants within a 2D grid environment. The simulation incorporates various aspects of real-world ant colonies, including foraging for food, pheromone communication, colony expansion, and environmental interactions. Through simple rules and interactions, the ants exhibit complex, emergent behaviors that can be observed and analyzed.

## Overview

### Key Components

- **Ants**: Individual agents that explore the environment, collect food, deposit pheromones, and contribute to the colony's growth.
- **Queen**: The central figure of the colony responsible for laying eggs and expanding the colony's population.
- **Colony**: Manages the collective resources, eggs, and overall state of the ant colony.
- **Environment**: A grid-based space where ants move, food spawns, and pheromone trails are laid and evaporate over time.
- **Simulation Configuration**: A set of parameters that define the behavior and properties of the simulation, such as grid size, number of ants, pheromone evaporation rate, and more.
- **Visualization**: An animated display of the simulation using Matplotlib, showing ants, food, pheromone trails, and other relevant information.

## Mechanics

### Ant Behavior

- **Movement and Exploration**:

  - Ants move around the grid based on pheromone levels and random exploration.
  - They avoid immediate backtracking by not returning to their previous position unless no other options are available.
  - Ants have a sensory perception radius (`perception_radius`) allowing them to detect nearby food.
  - If food is detected within this radius, ants move towards the closest food source using the `move_towards` method.

- **Food Collection and Return**:

  - Ants collect food when they reach a cell containing food.
  - Once an ant collects enough food (defined by `food_threshold_return`), it marks itself as returning to the queen.
  - While returning, ants move directly towards the queen's position.
  - Upon reaching the queen, ants deposit the collected food into the colony's food store.

- **Pheromone Communication**:
  - Ants leave pheromone trails as they move, which helps other ants find food sources.
  - Pheromone levels influence the ants' movement decisions, balancing between following trails and exploring new paths.
  - Pheromones evaporate over time based on the `pheromone_evaporation_rate`.

### Queen and Colony Dynamics

- **Food Management**:

  - The colony accumulates food deposited by returning ants.
  - The queen uses the collected food to lay eggs when sufficient resources are available (defined by `food_required_to_lay_egg`).

- **Egg Laying and Hatching**:
  - The queen lays eggs, which take a certain time to hatch (`egg_gestation_period`).
  - Once hatched, new ants are added to the colony and begin participating in foraging activities.

### Environment and Food Spawning

- **Grid Structure**:

  - The environment is represented as a 2D grid with cells containing food, pheromones, or both.
  - Positions wrap around the edges, creating a toroidal (donut-shaped) grid.

- **Food Spawning**:

  - Food spawns randomly based on the `food_spawn_chance`.
  - The number of food items spawned and their values are determined by `food_spawn_baseline`, `food_spawn_variance`, `food_value_baseline`, and `food_value_variance`.
  - This introduces variability in food availability and nutritional content.

- **Pheromone Dynamics**:
  - Pheromones left by ants decay over time, preventing the grid from becoming saturated.
  - The visual opacity of pheromone trails corresponds to their intensity, fading as they evaporate.

## Code Structure and Abstractions

### Models (`models.py`)

- **Ant Class**:

  - Represents individual ants with attributes like `position`, `food`, `returning_to_queen`, and `id`.
  - Methods include:
    - `update()`: Updates the ant's state each simulation step.
    - `move()`: Handles movement logic, including sensory perception and pheromone following.
    - `move_towards()`: Moves the ant towards a specified position.
    - `collect_food()`: Collects food from the environment.
    - `deposit_food()`: Deposits collected food to the colony.
    - `leave_pheromone()`: Leaves pheromones on the current cell.
    - `manhattan_distance()`: Calculates distance for movement decisions.

- **Queen Class**:

  - Represents the queen with a `position`.
  - Manages egg laying and interacts with returning ants.

- **Colony Class**:
  - Manages the collection of ants, the queen, food stores, eggs, and egg timers.
  - Methods include:
    - `update()`: Updates the colony's state, including egg hatching and laying.
    - `lay_eggs()`: Determines when to lay eggs based on food stores.
    - `hatch_eggs()`: Handles the hatching process and adds new ants to the colony.

### Environment (`environment.py`)

- **Environment Class**:
  - Manages the grid, food positions, and pheromone levels.
  - Methods include:
    - `update()`: Updates environmental elements each simulation step.
    - `add_pheromone()`: Adds pheromones to the grid.
    - `get_pheromone_level()`: Retrieves pheromone levels at a position.
    - `get_food()`: Retrieves and removes food from a position.
    - `get_food_positions()`: Returns a list of all food positions.
    - `get_food_positions_within_radius()`: Returns food positions within an ant's perception radius.

### Simulation Configuration (`config.py`)

- **SimulationConfig Class**:
  - Contains all configurable parameters, such as grid size, number of ants, pheromone properties, and food dynamics.
  - Includes a computed field `perception_radius`, which adjusts based on grid size to ensure appropriate sensory range for ants.
  - Parameters include:
    - `grid_size`, `num_ants`, `simulation_duration`
    - Food dynamics: `food_spawn_chance`, `food_spawn_baseline`, `food_spawn_variance`, `food_value_baseline`, `food_value_variance`
    - Ant behavior: `food_threshold_return`, `randomness_factor`
    - Pheromone dynamics: `pheromone_initial_intensity`, `pheromone_evaporation_rate`, `pheromone_max_opacity`

### Simulation and Visualization (`simulation.py`)

- **Simulation Class**:

  - Orchestrates the entire simulation, handling time steps, updates, and visualization.
  - Methods include:
    - `run()`: Executes the simulation without visualization.
    - `step()`: Advances the simulation by a time increment.
    - `animate()`: Creates an animated visualization using Matplotlib.
    - Helper methods for initializing and updating plot elements.

- **Visualization Elements**:
  - **Ants**: Displayed as black dots with annotations showing carried food.
  - **Queen**: Displayed as a red dot with an annotation showing resources needed for the next egg.
  - **Food**: Displayed as green dots with annotations showing their value.
  - **Pheromone Trails**: Visualized as blue gradients that fade over time.
  - **Title**: Shows simulation time, number of ants, and eggs waiting to hatch.

## Setup

- **Required Packages**:
  - `numpy`
  - `matplotlib`
  - `prefect`

### Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/zzstoatzz/ants.git
   cd ants
   ```

2. **Install Dependencies**:

   ```bash
   make setup
   ```

### Running the Simulation

Execute the main script to start the simulation with default settings:

```bash
make run
```

### Configuration

- **Adjust Simulation Parameters**:
  - Modify `config.py` to change settings like grid size, number of ants, food spawning rates, etc.
- **Example**:
  ```python
  SimulationConfig(
      grid_size=(200, 200),
      num_ants=100,
      simulation_duration=2000.0,
      food_spawn_chance=0.2,
      # ... other parameters ...
  )
  ```

## Extending the Simulation

- **Implement New Behaviors**:
  - Extend the `Ant` class to add new behaviors or improve existing ones.
- **Modify Environment Dynamics**:
  - Adjust how food spawns or how pheromones evaporate in `Environment`.
- **Enhance Visualization**:
  - Customize the `Simulation` class to change visual aspects or add new plot elements.

## Project Structure

```
» tree --gitignore
.
├── Makefile
├── README.md
├── __init__.py
├── config.py
├── environment.py
├── main.py
├── models.py
├── requirements.txt
└── simulation.py
```

## Key Concepts

- **Emergent Behavior**: Complex patterns arise from simple rules and interactions among ants.
- **Pheromone Communication**: Ants use pheromones to indirectly communicate and coordinate.
- **Sensory Perception**: Ants detect nearby food and make movement decisions based on sensory input.
- **Resource Management**: The colony manages food resources to grow and sustain its population.
