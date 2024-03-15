class ResourceConfiguration(object):
    def __init__(self, neuron_count, max_chips, max_core_per_chips, max_sdram) -> None:
        self._neuron_count = neuron_count
        self._max_chips = max_chips
        self._max_cores_per_chip = max_core_per_chips
        self._max_sdram = max_sdram
    
    def get_neruon_count(self):
        return self._neuron_count
    
    def get_max_chips(self):
        return self._max_chips
    
    def get_max_cores_per_chip(self):
        return self._max_cores_per_chip

    def get_max_sdram(self):
        return self._max_sdram
    
    def set_neuron_count(self, neuron_count):
        self._neuron_count = neuron_count