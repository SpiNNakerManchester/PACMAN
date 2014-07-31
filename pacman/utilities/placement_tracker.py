from pacman import exceptions


class PlacementTracker():

    def __init__(self, machine):
        self._placements_avilable = dict()
        self._free_cores = 0
        for chip in machine.chips:
            key = "{}:{}".format(chip.x, chip.y)
            self._placements_avilable[key] = list()
            for processor in chip.processors:
                self._placements_avilable[key]\
                    .append(processor.processor_id)
                self._free_cores += 1
        placements_assigned = dict()

    def assign_core(self, x, y, p):
        key = "{}:{}".format(x, y)
        #check key exists
        if not key in self._placements_avilable.keys():
            raise exceptions.PacmanPlaceException(
                "cannot assign to chip {}:{} as there are no more avilable "
                "processors".format(x, y))
        #locate processor list
        processors_avilable = self._placements_avilable[key]
        #check that theres a processor avialble
        if not p in processors_avilable:
            raise exceptions.PacmanPlaceException(
                "cannot assign to processor {} in chip {}:{} as the processor "
                "has already been assigned")
        #remove processor
        processors_avilable.remove(p)
        self._free_cores -= 1
        #remove key if chip filled
        if len(processors_avilable) == 0:
            del self._placements_avilable[key]

    def unassign_core(self, x, y, p):
        key = "{}:{}".format(x, y)
        if not key in self._placements_avilable.keys():
            self._placements_avilable[key] = list(p)
        else:
            processor_list = self._placements_avilable[key]
            if not p in processor_list:
                self._placements_avilable[key].append(p)
            else:
                raise exceptions.PacmanPlaceException(
                    "cannot unassign processor {} in chip {}:{} as the "
                    "processor has already been unassigned")
        self._free_cores += 1