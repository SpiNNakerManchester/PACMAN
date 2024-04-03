# Copyright (c) 2016 The University of Manchester
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
from __future__ import annotations
import logging
from typing import (
    Collection, Generic, Optional, Tuple, TypeVar, Union, cast, TYPE_CHECKING)

import numpy
from typing_extensions import Self

from spinn_utilities.abstract_base import AbstractBase, abstractmethod
from spinn_utilities.ordered_set import OrderedSet
from spinn_utilities.log import FormatAdapter

from pacman.exceptions import (
    PacmanConfigurationException, PacmanInvalidParameterException)
from pacman.model.graphs import AbstractVertex
if TYPE_CHECKING:
    from pacman.model.partitioner_splitters import AbstractSplitterCommon
    from pacman.model.graphs.machine import MachineVertex
    from pacman.model.routing_info import BaseKeyAndMask
    from .application_edge import ApplicationEdge
    from .application_edge_partition import ApplicationEdgePartition
#: :meta private:
MV = TypeVar("MV", bound='MachineVertex')
logger = FormatAdapter(logging.getLogger(__file__))


class ApplicationVertex(AbstractVertex, Generic[MV], metaclass=AbstractBase):
    """
    A vertex that can be broken down into a number of smaller vertices
    based on the resources that the vertex requires.
    """

    __slots__ = (
        # List of machine vertices associated with this app vertex
        "_machine_vertices",

        # The splitter object associated with this app vertex
        "_splitter",

        # The maximum number of atoms for each dimension for each core.
        # For example, a 2D vertex might have a shape of 640 by 480 with
        # rectangles on each core or 32 by 16.
        # Typically all but possibly the last core will have this number. If
        # the vertex has multiple dimensions, one or more of the dimensions
        # might have fewer atoms on the last core (e.g. the rectangle on the
        # last core of a 2D vertex might be smaller).
        "_max_atoms_per_dimension_per_core")

    def __init__(
            self, label: Optional[str] = None,
            max_atoms_per_core: Optional[Union[int, Tuple[int, ...]]] = None,
            splitter: Optional[AbstractSplitterCommon[Self]] = None):
        """
        :param str label: The optional name of the vertex.
        :param max_atoms_per_core: The max number of atoms that can be
            placed on a core for each dimension, used in partitioning.
            If the vertex is n-dimensional, with n > 1, the value must be a
            tuple with a value for each dimension.  If it is single-dimensional
            the value can be a 1-tuple or an int.
        :type max_atoms_per_core: None or int or tuple(int,...)
        :param splitter: The splitter object needed for this vertex.
            Leave as `None` to delegate the choice of splitter to the selector.
        :type splitter: None or
            ~pacman.model.partitioner_splitters.AbstractSplitterCommon
        """
        # Need to set to None temporarily as add_constraint checks splitter
        self._splitter: Optional[AbstractSplitterCommon[Self]] = None
        super().__init__(label)
        self._machine_vertices: OrderedSet[MV] = OrderedSet()
        if splitter:
            # Use setter as there is extra work to do
            self.splitter = splitter
        # Keep the name for simplicity but move to new internal representation
        self._max_atoms_per_dimension_per_core: Optional[Tuple[int, ...]]
        self._set_max_atoms_per_dimension_per_core(max_atoms_per_core)

    def __str__(self):
        return self.label

    def __repr__(self):
        if self.get_fixed_location():
            return (f"ApplicationVertex({self.label},"
                    f" at{self.get_fixed_location()})")
        else:
            return f"ApplicationVertex({self.label})"

    @property
    def has_splitter(self) -> bool:
        """
        Whether this vertex currently has a splitter defined.
        """
        return self._splitter is not None

    @property
    def splitter(self) -> AbstractSplitterCommon[Self]:
        """
        :rtype: ~pacman.model.partitioner_splitters.AbstractSplitterCommon
        """
        s = self._splitter
        if s is None:
            raise PacmanConfigurationException(
                f"The splitter object on {self._label} has not yet had "
                "a splitter set.")
        return s

    @splitter.setter
    def splitter(self, new_value: AbstractSplitterCommon[Self]):
        """
        Sets the splitter object. Does not allow repeated settings.

        :param new_value: The new splitter object
        :type new_value:
            ~pacman.model.partitioner_splitters.AbstractSplitterCommon
        """
        if self._splitter == new_value:
            return
        if self._splitter is not None:
            raise PacmanConfigurationException(
                f"The splitter object on {self._label} has already been set, "
                "it cannot be reset. Please fix and try again.")
        self._splitter = new_value
        self._splitter.set_governed_app_vertex(self)

    def remember_machine_vertex(self, machine_vertex: MV):
        """
        Adds the machine vertex to the iterable returned by machine_vertices

        :param ~pacman.model.graphs.machine.MachineVertex machine_vertex:
            A pointer to a machine_vertex
        """
        machine_vertex.index = len(self._machine_vertices)
        self._machine_vertices.add(machine_vertex)

    @property
    def atoms_shape(self) -> Tuple[int, ...]:
        """
        The "shape" of the atoms in the vertex i.e. how the atoms are split
        between the dimensions of the vertex.  By default everything is
        1-dimensional, so the value will be a 1-tuple but can be
        overridden by a vertex that supports multiple dimensions.

        :rtype: tuple(int, ...)
        """
        return (self.n_atoms,)

    @property
    @abstractmethod
    def n_atoms(self) -> int:
        """
        The number of atoms in the vertex.

        :rtype: int
        """
        raise NotImplementedError

    def round_n_atoms(
            self, n_atoms: Union[int, float], label: str = "n_atoms") -> int:
        """
        Utility function to allow superclasses to make sure `n_atoms` is an
        integer.

        :param n_atoms: Value convertible to int to be used for `n_atoms`
        :type n_atoms: int or float or numpy.
        :return: Number of atoms.
        :rtype: int
        :raises PacmanInvalidParameterException:
            If the value cannot be safely converted to an integer
        """
        if isinstance(n_atoms, int):
            return n_atoms
        # Allow a float which has a near int value
        temp = int(round(n_atoms))
        if abs(temp - n_atoms) < 0.001:
            if temp != n_atoms:
                logger.warning(
                    "Size of the {} rounded from {} to {}. "
                    "Please use int values for n_atoms",
                    label, n_atoms, temp)
            return temp
        raise PacmanInvalidParameterException(
            label, n_atoms, f"int value expected for {label}")

    @property
    def machine_vertices(self) -> Collection[MV]:
        """
        The machine vertices that this application vertex maps to.

        :rtype: iterable(~pacman.model.graphs.machine.MachineVertex)
        """
        return self._machine_vertices

    def __check_atoms_per_core(self):
        if (len(self._max_atoms_per_dimension_per_core) !=
                len(self.atoms_shape)):
            raise ValueError(
                f"On application vertex {self}, the number of dimensions in"
                " the maximum number of atoms per core "
                f" {self._max_atoms_per_dimension_per_core} must be the same"
                " number of dimensions as that of the vertex shape"
                f" {self.atoms_shape}")
        if len(self.atoms_shape) > 1:
            for maxi, dim in zip(self._max_atoms_per_dimension_per_core,
                                 self.atoms_shape):
                if (dim / maxi) != (dim // maxi):
                    raise ValueError(
                        f"On application vertex {self} each dimension of the"
                        f" vertex shape {self.atoms_shape} must be divisible"
                        " by the maximum number of atoms per core in that"
                        f" dimension {self._max_atoms_per_dimension_per_core}")

    def get_max_atoms_per_core(self) -> int:
        """
        Gets the maximum number of atoms per core, which is either the
        number of atoms required across the whole application vertex,
        or a lower value set.

        :rtype: int
        """
        if self._max_atoms_per_dimension_per_core is None:
            return self.n_atoms
        self.__check_atoms_per_core()
        return int(numpy.prod(self._max_atoms_per_dimension_per_core))

    def get_max_atoms_per_dimension_per_core(self) -> Tuple[int, ...]:
        """
        Gets the maximum number of atoms per dimension per core.  This
        will return a tuple with a number for each dimension of the vertex,
        which might be one if this is a single-dimension vertex.

        :rtype: tuple(int,...)
        """
        if self._max_atoms_per_dimension_per_core is None:
            return self.atoms_shape
        self.__check_atoms_per_core()
        return self._max_atoms_per_dimension_per_core

    def _set_max_atoms_per_dimension_per_core(
            self, new_value: Optional[Union[int, Tuple[int, ...]]]):
        """
        Set the maximum number of atoms per dimension per core.

        Can be used to raise or lower the maximum number of atoms per core
        or per dimension per core.

        :param new_value:
            Value to set.  If the vertex is n-dimensional where n > 1, a tuple
            of n values must be given.  If the vertex is 1 dimensional,
            a 1-tuple or integer can be given.  If this is set to `None` the
            vertex will have atoms_shape as the maximum.
        :type new_value: None or int or tuple(int,...)
        """
        if new_value is None:
            self._max_atoms_per_dimension_per_core = None
        elif numpy.isscalar(new_value):
            max_atoms_int: int = int(cast(int, new_value))
            self._max_atoms_per_dimension_per_core = (max_atoms_int, )
        else:
            max_atoms_tuple: Tuple[int, ...] = cast(
                Tuple[int, ...],  new_value)
            self._max_atoms_per_dimension_per_core = max_atoms_tuple

    def set_max_atoms_per_dimension_per_core(
            self, new_value: Optional[Union[int, Tuple[int, ...]]]):
        """
        Set the maximum number of atoms per dimension per core.

        Can be used to raise or lower the maximum number of atoms per core
        or per dimension per core.

        :param new_value:
            Value to set.  If the vertex is n-dimensional where n > 1, a tuple
            of n values must be given.  If the vertex is 1 dimensional,
            a 1-tuple or integer can be given.  If this is set to `None` the
            vertex will have atoms_shape as the maximum.
        :type new_value: None or int or tuple(int,...)
        """
        self._set_max_atoms_per_dimension_per_core(new_value)
        self.__check_atoms_per_core()

    def reset(self) -> None:
        """
        Forget all machine vertices in the application vertex, and reset
        the splitter (if any).
        """
        self._machine_vertices = OrderedSet()
        if self._splitter is not None:
            self._splitter.reset_called()

    def get_machine_fixed_key_and_mask(
            self, machine_vertex: MachineVertex,
            partition_id: str) -> Optional[BaseKeyAndMask]:
        """
        Get a fixed key and mask for the given machine vertex and partition
        identifier, or `None` if not fixed (the default).

        If this doesn't return `None`, :py:meth:`get_fixed_key_and_mask`
        must also not return `None`,
        and the keys returned here must align with those such that for each
        ``key:mask`` returned here, ``key & app_mask == app_key``.  It is OK
        for this to return `None` and :py:meth:`get_fixed_key_and_mask` to
        return non-`None` if and only if there is only one machine vertex.

        :param ~pacman.model.graphs.machine.MachineVertex machine_vertex:
            A source machine vertex of this application vertex
        :param str partition_id:
            The identifier of the partition to get the key for
        :rtype: ~pacman.model.routing_info.BaseKeyAndMask or None
        """
        # pylint: disable=unused-argument
        return None

    def get_fixed_key_and_mask(
            self, partition_id: str) -> Optional[BaseKeyAndMask]:
        """
        Get a fixed key and mask for the application vertex or `None` if not
        fixed (the default).  See :py:meth:`get_machine_gixed_key_and_mask` for
        the conditions.

        :param str partition_id:
            The identifier of the partition to get the key for
        :rtype: ~pacman.model.routing_info.BaseKeyAndMask or None
        """
        # pylint: disable=unused-argument
        return None

    def add_incoming_edge(
            self, edge: ApplicationEdge, partition: ApplicationEdgePartition):
        """
        Add an edge incoming to this vertex.  This is ignored by default,
        but could be used to track incoming edges, and/or report faults.

        :param ~pacman.model.graphs.application.ApplicationEdge edge:
            The edge to add.
        :param partition: The partition to add the edge to.
        :type partition:
            ~pacman.model.graphs.application.ApplicationEdgePartition
        """

    def get_key_ordered_indices(self, indices=None):
        """
        Get indices of the vertex in the order that atoms appear when the
        vertex is split into cores as determined by max_atoms_per_core.  When
        a multi-dimensional vertex is split into cores, the atoms on each
        vertex is not linear but rather a hyper-rectangle of the atoms, thus
        the order of the atoms in the vertex as a whole is not the same as the
        order of the vertex when scanning over the cores.

        :param indices:
            Optional subset of indices to convert.  If not provided all indices
            will be converted.
        :type indices: numpy.ndarray or None.
        :rtype: numpy.ndarray
        """
        if indices is None:
            indices = numpy.arange(self.n_atoms)
        atoms_shape = self.atoms_shape
        n_dims = len(atoms_shape)
        if n_dims == 1:
            return indices
        atoms_per_core = self.get_max_atoms_per_dimension_per_core()
        remainders = numpy.array(indices)
        cum_per_core = 1
        cum_cores_per_dim = 1
        core_index = numpy.zeros(len(indices))
        atom_index = numpy.zeros(len(indices))
        for n in range(n_dims):
            # Work out the global index in this dimension
            global_index_d = remainders % atoms_shape[n]

            # Work out the core index in this dimension
            core_index_d = global_index_d // atoms_per_core[n]

            # Update the core index by multiplying the current value by the
            # last dimension size and then add the current dimension value
            core_index += core_index_d * cum_cores_per_dim

            # Work out the atom index on the core in this dimension
            atom_index_d = global_index_d - (atoms_per_core[n] * core_index_d)

            # Update the atom index by multiplying the current value by the
            # last dimension size and then add the current dimension value
            atom_index += atom_index_d * cum_per_core

            # Update the remainders for next time based on the values in
            # this dimension, and save the sizes for this dimension
            remainders = remainders // atoms_shape[n]
            cum_per_core *= atoms_per_core[n]
            cum_cores_per_dim *= atoms_shape[n] / atoms_per_core[n]

        return ((core_index * self.get_max_atoms_per_core()) +
                atom_index).astype(numpy.uint32)

    def get_raster_ordered_indices(self, indices):
        """
        Convert indices from key order to raster order.

        :param numpy.ndarray indices: The key-ordered indices to convert.
        :rtype: numpy.ndarray
        """
        atoms_shape = self.atoms_shape
        n_dims = len(atoms_shape)
        if n_dims == 1:
            return indices
        atoms_per_core = self.get_max_atoms_per_dimension_per_core()
        cores_per_dim = numpy.divide(atoms_shape, atoms_per_core)
        cum_size = 1
        global_index = numpy.zeros(len(indices))

        # Work out the core indices and core-based atom indices
        core_index_remainders = indices // self.get_max_atoms_per_core()
        atom_index_remainders = indices % self.get_max_atoms_per_core()

        for n in range(n_dims):
            # Work out the core index and atom index in this dimension
            core_index_d = core_index_remainders % cores_per_dim[n]
            atom_index_d = atom_index_remainders % atoms_per_core[n]

            # Use these to work out the global index in this dimension
            global_index_d = (core_index_d * atoms_per_core[n]) + atom_index_d

            # Update the global index with this dimension
            global_index += global_index_d * cum_size

            # Update the remainders and sizes for the next loop run
            core_index_remainders = core_index_remainders // cores_per_dim[n]
            atom_index_remainders = atom_index_remainders // atoms_per_core[n]
            cum_size *= atoms_shape[n]

        return global_index.astype(numpy.uint32)

    def has_fixed_location(self):
        """
        Check if this vertex or any machine vertex has a fixed location.

        :rtype: bool
        :returns: True if the Application Vertex or any one of its
        Machine Vertices has a fixed location
        False if None of the Vertices has a none None fixed location
        """
        if self.get_fixed_location() is not None:
            return True
        for vertex in self._machine_vertices:
            if vertex.get_fixed_location() is not None:
                return True
        return False
