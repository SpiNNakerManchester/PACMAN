class PlacementTracker():

    def __init__(self, board_id, x, y, processors, sdram_size, cpu_speed,
                 dtcm_per_proc):
        self.board_id = board_id
        self.x = x
        self.y = y
        self.sdram_size = sdram_size
        self.cpu_speed = cpu_speed
        self.dtcm_per_proc = dtcm_per_proc

        self.core_available = list()
        next_id = 0
        self.free_cores = 0
        for prcoessor in sorted(processors,
                                key=lambda processor: processor.idx):
            if next_id is not None:
                for _ in range(next_id, prcoessor.idx):
                    self.core_available.append(False)
            self.core_available.append(True)
            self.free_cores += 1
            next_id = prcoessor.idx + 1
        self.free_sdram = sdram_size

    def assign_core(self, sdram, core=None):
        chosen_core = None
        if core is not None:
            self.core_available[core] = False
            chosen_core = core
        else:
            for i in range(0, len(self.core_available)):
                if self.core_available[i]:
                    self.core_available[i] = False
                    chosen_core = i
                    break

        self.free_cores -= 1
        self.free_sdram -= sdram

        return chosen_core

    def unassign_core(self, sdram, core):
        self.core_available[core] = True
        self.free_cores += 1
        self.free_sdram -= sdram