from pacman.model.graphs.application import ApplicationGraph
from pacman.utilities.utility_objs.chip_counter import ChipCounter
import numpy as np
from pacman.model.graphs.application.application_vertex import ApplicationVertex
from pacman.model.graphs.common import Slice, MDSlice 
from spynnaker.pyNN.models.neuron import PopulationMachineVertex
from spynnaker.pyNN.models.neuron.neuron_data import NeuronData
from spynnaker.pyNN.models.neuron.synaptic_matrices import SynapticMatrices
from pacman.model.resources import AbstractSDRAM
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
from typing import Sequence, cast
from numpy.typing import NDArray
from spynnaker.pyNN.models.neuron.population_machine_common import (PopulationMachineCommon)

from pacman.operations.partition_algorithms.solution_checker import SolutionChecker
from pacman.operations.partition_algorithms.ga.entities.resource_configuration import ResourceConfiguration
from numpy import floating
from pacman.operations.partition_algorithms.utils.sdram_recorder import SDRAMRecorder
from pacman.operations.partition_algorithms.utils.sdram_calculator import SDRAMCalculator

class SolutionAdopter:
  

    @classmethod
    def to_multi_dimension_representation(num :int, max_per_dimension):
        l = num
        s = max_per_dimension
        shape_dimensions = len(s)
        t =  [0] * shape_dimensions
        m = 1
        for i in reversed(range(0, shape_dimensions)):
            m *= s[i]
            remainder = l % m
            quotient = l / m
            t[i] = remainder
        
            if quotient == 0:
                break
        return t

    def create_machine_vertex(
            self, vertex_slice: Slice, sdram: AbstractSDRAM, label: str,
            structural_sz: int, ring_buffer_shifts: Sequence[int],
            weight_scales: NDArray[floating], index: int,
            max_atoms_per_core: int, synaptic_matrices: SynapticMatrices,
            neuron_data: NeuronData, vertex: ApplicationVertex) -> PopulationMachineCommon:
        # If using local-only create a local-only vertex
        s_dynamics = vertex.synapse_dynamics
        if isinstance(s_dynamics, AbstractLocalOnly):
            return PopulationMachineLocalOnlyCombinedVertex(
                sdram, label, self.governed_app_vertex, vertex_slice, index,
                ring_buffer_shifts, weight_scales, neuron_data,
                max_atoms_per_core)

        # Otherwise create a normal vertex
        return PopulationMachineVertex(
            sdram, label, vertex, vertex_slice, index,
            ring_buffer_shifts,
            weight_scales, structural_sz, max_atoms_per_core,
            synaptic_matrices, neuron_data)
    
    @classmethod
    def AdoptSolution(self, adapter_output: bytearray, graph: ApplicationGraph, chip_counter: ChipCounter, resource_constraint_configuration: ResourceConfiguration):
        _sdram_recorder = SDRAMRecorder()
        encoded_solution = adapter_output
        N_Ai = [vertex.n_atoms for vertex in graph.vertices]
        if len(N_Ai) == 0:
            return
        presum_N_Ai = [0] * len(N_Ai)
        presum_N_Ai[0] = N_Ai[0]
        N = np.sum(N_Ai)
        max_chips = 0
        max_chip_count = N if resource_constraint_configuration.get_max_chips() <= 1 else resource_constraint_configuration.get_max_chips()
        max_chips_per_core = resource_constraint_configuration.get_max_cores_per_chip()
        chip_core_representation_total_length = int(np.ceil(np.log2(max_chip_count * max_chips_per_core)))
        prev_index = -1
        prev_chip_id = -1
        prev_core_id = -1
        core_neuron_slice_placement_record_map = dict({})

        # calculate presum of neuron count vertexes 
        for i in range(1, len(presum_N_Ai)):
            presum_N_Ai[i] = presum_N_Ai[i - 1] + N_Ai[i]

        application_vertex_index = 0
        vertices = list(graph.vertices)
        # Append bytes of a dummy chip-core neuron location representation of at the end of bytearray, for simplying 
        # the deployment of the last slice of neurons.
        # Nueron slice deployment condition is met when encounter this representation at the (N+1)-th iteration, and 
        # the last slice of neurons be deployed at the (N+1)-th iteration.
        extend_encoding = bytes('1' * chip_core_representation_total_length, 'ascii')
        adapter_output.extend(extend_encoding)
        slice_index = 0

        sdram_calculator: SDRAMCalculator = SDRAMCalculator(vertices[application_vertex_index]) 
        # Iterate neurons, making slices, and record slices and neurons amount in cores.
        for i in range(0, N + 1):
            while i > presum_N_Ai[application_vertex_index]:
                application_vertex_index += 1

            i_th_neuron__info_encoding_begin = i * chip_core_representation_total_length
            i_th_neuron_info_encoding_end = (i + 1) * chip_core_representation_total_length
            encoded_neuron_info_str_value = encoded_solution[i_th_neuron__info_encoding_begin:i_th_neuron_info_encoding_end].decode()
            encoded_neuron_info_int_value = int(encoded_neuron_info_str_value, 2)
            chip_id = encoded_neuron_info_int_value // max_chips_per_core
            core_id = encoded_neuron_info_int_value % max_chips_per_core
            max_chips = max(max_chips, chip_id + 1)

            if prev_index == -1 or prev_chip_id == -1 or prev_core_id == -1:
                prev_index = i
                prev_chip_id = chip_id
                prev_core_id = core_id
                continue
            
            if chip_id != prev_chip_id or core_id != prev_core_id:
                application_vertex = vertices[application_vertex_index]
                lo_atom = prev_index
                hi_atom = i - 1
                n_on_core_1_dim = hi_atom - lo_atom + 1
                vertex_slice = None
                # Make Slice
                if len(application_vertex.atoms_shape) == 1:
                    vertex_slice = Slice(lo_atom=lo_atom, hi_atom=hi_atom)
                else:
                    start = SolutionAdopter.to_multi_dimension_representation(lo_atom, application_vertex.atoms_shape)
                    n_on_core = SolutionAdopter.to_multi_dimension_representation(n_on_core_1_dim, application_vertex.atoms_shape)
                    vertex_slice = MDSlice(
                        lo_atom, hi_atom, tuple(n_on_core), tuple(start), 
                        application_vertex.atoms_shape)
                label = f"{application_vertex.label}{vertex_slice}"

                lo_atom = prev_index
                hi_atom = i - 1
                n_on_core_1_dim = hi_atom - lo_atom + 1
                

                # record neuron_count and slice of this core
                key_chip_core_location =  ("%d#%d" % (chip_id, core_id)) 
                if key_chip_core_location in core_neuron_slice_placement_record_map:
                    core_neuron_slice_placement_record_map[key_chip_core_location]['atoms_in_core'] = \
                        core_neuron_slice_placement_record_map[key_chip_core_location]['atoms_in_core'] + n_on_core_1_dim
                else:
                    core_neuron_slice_placement_record_map[key_chip_core_location] = {}
                    core_neuron_slice_placement_record_map[key_chip_core_location]['atoms_in_core'] = \
                        n_on_core_1_dim
                    core_neuron_slice_placement_record_map[key_chip_core_location]['slices'] = []
                core_neuron_slice_placement_record_map[key_chip_core_location]['slices'].append((application_vertex, vertex_slice))
                prev_chip_id = chip_id
                prev_core_id = core_id
                prev_index = i

        # iterate records, creating machine vertexes.
        for key in core_neuron_slice_placement_record_map.keys():
            atoms_in_core = core_neuron_slice_placement_record_map[key]['atoms_in_core'] # atoms_in_core: total number of atoms in the core
            chip_core_index = [int(x) for x in str(key).split("#")]
            chip_index = chip_core_index[0]
            core_index = chip_core_index[1]
            
            # iterate all slices in the core identified by (chip_index, core_index)
            for (application_vertex, vertex_slice) in core_neuron_slice_placement_record_map[key]['slices']:
                # It seems the atoms_in_core should be the size of slice.
                ring_buffer_shifts = application_vertex.get_ring_buffer_shifts()
                weight_scales = application_vertex.get_weight_scales(ring_buffer_shifts)
                slice_n_atoms = vertex_slice.n_atoms
                all_syn_block_sz = application_vertex.get_synapses_size(
                        slice_n_atoms)
                structural_sz = application_vertex.get_structural_dynamics_size(
                        slice_n_atoms)

                recorded_sdram = _sdram_recorder._get_sdram(chip_index, core_index)                
                sdram = sdram_calculator.get_sdram_used_by_atoms(
                        slice_n_atoms, all_syn_block_sz, structural_sz, application_vertex)
                
                if recorded_sdram == None:
                    _sdram_recorder._record_sdram(chip_index, core_index, sdram)
                    recorded_sdram = sdram
                else:
                    recorded_sdram.merge(sdram)

                synapse_regions = PopulationMachineVertex.SYNAPSE_REGIONS

                # Note that the 3rd argument of __init__ method of SynapticMatrices class
                # should be the max_atoms_per_core
                synaptic_matrices = SynapticMatrices(
                        application_vertex, synapse_regions, atoms_in_core, weight_scales,
                        all_syn_block_sz)
                neuron_data = NeuronData(application_vertex)

                index = slice_index
                machine_vertex = self.create_machine_vertex(self,
                        vertex_slice, recorded_sdram, label,
                        structural_sz, ring_buffer_shifts, weight_scales, index, 
                        slice_n_atoms, synaptic_matrices, neuron_data, application_vertex)
                application_vertex.remember_machine_vertex(machine_vertex)
                slice_index += 1
        chip_counter.set_n_chips(max_chips)
    
    