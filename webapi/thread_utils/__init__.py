import threading
import time
from typing import Callable, Iterable, Mapping


class ThreadNotStartingException(Exception):
    pass


class ThreadControllerHasTooManyErrors(Exception):
    pass


class ThreadInfo:
    def __init__(self, num_thread: int, name: str, *, func: Callable, args: Iterable, kwargs: Mapping):
        self.num_thread = num_thread
        self.name = name
        self.func = func
        self.args = args
        self.kwargs = kwargs


class ThreadController:
    def __init__(self):
        self.run_thread: threading.Thread | None = None
        self._lock = threading.RLock()
        self._thread_num = 0
        self._threads: dict[ThreadInfo, threading.Thread] = dict()

    def loop_check(self):
        total_fail_count = 0
        while True:
            for threadInfo, thread in self._threads.copy().items():
                if not thread.is_alive():
                    print(f"Found dead thread #{threadInfo.num_thread} \"{threadInfo.name}\"")
                    total_fail_count += 1
                    if total_fail_count > 10:
                        raise ThreadControllerHasTooManyErrors(f"ThreadControllers has too many fails! Stop")
                    run_count = 0
                    while True:
                        print(f"Restarting thread \"{threadInfo.name}\"")
                        run_count += 1
                        if run_count > 3:
                            raise ThreadNotStartingException(
                                f"Thread {threadInfo.num_thread} failed to start 3 times!")
                        try:
                            self._threads.pop(threadInfo)
                            self.add_thread(threadInfo.func, threadInfo.args, threadInfo.kwargs, name=threadInfo.name)
                        except Exception as e:
                            print(e)
                            continue
                        break
            time.sleep(1)

    def run_infinite(self, block=True):
        self.run_thread = threading.Thread(target=self.loop_check, daemon=True)
        self.run_thread.start()
        if block:
            self.join()

    def join(self):
        while True:
            if not self.run_thread.is_alive():
                break
            self.run_thread.join(1)

    def add_thread(self, func: Callable, args: Iterable = None, kwargs: Mapping = None, name="Unnamed"):
        if args is None:
            args = tuple()
        if kwargs is None:
            kwargs = dict()

        self._thread_num += 1
        funcData = ThreadInfo(self._thread_num, func=func, args=args, kwargs=kwargs, name=name)
        thread = threading.Thread(target=funcData.func, args=args, kwargs=kwargs, daemon=True)
        thread.start()
        self._threads[funcData] = thread

        print(f"Thread #{funcData.num_thread} \"{funcData.name}\" started!")
