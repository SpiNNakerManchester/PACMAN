from pacman.model.resources import AbstractSDRAM
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
from spynnaker.pyNN.models.neuron.population_machine_common import (PopulationMachineCommon)


class SDRAMCalculator(object):
    def __init__(self, governed_app_vertex: ApplicationVertex) -> None:
        self._governed_app_vertex = governed_app_vertex

    
    def __get_local_only_constant_sdram(
            self, n_atoms: int) -> MultiRegionSDRAM:
        s_dynamics = cast(AbstractLocalOnly,
                          self._governed_app_vertex.synapse_dynamics)
        sdram = MultiRegionSDRAM()
        sdram.add_cost(
            PopulationMachineLocalOnlyCombinedVertex.REGIONS.LOCAL_ONLY,
            PopulationMachineLocalOnlyCombinedVertex.LOCAL_ONLY_SIZE)
        sdram.add_cost(
            PopulationMachineLocalOnlyCombinedVertex.REGIONS.LOCAL_ONLY_PARAMS,
            s_dynamics.get_parameters_usage_in_bytes(
                n_atoms, self._governed_app_vertex.incoming_projections))
        return sdram
    

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
            vertex.synapse_recorder.set_max_rewires_per_ts(max_rewires_per_ts)

        return (vertex.get_max_neuron_variable_sdram(n_atoms) +
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
            sdram.merge(self.__get_synapse_constant_sdram(
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
        variable_sdram = self.__get_variable_sdram(n_atoms, vertex)
        constant_sdram = self.__get_constant_sdram(n_atoms, all_syn_block_sz, 
                                                   structural_sz, vertex)
        sdram = MultiRegionSDRAM()
        sdram.nest(len(PopulationMachineVertex.REGIONS) + 1, variable_sdram)
        sdram.merge(constant_sdram)

        # return the total resources.
        return sdram
    
    def calculate_sdram(self, application_vertex, slice_n_atoms):
        ring_buffer_shifts = application_vertex.get_ring_buffer_shifts()
        weight_scales = application_vertex.get_weight_scales(ring_buffer_shifts)
        all_syn_block_sz = application_vertex.get_synapses_size(slice_n_atoms)
        structural_sz = application_vertex.get_structural_dynamics_size(
                        slice_n_atoms)
        sdram = self.get_sdram_used_by_atoms(self,
                        slice_n_atoms, all_syn_block_sz, structural_sz, application_vertex)
        return sdram

