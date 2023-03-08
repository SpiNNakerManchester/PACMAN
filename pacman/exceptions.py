# Copyright (c) 2014 The University of Manchester
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
