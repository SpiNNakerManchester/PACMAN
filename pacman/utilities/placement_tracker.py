from pacman import exceptions


class PlacementTracker():

    def __init__(self, machine):
        self._placements_avilable = dict()
        self._free_cores = 0
        for chip in machine.chips:
            key = "{}:{}".format(chip.x, chip.y)
            self._placements_avilable[key] = list()
            for processor in chip.processors:
                if processor.processor_id == 0 and not chip.virtual:
                    self._placements_avilable[key]\
                        .append(False)
                else:
                    self._placements_avilable[key]\
                        .append(True)
                    self._free_cores += 1
            # last eleemtn will be avilable cores tracker
            self._placements_avilable[key].append(len(list(chip.processors)))
        placements_assigned = dict()

    def assign_core(self, x, y, p):
        key = "{}:{}".format(x, y)
        #check key exists
        if not key in self._placements_avilable.keys():
            raise exceptions.PacmanPlaceException(
                "cannot assign to chip {}:{} as the chip does not exist for "
                "placement".format(x, y))
        #locate processor list
        processors_avilable = self._placements_avilable[key]
        if p is None:
            # locate first avilable
            p = self.locate_first_avilable(x, y)
        else:
            #check that theres a processor avialble
            if not processors_avilable[p]:
                raise exceptions.PacmanPlaceException(
                    "cannot assign to processor {} in chip {}:{} as the "
                    "processor has already been assigned")
        #update processor
        processors_avilable[p] = False
        processors_avilable[-1] -= 1
        self._free_cores -= 1
        return x, y, p

    def unassign_core(self, x, y, p):
        key = "{}:{}".format(x, y)
        processor_list = self._placements_avilable[key]
        if not processor_list[p]:
            processor_list[p] = True
            processor_list[-1] += 1
        else:
            raise exceptions.PacmanPlaceException(
                "cannot unassign processor {} in chip {}:{} as the "
                "processor has already been unassigned")
        self._free_cores += 1

    def has_avilable_cores_left(self, x, y, p):
        key = "{}:{}".format(x, y)
        if not key in self._placements_avilable.keys():
            raise exceptions.PacmanPlaceException(
                "cannot detemrine if the chip {}:{} has free processors, as the"
                " chip does not exist in the machine".format(x, y))
        else:
            avilable_cores = self._placements_avilable[key]
            if p is None:
                if avilable_cores[-1] > 0:
                    return True
                else:
                    return False
            else:
                return avilable_cores[p]

    def locate_first_avilable(self, x, y):
        key = "{}:{}".format(x, y)
        #check key exists
        if not key in self._placements_avilable.keys():
            raise exceptions.PacmanPlaceException(
                "cannot assign to chip {}:{} as the chip does not exist for "
                "placement".format(x, y))
        index = 0
        processors_avilable = self._placements_avilable[key]
        for processor in processors_avilable:
            if processor:
                return index
            index += 1
        return None

