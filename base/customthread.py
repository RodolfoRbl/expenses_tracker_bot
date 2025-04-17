import time
from threading import Thread


class CustomThread(Thread):

    def __init__(self, func, *args, **kwargs) -> None:
        Thread.__init__(self)
        self.func = func
        self.result = None
        self.args = args
        self.kwargs = kwargs

    def run(self):
        self.result = self.func(*self.args, **self.kwargs)

    def join_and_result(self):
        super().join()
        return self.result


def wait(sec, name):
    print("start of waiting")
    print(f"the parameter is: {sec} and the name {name}")
    time.sleep(2)
    print("end of waiting")
    return 100


def something_else():
    for i in range(4):
        print(f"doing something else {i}")

