from pacman import exceptions


class PlacementTracker():
    """

    """

    def __init__(self, machine):
        self._placements_available = dict()
        self._free_cores = 0
        for chip in machine.chips:
            key = (chip.x, chip.y)
            self._placements_available[key] = list()
            for processor in chip.processors:
                if processor.processor_id == 0 and not chip.virtual:
                    self._placements_available[key]\
                        .append(False)
                else:
                    self._placements_available[key]\
                        .append(True)
                    self._free_cores += 1
            # last element will be available cores tracker
            self._placements_available[key].append(len(list(chip.processors)))

    def assign_core(self, x, y, p):
        key = (x, y)
        #check key exists
        if not key in self._placements_available.keys():
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
            if not processors_available[p]:
                raise exceptions.PacmanPlaceException(
                    "cannot assign to processor {} in chip {}:{} as the "
                    "processor has already been assigned")
        #update processor
        processors_available[p] = False
        processors_available[-1] -= 1
        self._free_cores -= 1
        return x, y, p

    def unassign_core(self, x, y, p):
        key = (x, y)
        processor_list = self._placements_available[key]
        if not processor_list[p]:
            processor_list[p] = True
            processor_list[-1] += 1
        else:
            raise exceptions.PacmanPlaceException(
                "cannot unassign processor {} in chip {}:{} as the "
                "processor has already been unassigned")
        self._free_cores += 1

    def has_available_cores_left(self, x, y, p):
        key = (x, y)
        if not key in self._placements_available.keys():
            raise exceptions.PacmanPlaceException(
                "cannot determine if the chip {}:{} has free processors, as the"
                " chip does not exist in the machine".format(x, y))
        else:
            available_cores = self._placements_available[key]
            if p is None:
                if available_cores[-1] > 0:
                    return True
                else:
                    return False
            else:
                return available_cores[p]

    def locate_first_available(self, x, y):
        key = (x, y)
        #check key exists
        if not key in self._placements_available.keys():
            raise exceptions.PacmanPlaceException(
                "cannot assign to chip {}:{} as the chip does not exist for "
                "placement".format(x, y))
        index = 0
        processors_available = self._placements_available[key]
        for processor in processors_available:
            if processor:
                return index
            index += 1
        return None

