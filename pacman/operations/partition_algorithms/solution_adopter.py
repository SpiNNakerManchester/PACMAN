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
from typing import Sequence
from numpy.typing import NDArray
from spynnaker.pyNN.models.neuron.population_machine_common import (
    PopulationMachineCommon)
from .solution_checker import SolutionChecker
from numpy import floating


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

    def __get_variable_sdram(self, n_atoms: int, vertex: ApplicationVertex) -> AbstractSDRAM:
        """
        Returns the variable SDRAM from the recorders.

        :param int n_atoms: The number of atoms to account for
        :return: the variable SDRAM used by the neuron recorder
        :rtype: VariableSDRAM
        """
        s_dynamics = vertex.synapse_dynamics
        if isinstance(s_dynamics, AbstractSynapseDynamicsStructural):
            max_rewires_per_ts = s_dynamics.get_max_rewires_per_ts()
            vertex.synapse_recorder.set_max_rewires_per_ts(
                max_rewires_per_ts)

        return (
            vertex.get_max_neuron_variable_sdram(n_atoms) +
            vertex.get_max_synapse_variable_sdram(n_atoms))

    def __get_constant_sdram(
            self, n_atoms: int, all_syn_block_sz: int,
            structural_sz: int, vertex: ApplicationVertex) -> MultiRegionSDRAM:
        """
        Returns the constant SDRAM used by the atoms.

        :param int n_atoms: The number of atoms to account for
        :rtype: ~pacman.model.resources.MultiRegionSDRAM
        """
        s_dynamics = vertex.synapse_dynamics
        n_record = (
            len(vertex.neuron_recordables) +
            len(vertex.synapse_recordables))

        n_provenance = NeuronProvenance.N_ITEMS + MainProvenance.N_ITEMS
        if isinstance(s_dynamics, AbstractLocalOnly):
            n_provenance += LocalOnlyProvenance.N_ITEMS
        else:
            n_provenance += (
                SynapseProvenance.N_ITEMS + SpikeProcessingProvenance.N_ITEMS)

        sdram = MultiRegionSDRAM()
        if isinstance(s_dynamics, AbstractLocalOnly):
            sdram.merge(vertex.get_common_constant_sdram(
                n_record, n_provenance,
                PopulationMachineLocalOnlyCombinedVertex.COMMON_REGIONS))
            sdram.merge(vertex.get_neuron_constant_sdram(
                n_atoms,
                PopulationMachineLocalOnlyCombinedVertex.NEURON_REGIONS))
            sdram.merge(self.__get_local_only_constant_sdram(n_atoms))
        else:
            sdram.merge(vertex.get_common_constant_sdram(
                n_record, n_provenance,
                PopulationMachineVertex.COMMON_REGIONS))
            sdram.merge(vertex.get_neuron_constant_sdram(
                n_atoms, PopulationMachineVertex.NEURON_REGIONS))
            sdram.merge(self.__get_synapse_constant_sdram(self, 
                n_atoms, all_syn_block_sz, structural_sz, vertex))
        return sdram


    def __get_synapse_constant_sdram(
            self, n_atoms: int, all_syn_block_sz: int,
            structural_sz: int, vertex: ApplicationVertex) -> MultiRegionSDRAM:
        """
        Get the amount of fixed SDRAM used by synapse parts.

        :param int n_atoms: The number of atoms to account for

        :rtype: ~pacman.model.resources.MultiRegionSDRAM
        """
        regions = PopulationMachineVertex.SYNAPSE_REGIONS
        sdram = MultiRegionSDRAM()
        sdram.add_cost(regions.synapse_params,
                       vertex.get_synapse_params_size())
        sdram.add_cost(regions.synapse_dynamics,
                       vertex.get_synapse_dynamics_size(
                           n_atoms))
        sdram.add_cost(regions.structural_dynamics, structural_sz)
        sdram.add_cost(regions.synaptic_matrix, all_syn_block_sz)
        sdram.add_cost(
            regions.pop_table,
            MasterPopTableAsBinarySearch.get_master_population_table_size(
                vertex.incoming_projections))
        sdram.add_cost(regions.connection_builder,
                       vertex.get_synapse_expander_size())
        sdram.add_cost(regions.bitfield_filter,
                       get_sdram_for_bit_field_region(
                           vertex.incoming_projections))
        return sdram
    
    def get_sdram_used_by_atoms(
            self, n_atoms: int, all_syn_block_sz: int,
            structural_sz: int, vertex: ApplicationVertex) -> AbstractSDRAM:
        """
        Gets the resources of a slice of atoms.

        :param int n_atoms:
        :rtype: ~pacman.model.resources.MultiRegionSDRAM
        """
        # pylint: disable=arguments-differ
        variable_sdram = self.__get_variable_sdram(self, n_atoms, vertex)
        constant_sdram = self.__get_constant_sdram(self, 
            n_atoms, all_syn_block_sz, structural_sz, vertex)
        sdram = MultiRegionSDRAM()
        sdram.nest(len(PopulationMachineVertex.REGIONS) + 1, variable_sdram)
        sdram.merge(constant_sdram)

        # return the total resources.
        return sdram
    
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
    def AdoptSolution(self, adapter_output: bytearray, graph: ApplicationGraph, chip_counter: ChipCounter, max_atoms_per_core: int):
        if not SolutionChecker.check(adapter_output):
            raise RuntimeError("[solution_adopter.py] Machine graph solution not satisfies constraints.")
        encoded_solution = adapter_output
        N_Ai = [vertex.n_atoms for vertex in graph.vertices]
        presum_N_Ai = [0] * len(N_Ai)
        N = np.sum(N_Ai)
        max_chips = 0
        max_chip_count = N
        max_chips_per_core = 18
        chip_core_representation_total_length = int(np.ceil(np.log2(max_chip_count * max_chips_per_core)))
        prev_index = -1
        prev_chip_id = -1
        prev_core_id = -1
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
        slice_index = 0
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
                # make slice here
                # Slice(prev_i, i)
                # make machine vertex ....
                application_vertex = list(graph.vertices)[application_vertex_index]
                lo_atom = prev_index
                hi_atom = i - 1
                n_on_core_1_dim = hi_atom - lo_atom + 1
                vertex_slice = None
                if len(application_vertex.atoms_shape) == 1:
                    vertex_slice = Slice(lo_atom=lo_atom, hi_atom=hi_atom)
                else:
                    start = SolutionAdopter.to_multi_dimension_representation(lo_atom, application_vertex.atoms_shape)
                    n_on_core = SolutionAdopter.to_multi_dimension_representation(n_on_core_1_dim, application_vertex.atoms_shape)
                    vertex_slice = MDSlice(
                        lo_atom, hi_atom, tuple(n_on_core), tuple(start), 
                        application_vertex.atoms_shape)
                label = f"{application_vertex.label}{vertex_slice}"

                prev_chip_id = chip_id
                prev_core_id = core_id
                prev_index = i
                ring_buffer_shifts = application_vertex.get_ring_buffer_shifts()
                weight_scales = application_vertex.get_weight_scales(ring_buffer_shifts)
                all_syn_block_sz = application_vertex.get_synapses_size(
                    max_atoms_per_core)
                structural_sz = application_vertex.get_structural_dynamics_size(
                    max_atoms_per_core)
                sdram = self.get_sdram_used_by_atoms(self,
                    max_atoms_per_core, all_syn_block_sz, structural_sz, application_vertex)
                synapse_regions = PopulationMachineVertex.SYNAPSE_REGIONS
                synaptic_matrices = SynapticMatrices(
                    application_vertex, synapse_regions, max_atoms_per_core, weight_scales,
                    all_syn_block_sz)
                neuron_data = NeuronData(application_vertex)

                index = slice_index
                machine_vertex = self.create_machine_vertex(self,
                    vertex_slice, sdram, label,
                    structural_sz, ring_buffer_shifts, weight_scales,
                    index, max_atoms_per_core, synaptic_matrices, neuron_data, application_vertex)
                application_vertex.remember_machine_vertex(machine_vertex)
                slice_index += 1               

        chip_counter.set_n_chips(max_chips)
    
    