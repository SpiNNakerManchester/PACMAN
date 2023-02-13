# Copyright (c) 2017-2023 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" A collection of methods which support partitioning algorithms.
"""

import math
from pacman.exceptions import PacmanConfigurationException
from pacman.model.graphs.common import Slice


def get_multidimensional_slices(app_vertex):
    """ Get the multi-dimensional slices of an application vertex
        such that each is sized to the maximum atoms per dimension per core
        except the last which might be smaller in one or more dimensions

    :param ApplicationVertex app_vertex: The vertex to get the slices of
    """
    # If there is only one slice, get that
    if app_vertex.n_atoms < app_vertex.get_max_atoms_per_core():
        return [Slice(0, app_vertex.n_atoms - 1, app_vertex.atoms_shape,
                      tuple(0 for _ in app_vertex.atoms_shape))]

    atoms_per_core = app_vertex.get_max_atoms_per_dimension_per_core()
    n_atoms = app_vertex.atoms_shape
    if len(atoms_per_core) != len(n_atoms):
        raise PacmanConfigurationException(
            "The length of atoms_per_core doesn't match the number of"
            " dimensions")

    # Find out how many vertices we will create, keeping track of the
    # total atoms per core, and the numerator to divide by when working
    # out positions
    n_vertices = 1
    total_atoms_per_core = 1
    dim_numerator = [0] * len(n_atoms)
    total_n_atoms = 1
    for d in range(len(n_atoms)):
        dim_numerator[d] = n_vertices
        n_this_dim = int(math.ceil(n_atoms[d] / atoms_per_core[d]))
        n_vertices *= n_this_dim
        total_atoms_per_core *= atoms_per_core[d]
        total_n_atoms *= n_atoms[d]

    # Run over all the vertices and create slices for them
    slices = list()
    hi_atom = -1
    for v in range(n_vertices):
        # Work out where in each of the dimensions this vertex starts by
        # dividing the remainder from the previous dimension by the
        # numerator of each dimension
        start = [0] * len(n_atoms)
        n_on_core = [0] * len(n_atoms)
        remainder = v
        total_on_core = 1
        for d in reversed(range(len(n_atoms))):
            start[d] = (remainder // dim_numerator[d]) * atoms_per_core[d]
            remainder = remainder % dim_numerator[d]
            hi_d = min(start[d] + atoms_per_core[d], n_atoms[d])
            n_on_core[d] = hi_d - start[d]
            total_on_core *= n_on_core[d]

        # Make a slice and a vertex
        lo_atom = hi_atom + 1
        hi_atom = (lo_atom + total_on_core) - 1
        vertex_slice = Slice(
            lo_atom, hi_atom, tuple(n_on_core), tuple(start))
        slices.append(vertex_slice)

    return slices
