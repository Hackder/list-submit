from typing import Callable
import threading


IsAlive = Callable[[], bool]


def run_with_companion[
    T
](task: Callable[[], T], companion: Callable[[IsAlive], None]) -> T:
    """
    Starts the task and companion functions at the same time,
    and waits for the task to finish.

    The companion function is passed a helper getter `is_alive` function,
    that will return True if the task is still running. It is the developers
    responsibility to terminate the compation when the task is finished.

    Returns the result of the task function.

    Example:
        def companion(is_alive):
            while is_alive():
                print("Task is still running")
                time.sleep(1)

        run_with_companion(some_long_task, companion)
    """

    alive: list[bool] = [True]

    def is_alive() -> bool:
        nonlocal alive
        return alive[0]

    companion_thread = threading.Thread(target=lambda: companion(is_alive))
    # Make sure the companion thread is terminated when the main thread is terminated
    companion_thread.daemon = True
    companion_thread.start()
    result = task()
    alive[0] = False
    companion_thread.join()

    return result
