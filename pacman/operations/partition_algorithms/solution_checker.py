from pacman.model.graphs.application import ApplicationGraph
from pacman.utilities.utility_objs.chip_counter import ChipCounter
import numpy as np
from pacman.model.graphs.application.application_vertex import ApplicationVertex
from pacman.model.graphs.common import Slice, MDSlice 
from spynnaker.pyNN.models.neuron import PopulationMachineVertex
from spynnaker.pyNN.models.neuron.neuron_data import NeuronData
from spynnaker.pyNN.models.neuron.synaptic_matrices import SynapticMatrices
from pacman.model.resources import AbstractSDRAM, MultiRegionSDRAM
from spynnaker.pyNN.models.neuron.population_machine_vertex import (
    NeuronProvenance, SynapseProvenance, MainProvenance,
    SpikeProcessingProvenance)
from spynnaker.pyNN.models.neuron.local_only import AbstractLocalOnly
from spynnaker.pyNN.models.neuron import (
    PopulationMachineVertex,
    PopulationMachineLocalOnlyCombinedVertex, LocalOnlyProvenance)
from spynnaker.pyNN.models.neuron.synapse_dynamics import (
    AbstractSynapseDynamicsStructural)
from spynnaker.pyNN.models.neuron.master_pop_table import (
    MasterPopTableAsBinarySearch)
from spynnaker.pyNN.utilities.bit_field_utilities import (
    get_sdram_for_bit_field_region)
from typing import Sequence
from numpy.typing import NDArray
from spynnaker.pyNN.models.neuron.population_machine_common import (PopulationMachineCommon)
from numpy import floating
from pacman.operations.partition_algorithms.utils.sdram_recorder import SDRAMRecorder
from pacman.operations.partition_algorithms.ga.entities.resource_configuration import ResourceConfiguration
from pacman.operations.partition_algorithms.utils.sdram_calculator import SDRAMCalculator
from pacman.data import PacmanDataView
class SolutionChecker(object):
    def __init__(self, resource_constraint_configuration: ResourceConfiguration) -> None:
        self._constraint_max_core_per_chip = resource_constraint_configuration.get_max_cores_per_chip()
        self._constraint_max_chips = resource_constraint_configuration.get_max_chips()
        self._constraint_sdram_capacity = resource_constraint_configuration.get_max_sdram()
        self._sdram_recorder: SDRAMRecorder = SDRAMRecorder()

    @classmethod
    def check(self, adapter_output: bytearray, graph: ApplicationGraph, solution_configuration_max_chips = np.inf, solution_configuration_max_chips_per_core = 18) -> bool:
        encoded_solution = adapter_output
        N_Ai = [vertex.n_atoms for vertex in graph.vertices]
        presum_N_Ai = [0] * len(N_Ai)
        N = np.sum(N_Ai)
        chip_core_representation_total_length = int(np.ceil(np.log2(solution_configuration_max_chips * solution_configuration_max_chips_per_core)))
        prev_index = -1
        prev_chip_id = -1
        prev_core_id = -1

        # 1. Calculate the presum of application nodes' neurons count
        presum_N_Ai[0] = N_Ai[0]
        for i in range(1, len(presum_N_Ai)):
            presum_N_Ai[i] = presum_N_Ai[i - 1] + N_Ai[i]

        application_vertex_index = 0
        
        # Append bytes of a dummy chip-core neuron location representation of at the end of bytearray, for simplying 
        # the deployment of the last slice of neurons.
        # Nueron slice deployment condition is met when encounter this representation at the (N+1)-th iteration, and 
        # the last slice of neurons be deployed at the (N+1)-th iteration.
        extend_encoding = bytes('1' * chip_core_representation_total_length, 'ascii')
        adapter_output.extend(extend_encoding)
        
        # Maps "chip_index#core_index" to neuron_count inside the specific core.
        core_neurons_amount_map = dict({})
        for i in range(0, N + 1):
            while i > presum_N_Ai[application_vertex_index]:
                application_vertex_index += 1

            i_th_neuron__info_encoding_begin = i * chip_core_representation_total_length
            i_th_neuron_info_encoding_end = (i + 1) * chip_core_representation_total_length
            encoded_neuron_info_str_value = encoded_solution[i_th_neuron__info_encoding_begin:i_th_neuron_info_encoding_end].decode()
            encoded_neuron_info_int_value = int(encoded_neuron_info_str_value, 2)
            chip_id = encoded_neuron_info_int_value // self._constraint_max_core_per_chip
            core_id = encoded_neuron_info_int_value % self._constraint_max_core_per_chip
            if core_id >= self._constraint_max_core_per_chip or chip_id >= self._constraint_max_chips:
                return False
            max_chips = max(max_chips, chip_id + 1)
            if max_chips > self._constraint_max_chips:
                return False

            if prev_index == -1 or prev_chip_id == -1 or prev_core_id == -1:
                prev_index = i
                prev_chip_id = chip_id
                prev_core_id = core_id
                continue
            
            if chip_id != prev_chip_id or core_id != prev_core_id:
                application_vertex = list(graph.vertices)[application_vertex_index]
                prev_chip_id = chip_id
                prev_core_id = core_id
                prev_index = i

                lo_atom = prev_index
                hi_atom = i - 1
                n_on_core_1_dim = hi_atom - lo_atom + 1
                
                key_core_location =  ("%d#%d" % (chip_id, core_id)) 
                if key_core_location in core_neurons_amount_map:
                    core_neurons_amount_map[key_core_location] = core_neurons_amount_map[key_core_location] + n_on_core_1_dim
                else:
                    core_neurons_amount_map[key_core_location] = n_on_core_1_dim
                
                recorded_sdram = self._sdram_recorder._get_sdram(chip_id, core_id)
                
                # sdram = self.get_sdram_used_by_atoms(self,
                #     atoms_in_atoms, all_syn_block_sz, structural_sz, application_vertex)
                sdram = SDRAMCalculator().calculate_sdram(application_vertex, n_on_core_1_dim)
                if recorded_sdram == None:
                    self._sdram_recorder._record_sdram(chip_id, core_id, sdram)
                    recorded_sdram = sdram
                else:
                    recorded_sdram.merge(sdram)
                
                if recorded_sdram.get_total_sdram(PacmanDataView.get_plan_n_timestep()) > self._constraint_sdram_capacity:
                    return False
    
    