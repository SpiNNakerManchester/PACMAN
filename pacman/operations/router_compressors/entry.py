class Entry(object):
    __slots__ = ["key", "mask", "defaultable", "spinnaker_route"]

    def __init__(self, key, mask, defaultable, spinnaker_route):
        self.key = key
        self.mask = mask
        self.defaultable = defaultable
        self.spinnaker_route = spinnaker_route

    def __str__(self):
        return "{} {} {}".format(self.key, self.mask, self.spinnaker_route)
