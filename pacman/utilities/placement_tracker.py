from pacman import exceptions


class PlacementTracker():
    """

    """

    def __init__(self, machine):
        self._placements_available = dict()
        self._free_cores = 0
        for chip in machine.chips:
            key = (chip.x, chip.y)
            self._placements_available[key] = set()
            for processor in chip.processors:
                if processor.processor_id != 0 or chip.virtual:
                    self._placements_available[key].add(
                            processor.processor_id)
                    self._free_cores += 1

    def assign_core(self, x, y, p):
        key = (x, y)
        #check key exists
        if not key in self._placements_available:
            raise exceptions.PacmanPlaceException(
                "cannot assign to chip {}:{} as the chip does not exist for "
                "placement".format(x, y))
        #locate processor list
        processors_available = self._placements_available[key]
        if p is None:
            # locate first available
            p = self.locate_first_available(x, y)
        else:
            #check that there's a processor available
            if p not in processors_available:
                raise exceptions.PacmanPlaceException(
                    "cannot assign to processor {} in chip {}:{} as the "
                    "processor has already been assigned")
        #update processor
        processors_available.remove(p)
        self._free_cores -= 1
        return x, y, p

    def unassign_core(self, x, y, p):
        key = (x, y)
        processor_list = self._placements_available[key]
        if p not in processor_list:
            processor_list.add(p)
        else:
            raise exceptions.PacmanPlaceException(
                "cannot unassign processor {} in chip {}:{} as the "
                "processor has already been unassigned")
        self._free_cores += 1

    def has_available_cores_left(self, x, y, p):
        key = (x, y)
        if key not in self._placements_available.keys():
            raise exceptions.PacmanPlaceException(
                "cannot determine if the chip {}:{} has free processors, as"
                " the chip does not exist in the machine".format(x, y))
        else:
            available_cores = self._placements_available[key]
            if p is None:
                return len(available_cores) > 0
            else:
                return p in available_cores

    def locate_first_available(self, x, y):
        key = (x, y)

        #check key exists
        if not key in self._placements_available.keys():
            raise exceptions.PacmanPlaceException(
                "cannot assign to chip {}:{} as the chip does not exist for "
                "placement".format(x, y))
        if len(self._placements_available[key]) > 0:
            return next(iter(self._placements_available[key]))
        return None
