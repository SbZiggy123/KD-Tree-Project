# a simpler binary tree that can be 

class BruteForce:
    def __init__(self):
        self.records = []

    def insert(self, key):
        self.records.append(key)

    def exactSearch(self, target):                          # scan every record for an exact match
        for r in self.records:
            if r == target:
                return r
        return None

    def partialSearch(self, constraints):                   # scan every record and check all constraints
        result = []
        for r in self.records:
            if all(r[dim] == val for dim, val in constraints.items()):
                result.append(r)
        return result

    def regionQuery(self, lower, upper):                    # scan every record and check it falls in the region
        result = []
        for r in self.records:
            if all(lower[i] <= r[i] <= upper[i] for i in range(len(lower))):
                result.append(r)
        return result

    def nearestNeighbour(self, target):                     # scan every record and track the closest
        bestNode = None
        bestDist = float("inf")
        for r in self.records:
            d = sum((r[i] - target[i]) ** 2 for i in range(len(target)))
            if d < bestDist:
                bestDist = d
                bestNode = r
        return bestNode