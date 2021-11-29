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


class PacmanException(Exception):
    """ Indicates a general exception from Pacman
    """


class PacmanInvalidParameterException(PacmanException):
    """ An exception that indicates that a parameter has an invalid value.
    """

    def __init__(self, parameter, value, problem):
        """
        :param str parameter: The name of the parameter
        :param str value: The value of the parameter
        :param str problem: The problem with the value of the parameter
        """
        super().__init__(problem)
        self.parameter = parameter
        self.value = value


class PacmanAlreadyExistsException(PacmanException):
    """ An exception that indicates that something already exists and that
        adding another would be a conflict.
    """

    def __init__(self, item_type, item_id):
        """
        :param str item_type: The type of the item that already exists
        :param str item_id: The ID of the item which is in conflict
        """
        super().__init__("{}({}) already exists".format(item_type, item_id))
        self.item_type = item_type
        self.item_id = item_id


class PacmanPartitionException(PacmanException):
    """ An exception that indicates that something went wrong with partitioning
    """


class PacmanPlaceException(PacmanException):
    """ An exception that indicates that something went wrong with placement
    """


class PacmanPruneException(PacmanException):
    """ An exception that indicates that something went wrong with pruning
    """


class PacmanRouteInfoAllocationException(PacmanException):
    """ An exception that indicates that something went wrong with route info
        allocation.
    """


class PacmanElementAllocationException(PacmanException):
    """ An exception that indicates that something went wrong with element
        allocation.
    """


class PacmanRoutingException(PacmanException):
    """ An exception that indicates that something went wrong with routing.
    """


class PacmanConfigurationException(PacmanException):
    """ An exception that indicates that something went wrong with
        configuring some part of PACMAN.
    """


class PacmanNotExistException(PacmanException):
    """ An exception that indicates that a routing table entry was attempted
        to be removed from a routing table which didn't have such an entry.
    """


class PacmanExternalAlgorithmFailedToCompleteException(PacmanException):
    """ An exception that indicates that an algorithm ran from outside
        the software stack has failed to complete for some unknown reason.
    """


class PacmanAlgorithmFailedToGenerateOutputsException(PacmanException):
    """ An exception that indicates that an algorithm has not generated the
        correct outputs for some unknown reason.
    """


class PacmanAlreadyPlacedError(ValueError):
    """ An exception that indicates multiple placements are being made for a
        vertex.
    """


class PacmanNotPlacedError(KeyError):
    """ An exception that indicates no placements are made for a vertex.
    """


class PacmanProcessorAlreadyOccupiedError(ValueError):
    """ An exception that indicates multiple placements are being made to a
        processor.
    """


class PacmanProcessorNotOccupiedError(KeyError):
    """ An exception that indicates that no placement has been made to a
        processor.
    """


class PacmanValueError(ValueError, PacmanException):
    """ An exception that indicates that a value is invalid for some reason.
    """


class PacmanNotFoundError(KeyError, PacmanException):
    """ An exception that indicates that some object has not been found when
        requested.
    """


class PacmanTypeError(TypeError, PacmanException):
    """ An exception that indicates that an object is of incorrect type.
    """


class PacmanNoMergeException(PacmanException):
    """ An exception that indicates to indicate that there are no merges worth
        performing.
    """


class PacmanCanNotFindChipException(PacmanException):
    """ An exception that indicates the chip was not in the list of chips.
    """


class MachineHasDisconnectedSubRegion(PacmanException):
    """ Some part of the machine has no paths connecting it to the rest of the
        machine.
    """


class SDRAMEdgeSizeException(PacmanException):
    """ raised when a constant SDRAM partition discovers its edges have\
    inconsistent size requests
    """


class PartitionMissingEdgesException(PacmanException):
    """
    Raise when after partitioning a partition does h=not have the edges it \
    expects
    """


class MinimisationFailedError(PacmanException):
    """ Raised when a routing table could not be minimised to reach a
        specified target.
    """


class GraphFrozenException(PacmanException):
    """
    Raise when an attempt is made to update a frozen graph
    """
