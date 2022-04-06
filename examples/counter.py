class Counter():
    def __init__(self, start=0):
        self.counter = start - 1

    def __call__(self):
        self.counter += 1
        return self.counter

    def value(self):
        return self.counter
