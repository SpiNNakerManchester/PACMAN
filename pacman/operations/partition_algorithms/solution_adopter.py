from pacman.model.graphs.application import ApplicationGraph
from pacman.utilities.utility_objs.chip_counter import ChipCounter
import numpy as np

class SolutionAdopter:
    @classmethod
    def AdoptSolution(adapter_output: bytearray, graph: ApplicationGraph, chip_counter: ChipCounter):
        encoded_solution = adapter_output
        N_Ai = [vertex.n_atoms for vertex in graph.vertices]
        N = np.sum(N_Ai)
        max_chips = 0
        
        core_bits = np.ceil(np.log2(18))
        chip_bits = np.ceil(np.log2(N))
        chip_core_represent_total_length = chip_bits + core_bits
        prev_index = -1
        prev_chip_id = -1
        prev_core_id = -1
        for i in range(0, N):
            i_th_neuron__info_encoding_begin = i * chip_core_represent_total_length
            i_th_neuron_info_encoding_end = (i + 1) * chip_core_represent_total_length
            encoded_neuron_info = encoded_solution[i_th_neuron__info_encoding_begin:i_th_neuron_info_encoding_end].decode()
            chip_id = encoded_neuron_info[0:N].decode(2)
            core_id = encoded_neuron_info[N:].decode(2)
            max_chips = max(max_chips, chip_id + 1)
            if chip_id != prev_chip_id or core_id != prev_core_id:
                # make slice here
                # Slice(prev_i, i)
                # make machine vertex ....

                prev_chip_id = chip_id
                prev_core_id = core_id
                prev_index = i

            

        chip_counter.n_chips = max_chips
