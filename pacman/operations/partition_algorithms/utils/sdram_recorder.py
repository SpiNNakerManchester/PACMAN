from pacman.model.resources import AbstractSDRAM

class SDRAMRecorder(object):
    def __init__(self) -> None:
        # A dictionary for recording the sdram built for specific cores.
        # key: string with the form of "chip_index#core_index".
        # value: AbstractSDRAM
        self._sdram_records = dict({})
    
    def _get_sdram(self, chip_index, core_index) -> AbstractSDRAM:
        chip_core_identification = '%s#%s' % (chip_index, core_index)
        if chip_core_identification in self._sdram_records:
            return self._sdram_records[chip_core_identification]
        return None
    
    def _record_sdram(self, chip_index, core_index, sdram: AbstractSDRAM) -> None:
        chip_core_identification = '%s#%s' % (chip_index, core_index)
        self._sdram_records[chip_core_identification] = sdram

