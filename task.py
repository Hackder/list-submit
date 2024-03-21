from typing import Callable
import threading


IsAlive = Callable[[], bool]


def run_with_companion(task: Callable, companion: Callable[[IsAlive], None]) -> None:
    """
    Starts the task and companion functions at the same time,
    and waits for the task to finish.

    The companion function is passed a helper getter `is_alive` function,
    that will return True if the task is still running. It is the developers
    responsibility to terminate the compation when the task is finished.

    Example:
        def companion(is_alive):
            while is_alive():
                print("Task is still running")
                time.sleep(1)

        run_with_companion(some_long_task, companion)
    """

    alive = True

    def is_alive() -> bool:
        nonlocal alive
        return alive

    companion_thread = threading.Thread(target=lambda: companion(is_alive))
    companion_thread.start()
    task()
    companion_thread.join()
