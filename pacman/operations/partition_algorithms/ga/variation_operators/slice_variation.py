from pacman.operations.partition_algorithms.ga.solution_representations.abst_ga_solution_representation import AbstractGASolutionRepresentation
from pacman.operations.partition_algorithms.ga.solution_representations.slice_representation import GASliceSolutionRepresentation
from pacman.operations.partition_algorithms.ga.variation_operators.abst_variation import AbstractGaVariation
from spinn_utilities.overrides import overrides
import random
import numpy as np

class GaSliceVariationuUniformGaussian(AbstractGaVariation):
    @overrides(AbstractGaVariation._do_variation)
    def _do_variation(self, individual: AbstractGASolutionRepresentation) -> AbstractGASolutionRepresentation:
        if not isinstance(individual, GASliceSolutionRepresentation):
            raise TypeError

        if self._use_ptype:
            self._ptype_variation(individual)
            return individual
        else:
            self._gtype_variation(individual)
            return individual

    # in ptype representation, a genes variation should consider the genes near it, so that it could make as more as neurons logically alive neigbor could be in the same place.
    def _ptype_variation(self, individual: GASliceSolutionRepresentation):
        raise NotImplementedError
    
    def _gtype_variation(self, individual: GASliceSolutionRepresentation):
        individual_rep = individual.get_gtype_solution_representation()
        neuron_count = individual_rep[-1] + 1 # Slice are represented closed interval of neurons
        max_cores_per_chip = individual.get_max_cores_per_chip()
        max_chips = individual.get_max_chips()
        gtype_representation_length = len(individual_rep)
        last_slice_end = -1
        for i in range(0, gtype_representation_length):
            slice_to_neuron_index = individual_rep[individual.SLICE_NEURON_TO_INDEX]
            chip_index = individual_rep[individual.CHIP_INDEX]
            core_index = individual_rep[individual.CORE_INDEX]


            is_variation_happen = (random.random() <= self._variation_happen_ratio)
            if is_variation_happen:
                variated_slice_to_neuron_index = 0
                if i != gtype_representation_length - 1:
                    # When there has the next slice, the variated_slice_to_neuron_index should
                    # obey the follow constrants:
                    # 1. No samller than the ending of the last slice.
                    # 2. No greater than the beginning of the next slice.
                    # 3. No greater than the index maximum: (neuron_count - 1)
                    variated_slice_to_neuron_index = \
                        max(last_slice_end + 1,  \
                            min(individual_rep[i + 1][individual.SLICE_NEURON_FROM_INDEX] - 1, min(neuron_count - 1, \
                                   (int)(slice_to_neuron_index + random.gauss(self.get_mu(), self.get_sigma())))))
                else:
                    # When there has the next slice, the variated_slice_to_neuron_index should
                    # obey the follow constrants:
                    # 1. No samller than the ending of the last slice.
                    # 2. No greater than the index maximum: (neuron_count - 1)
                    variated_slice_to_neuron_index = \
                        max(last_slice_end + 1,  min(neuron_count - 1, \
                                    (int)(slice_to_neuron_index + random.gauss(self.get_mu(), self.get_sigma()))))
                
                # Update the current slice's ending.
                individual_rep[individual.SLICE_NEURON_TO_INDEX] = variated_slice_to_neuron_index
                last_slice_end = variated_slice_to_neuron_index
                # Update the next slice's beginning if the next slice exists, so that there is no vacancy between two slices.
                if i != gtype_representation_length - 1:
                    individual_rep[i + 1][individual.SLICE_NEURON_FROM_INDEX] = variated_slice_to_neuron_index + 1

                # Variate chip index
                variated_chip_index = \
                    max(0, min(max_chips, (int)(chip_index + random.gauss(self.get_chip_index_variation_mu(), self.get_chip_index_variation_sigma()))))
                individual_rep[individual.CHIP_INDEX] = variated_chip_index

                 # Variate core index
                variated_core_index = \
                    max(0, min(max_chips, (int)(core_index + random.gauss(self.get_chip_index_variation_mu(), self.get_chip_index_variation_sigma()))))
                individual_rep[individual.CORE_INDEX] = variated_core_index
                


        
    # each gene is variated with a possibility of variation_rate. and the variation quantance obtains a gaussian distribution N(Sigma^2, mu)
    # if a gene is variated, it will make its neighbor neurons in the same place as it. The range of neighbor neuron is decided by a gaussian distribution of N(neibor_effect_sigma, neibor_effect_mu). 
    def __init__(self, use_ptype=True, variation_happen_ratio=0.2, sigma=1.0, mu=0.0, chip_index_variation_mu=0.0, chip_index_variation_sigma=0.0, core_index_variation_mu=0.0, core_index_variation_sigma=0.0) -> None:
        super().__init__()
        self._use_ptype = use_ptype
        self._variation_happen_ratio = variation_happen_ratio
        self._sigma = sigma
        self._mu = mu
        self._chip_index_variation_mu = chip_index_variation_mu
        self._chip_index_variation_sigma = chip_index_variation_sigma
        self._core_index_variation_mu = core_index_variation_mu
        self._core_index_variation_sigma = core_index_variation_sigma

    def get_mu(self):
        return self._mu
    
    def get_sigma(self):
        return self._sigma
    
    def get_variation_happen_ratio(self):
        return self._variation_happen_ratio

    def get_chip_index_variation_mu(self):
        return self._chip_index_variation_mu
    
    def get_chip_index_variation_sigma(self):
        return self._chip_index_variation_sigma
    
    def get_core_index_variation_mu(self):
        return self._core_index_variation_mu
    
    def get_core_index_variation_sigma(self):
        return self._core_index_variation_sigma
    
    def __str__(self):
        return "abst_variation"

