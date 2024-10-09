use pyo3::prelude::*;
use std::sync::{Arc, Mutex};

// Worker struct: represents a simple worker with an id and state.
#[pyclass]
struct Worker {
    id: usize,
    state: usize,
}

#[pymethods]
impl Worker {
    #[new]
    fn new(id: usize, state: usize) -> Worker {
        Worker { id, state }
    }

    // Simulates the worker performing a task, here just incrementing its state.
    fn perform_task(&mut self) {
        self.state += 1;
        println!(
            "Worker {} performed a task, new state: {}",
            self.id, self.state
        );
    }

    // Reports the current state.
    fn report_state(&self) -> usize {
        self.state
    }
}

// Aggregator struct: collects worker states.
#[pyclass]
struct Aggregator {
    states: Arc<Mutex<Vec<usize>>>,
}

#[pymethods]
impl Aggregator {
    #[new]
    fn new() -> Aggregator {
        Aggregator {
            states: Arc::new(Mutex::new(vec![])),
        }
    }

    // Updates the state in the aggregator.
    fn collect_state(&self, state: usize) {
        let mut states = self.states.lock().unwrap();
        states.push(state);
    }

    // Returns all collected states.
    fn get_all_states(&self) -> Vec<usize> {
        let states = self.states.lock().unwrap();
        states.clone()
    }
}

/// Python module.
#[pymodule]
fn ants_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Worker>()?;
    m.add_class::<Aggregator>()?;
    Ok(())
}
