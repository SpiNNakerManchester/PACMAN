# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import sys
from spinn_utilities.abstract_base import AbstractBase, abstractproperty
from spinn_utilities.ordered_set import OrderedSet
from spinn_utilities.log import FormatAdapter
from pacman.exceptions import (
    PacmanConfigurationException, PacmanInvalidParameterException)
from pacman.model.graphs import AbstractVertex
logger = FormatAdapter(logging.getLogger(__file__))


class ApplicationVertex(AbstractVertex, metaclass=AbstractBase):
    """ A vertex that can be broken down into a number of smaller vertices\
        based on the resources that the vertex requires.
    """

    __slots__ = [
        # List of machine verts associated with this app vertex
        "_machine_vertices",

        # The splitter object associated with this app vertex
        "_splitter",

        # The maximun number of atoms for each core.
        # Typically all but possibly the last core will have this number
        "_max_atoms_per_core"]

    SETTING_SPLITTER_ERROR_MSG = (
        "The splitter object on {} has already been set, it cannot be "
        "reset. Please fix and try again. ")

    def __init__(self, label=None, constraints=None,
                 max_atoms_per_core=sys.maxsize, splitter=None):
        """
        :param str label: The optional name of the vertex.
        :param iterable(AbstractConstraint) constraints:
            The optional initial constraints of the vertex.
        :param int max_atoms_per_core: The max number of atoms that can be
            placed on a core, used in partitioning.
        :param splitter: The splitter object needed for this vertex.
            Leave as None to delegate the choice of splitter to the selector.
        :type splitter: None or
            ~pacman.model.partitioner_interfaces.AbstractSplitterPartitioner
        :raise PacmanInvalidParameterException:
            If one of the constraints is not valid
        """
        # Need to set to None temporarily as add_constraint checks splitter
        self._splitter = None
        super().__init__(label, constraints)
        self._machine_vertices = OrderedSet()
        # Use setter as there is extra work to do
        self.splitter = splitter
        self._max_atoms_per_core = max_atoms_per_core

    def __str__(self):
        return self.label

    def __repr__(self):
        return "ApplicationVertex(label={}, constraints={}".format(
            self.label, self.constraints)

    @property
    def splitter(self):
        """
        :rtype:
            ~pacman.model.partitioner_interfaces.AbstractSplitterPartitioner
        """
        return self._splitter

    @splitter.setter
    def splitter(self, new_value):
        """ Sets the splitter object. Does not allow repeated settings.

        :param new_value: The new splitter object
        :type new_value:
            ~pacman.model.partitioner_interfaces.AbstractSplitterPartitioner
        :rtype: None
        """
        if self._splitter == new_value:
            return
        if self._splitter is not None:
            raise PacmanConfigurationException(
                self.SETTING_SPLITTER_ERROR_MSG.format(self._label))
        self._splitter = new_value
        self._splitter.set_governed_app_vertex(self)

    def remember_machine_vertex(self, machine_vertex):
        """
        Adds the Machine vertex the iterable returned by machine_vertices

        :param MachineVertex machine_vertex: A pointer to a machine_vertex
        """

        machine_vertex.index = len(self._machine_vertices)
        self._machine_vertices.add(machine_vertex)

    @property
    def atoms_shape(self):
        """ The "shape" of the atoms in the vertex i.e. how the atoms are split
            between the dimensions of the vertex.  By default everything is
            1-dimensional, so the return will be a 1-tuple but can be
            overridden by a vertex that supports multiple dimensions.

        :rtype: tuple(int, ...)
        """
        return (self.n_atoms,)

    @abstractproperty
    def n_atoms(self):
        """ The number of atoms in the vertex

        :rtype: int
        """

    def round_n_atoms(self, n_atoms, label="n_atoms"):
        """
        Utility function to allow suoer-classes to make sure n_atom is an int

        :param n_atoms: Value convertible to int to be used for n_atoms
        :type n_atoms: int or float or numpy.
        :return:
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
            label, n_atoms, "int value expected for {}".format(label))

    @property
    def machine_vertices(self):
        """ The machine vertices that this application vertex maps to

        :rtype: iterable(MachineVertex)
        """
        return self._machine_vertices

    def get_max_atoms_per_core(self):
        """ Gets the maximum number of atoms per core, which is either the\
            number of atoms required across the whole application vertex,\
            or a lower value set.

        :rtype: int
        """
        return self._max_atoms_per_core

    def set_max_atoms_per_core(self, new_value):
        """
        Set the max_atoms_per_core.

        Can be used to raise or lower the maximum number of atoms.

        :param int new_value: Value to set
        """
        self._max_atoms_per_core = new_value

    def reset(self):
        """ Forget all machine vertices in the application vertex, and reset
            the splitter (if any)
        """
        self._machine_vertices = OrderedSet()
        if self._splitter is not None:
            self._splitter.reset_called()

    def get_machine_fixed_key_and_mask(self, machine_vertex, partition_id):
        """ Get a fixed key and mask for the given machine vertex and partition
            identifier, or None if not fixed (the default).  If this doesn't
            return None, get_fixed_key_and_mask must also not return None,
            and the keys returned here must align with those such that for each
            key:mask returned here, key & app_mask == app_key.  It is OK for
            this to return None and get_fixed_key_and_mask to return not None
            iff there is only one machine vertex.

        :param MachineVertex machine_vertex:
            A source machine vertex of this application vertex
        :param str partition_id:
            The identifier of the partition to get the key for
        :rtype: BaseKeyAndMask or None
        """
        # pylint: disable=unused-argument
        return None

    def get_fixed_key_and_mask(self, partition_id):
        """ Get a fixed key and mask for the application vertex or None if not
            fixed (the default).  See get_machine_gixed_key_and_mask for the
            conditions.

        :param str partition_id:
            The identifier of the partition to get the key for
        :rtype: BaseKeyAndMask or None
        """
        # pylint: disable=unused-argument
        return None
