from pacman.model.graphs.application import ApplicationGraph
from pacman.utilities.utility_objs.chip_counter import ChipCounter
import numpy as np
from pacman.model.graphs.application.application_vertex import ApplicationVertex
from pacman.model.graphs.common import Slice, MDSlice 


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


    @classmethod
    def AdoptSolution(self, adapter_output: bytearray, graph: ApplicationGraph, chip_counter: ChipCounter):
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
        adapter_output.extend(bytes('1' * chip_core_representation_total_length, 'ascii'))

        for i in range(0, N + 1):
            while i > presum_N_Ai[application_vertex_index]:
                application_vertex_index += 1

            i_th_neuron__info_encoding_begin = i * chip_core_representation_total_length
            i_th_neuron_info_encoding_end = (i + 1) * chip_core_representation_total_length
            encoded_neuron_info_str_value = encoded_solution[i_th_neuron__info_encoding_begin:i_th_neuron_info_encoding_end].decode()
            encoded_neuron_info_int_value = int(encoded_neuron_info_str_value, 2)
            chip_id = encoded_neuron_info_int_value / max_chips_per_core
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
                app_vertex = graph.vertices[application_vertex_index]
                lo_atom = prev_index
                hi_atom = i - 1
                n_on_core_1_dim = hi_atom - lo_atom + 1
                vertex_slice = None
                if len(app_vertex.atoms_shape) == 1:
                    vertex_slice = Slice(lo_atom=lo_atom, hi_atom=hi_atom)
                else:
                    start = SolutionAdopter.to_multi_dimension_representation(lo_atom, app_vertex.atoms_shape)
                    n_on_core = SolutionAdopter.to_multi_dimension_representation(n_on_core_1_dim, app_vertex.atoms_shape)
                    vertex_slice = MDSlice(
                        lo_atom, hi_atom, tuple(n_on_core), tuple(start), 
                        app_vertex.atoms_shape)
                label = f"{app_vertex.label}{vertex_slice}"

                prev_chip_id = chip_id
                prev_core_id = core_id
                prev_index = i

                

        chip_counter.n_chips = max_chips
    
    