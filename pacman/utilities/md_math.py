# Copyright (c) 2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import math


def get_pop_info(n_neurons_per_core, n_cores):
    """
    Simplifed pop_info

    If using global key allocation the shift may be even bigger

    """
    core_shift = (n_neurons_per_core - 1).bit_length()
    pop_extra_shift = (n_cores - 1).bit_length()
    return {"pop_shift": core_shift + pop_extra_shift,
            "core_shift": core_shift,
            "core_mask":  (1 << pop_extra_shift) - 1,
            "neuron_mask": (1 << core_shift) - 1,
            "neurons_per_core": n_neurons_per_core}


def get_key(pop_info, pop_id, core_id, neuron_id):
    return (pop_id << pop_info["pop_shift"]) + \
           (core_id << pop_info["core_shift"]) + neuron_id


def get_core_index_from_key(key, pop_info):
    return (key >> pop_info["core_shift"]) & pop_info["core_mask"]


def get_neuron_index_from_key(key, pop_info):
    return key & pop_info["neuron_mask"]


def key_to_row(key, pop_info):
    # instead of looking up th epop_info just have it passed in
    core_index = get_core_index_from_key(key, pop_info)
    neuron_index = get_neuron_index_from_key(key, pop_info)
    return (core_index * pop_info["neurons_per_core"]) + neuron_index


def calc_pynn_neuron_indexes(pynn_neuron_index, full_size):
    n_dimensions = len(full_size)
    pynn_neuron_indexes = [None] * n_dimensions

    # Work out the position of the neuron in each dimension
    remainder = pynn_neuron_index
    for n in range(n_dimensions):
        pynn_neuron_indexes[n] = remainder % full_size[n]
        remainder = remainder // full_size[n]
    return pynn_neuron_indexes


def calc_core_indexes(pynn_neuron_indexes, neurons_per_cores):
    n_dimensions = len(neurons_per_cores)
    core_indexes = [None] * n_dimensions

    # Work out which core the neuron is on in each dimension
    for n in range(n_dimensions):
        core_indexes[n] = pynn_neuron_indexes[n] // neurons_per_cores[n]
    return core_indexes


def calc_core_index(core_indexes, full_size, neurons_per_cores):
    n_dimensions = len(core_indexes)

    # Work out the core index
    core_index = 0
    cum_cores_per_size = 1
    for n in range(n_dimensions):
        core_index += cum_cores_per_size * core_indexes[n]
        cores_per_size = full_size[n] // neurons_per_cores[n]
        cum_cores_per_size *= cores_per_size
    return core_index


def calc_neuron_indexes(pynn_neuron_indexes, neurons_per_cores, core_indexes):
    n_dimensions = len(core_indexes)
    neuron_indexes = [None] * n_dimensions

    # Work out the neuron index on this core in each dimension
    for n in range(n_dimensions):
        neuron_indexes[n] = \
            pynn_neuron_indexes[n] - (neurons_per_cores[n] * core_indexes[n])
    return neuron_indexes


def calc_neuron_index(neurons_per_cores, neuron_indexes):
    n_dimensions = len(neuron_indexes)

    # Work out the neuron index on this core
    neuron_index = 0
    cum_per_core = 1
    for n in range(n_dimensions):
        neuron_index += cum_per_core * neuron_indexes[n]
        cum_per_core *= neurons_per_cores[n]
    return neuron_index


def check_md_math(neurons_per_cores, n_cores_per_d, do_print=False):
    neurons_per_core = math.prod(neurons_per_cores)
    n_cores = math.prod(n_cores_per_d)
    full_size = [neurons_per_cores[i] * n_cores_per_d[i] for i in
                 range(len(neurons_per_cores))]
    n_neurons = math.prod(full_size)

    pop_info = get_pop_info(neurons_per_core, n_cores)
    print(pop_info)

    all_pynn_neuron_indexes = set()
    all_results = set()
    for pynn_neuron_index in range(n_neurons):
        pynn_neuron_indexes = calc_pynn_neuron_indexes(
            pynn_neuron_index, full_size)
        core_indexes = calc_core_indexes(
            pynn_neuron_indexes, neurons_per_cores)
        core_index = calc_core_index(
            core_indexes, full_size,  neurons_per_cores)
        neuron_indexes = calc_neuron_indexes(
            pynn_neuron_indexes, neurons_per_cores, core_indexes)
        neuron_index = calc_neuron_index(neurons_per_cores, neuron_indexes)
        key = get_key(pop_info, 13, core_index, neuron_index)
        row_k = key_to_row(key, pop_info)
        row_index = (core_index * neurons_per_core) + neuron_index
        if do_print:
            print(f"{ pynn_neuron_index=}, {pynn_neuron_indexes=}, "
                  f"{core_indexes=}, {core_index=}, {neuron_indexes=},"
                  f" {neuron_index=} {key=} {row_k=} {row_index=}")
        assert row_k == row_index
        as_tuple = tuple(pynn_neuron_indexes)
        assert (as_tuple not in all_pynn_neuron_indexes)
        all_pynn_neuron_indexes.add(as_tuple)
        assert (core_index, neuron_index) not in all_results
        all_results.add((core_index, neuron_index))
        assert (0 <= core_index < n_cores)
        assert (0 <= neuron_index < neurons_per_core)


if __name__ == '__main__':
    check_md_math(
        neurons_per_cores=[2, 3, 2], n_cores_per_d=[2, 3, 1], do_print=True)
