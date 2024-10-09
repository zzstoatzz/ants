from ants_rs import Aggregator, Worker

if __name__ == "__main__":
    # Create a worker and aggregator
    worker = Worker(1, 0)
    aggregator = Aggregator()

    # Worker performs a task and reports state
    worker.perform_task()
    aggregator.collect_state(worker.report_state())

    # Fetch all states collected by the aggregator
    print(aggregator.get_all_states())  # Output: [1]
