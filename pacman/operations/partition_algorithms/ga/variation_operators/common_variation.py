from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.solution_representations.common_ga_solution_representation import CommonGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.variation_operators.abst_variation import AbstractGaVariation
from spinn_utilities.overrides import overrides
import random
import numpy as np

class CommonGaVariationuUniformGaussian(AbstractGaVariation):
    @overrides(AbstractGaVariation._do_variation)
    def _do_variation(self, individual: AbstractGASolutionRepresentation) -> AbstractGASolutionRepresentation:
        if not isinstance(individual, CommonGASolutionRepresentation):
            raise TypeError

        if self._use_ptype:
            self._ptype_variation(individual)
            return individual
        else:
            self._gtype_variation(individual)
            return individual

    # In gtype representation, a gene variation should consider the gen near it, so that it could make as more as neurons logically alive neigbor could be in the same place. 
    def _gtype_variation(self, individual: AbstractGASolutionRepresentation):
        # variate a neuron's chip index and core index, then randomly change its neighbors to the same place.
        single_neuron_encoding_length = individual.get_single_neuron_encoding_length()
        individual_rep = individual.get_gtype_solution_representation()
        if ((len(individual_rep) % single_neuron_encoding_length != 0)):
            raise ValueError

        neuron_count = (len(individual_rep) / single_neuron_encoding_length)
        max_cores_per_chip = individual.get_max_cores_per_chip()
        max_chips = individual.get_max_chips()
        for neuron_index in range(0, neuron_count):
            is_variation = 1 if random.random() <= self.get_variation_rate() else 0
            if is_variation:
                neuron_encoding_begin = neuron_index * single_neuron_encoding_length
                neuron_encoding_end = (neuron_index + 1) * single_neuron_encoding_length
                chip_core_encoding = int(individual_rep[neuron_encoding_begin: neuron_encoding_end], 2)
                chip_index = chip_core_encoding / max_cores_per_chip
                core_index = chip_core_encoding % max_cores_per_chip
                # variate the chips
                v = random.gauss(self._chip_var_mu, self._chip_var_sigma)
                chip_index = max(0, min((int)((chip_index) + v), max_chips - 1))
                
                # variate the cores
                v = random.gauss(self._core_var_mu, self._core_var_sigma)
                core_index = max(0, min((int)((core_index) + v), max_cores_per_chip - 1))
                
                # variate its neighbor
                v = np.abs(random.gauss(self._neibor_effect_mu, self._neibor_effect_mu))
                variation_neuron_index_from = np.max(0, (int)(neuron_index - v))
                variation_neuron_index_to = (np.min((int)(neuron_index + v), neuron_count - 1) + 1) 
                chip_core_encoding_after_variation = ('{0:' + str(single_neuron_encoding_length) + 'b}').format(chip_index * individual.get_max_cores_per_chip() + core_index)
                individual_rep[variation_neuron_index_from * single_neuron_encoding_length:variation_neuron_index_to* single_neuron_encoding_length] = chip_core_encoding_after_variation * (variation_neuron_index_to - variation_neuron_index_from)
        return individual_rep
    
    def _ptype_variation(self, individual: AbstractGASolutionRepresentation):
        # variate a neuron's chip index and core index, then randomly change its neight to the same place
        individual_rep = individual.get_ptype_solution_representation()
    
        neuron_count = len(individual_rep)
        max_cores_per_chip = individual.get_max_cores_per_chip()
        max_chips = individual.get_max_chips()
        for neuron_index in range(0, neuron_count):
            is_variation = 1 if random.random() <= self.get_variation_rate() else 0
            if is_variation:
                chip_core_encoding = individual_rep[neuron_index]
                chip_index = chip_core_encoding / max_cores_per_chip
                core_index = chip_core_encoding % max_cores_per_chip
                # variate the chip index
                v = random.gauss(self._chip_var_mu, self._chip_var_sigma)
                chip_index = max(0, min((int)((chip_index) + v), max_chips - 1))
                
                # variate the core index
                v = random.gauss(self._core_var_mu, self._core_var_sigma)
                core_index = max(0, min((int)((core_index) + v), max_cores_per_chip - 1))
                
                # variate its neighbor
                v = np.abs(random.gauss(self._neibor_effect_mu, self._neibor_effect_mu))
                variation_neuron_index_from = np.max(0, (int)(neuron_index - v))
                variation_neuron_index_to = (np.min((int)(neuron_index + v), neuron_count - 1) + 1) 
                chip_core_encoding_after_variation = (chip_index * individual.get_max_cores_per_chip() + core_index)
                individual_rep[variation_neuron_index_from: variation_neuron_index_to] = chip_core_encoding_after_variation * (variation_neuron_index_to - variation_neuron_index_from)
        return individual_rep
    
    # Each gene is variated with a possibility of variation_rate. and the variation quantance obtains a gaussian distribution N(Sigma^2, mu)
    # If a gene is variated, it will make its neighbor neurons in the same place as it. The range of neighbor neuron is decided by a gaussian distribution of N(neibor_effect_sigma, neibor_effect_mu). 
    def __init__(self, use_ptype=True, variation_rate = 0.001, chip_var_sigma = 1.0, core_var_sigma = 1.0, neighbor_effect_sigma = 100, chip_var_mu = 0.0, core_var_mu = 0.0, neighbor_effect_mu = 0) -> None:
        super().__init__()
        self._use_ptype = use_ptype
        self._chip_var_sigma = chip_var_sigma
        self._chip_var_mu = chip_var_mu
        self._core_var_sigma = core_var_sigma
        self._core_var_mu = core_var_mu
        self._neibor_effect_sigma = neighbor_effect_sigma
        self._neibor_effect_mu = neighbor_effect_mu

        self._variation_rate = variation_rate

    
    def get_variation_rate(self):
        return self._variation_rate

    def __str__(self):
        return "common_variation"

