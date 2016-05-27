
class BiGUID:
    def __init__(self):
        self.mapA = {}
        self.mapB = {}

    def add(self, a, b):
        self.mapA[a] = b
        self.mapB[b] = a

    def delete(self, a, b):
        del self.mapA[a]
        del self.mapB[b]

    def get_a(self, b):
        return self.mapB[b]

    def get_b(self, a):
        return self.mapA[a]
