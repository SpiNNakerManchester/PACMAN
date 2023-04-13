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
    """
    Indicates a general exception from Pacman.
    """


class PacmanInvalidParameterException(PacmanException):
    """
    A parameter has an invalid value.
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
    """
    Something already exists and that adding another would be a conflict.
    """

    def __init__(self, item_type, item_id):
        """
        :param str item_type: The type of the item that already exists
        :param str item_id: The ID of the item which is in conflict
        """
        super().__init__(f"{item_type}({item_id}) already exists")
        self.item_type = item_type
        self.item_id = item_id


class PacmanPartitionException(PacmanException):
    """
    Something went wrong with partitioning.
    """


class PacmanPlaceException(PacmanException):
    """
    Something went wrong with placement.
    """


class PacmanTooBigToPlace(PacmanException):
    """
    What is requested to place on a Singkle Chip is too big
    """


class PacmanPruneException(PacmanException):
    """
    Something went wrong with pruning.
    """


class PacmanRouteInfoAllocationException(PacmanException):
    """
    Something went wrong with route info allocation.
    """


class PacmanElementAllocationException(PacmanException):
    """
    Something went wrong with element allocation.
    """


class PacmanRoutingException(PacmanException):
    """
    Something went wrong with routing.
    """


class PacmanConfigurationException(PacmanException):
    """
    Something went wrong with configuring some part of PACMAN.
    """


class PacmanNotExistException(PacmanException):
    """
    A routing table entry was attempted
    to be removed from a routing table which didn't have such an entry.
    """


class PacmanExternalAlgorithmFailedToCompleteException(PacmanException):
    """
    An algorithm ran from outside
    the software stack has failed to complete for some unknown reason.
    """


class PacmanAlgorithmFailedToGenerateOutputsException(PacmanException):
    """
    An algorithm has not generated the correct outputs for some unknown reason.
    """


class PacmanAlreadyPlacedError(ValueError):
    """
    Multiple placements are being made for a vertex.
    """


class PacmanNotPlacedError(KeyError):
    """
    No placements are made for a vertex.
    """


class PacmanProcessorAlreadyOccupiedError(ValueError):
    """
    Multiple placements are being made to a processor.
    """


class PacmanProcessorNotOccupiedError(KeyError):
    """
    No placement has been made to a processor.
    """


class PacmanValueError(ValueError, PacmanException):
    """
    A value is invalid for some reason.
    """


class PacmanNotFoundError(KeyError, PacmanException):
    """
    Some object has not been found when requested.
    """


class PacmanTypeError(TypeError, PacmanException):
    """
    An object is of incorrect type.
    """


class PacmanNoMergeException(PacmanException):
    """
    There are no merges worth performing.
    """


class PacmanCanNotFindChipException(PacmanException):
    """
    The chip was not in the list of chips.
    """


class MachineHasDisconnectedSubRegion(PacmanException):
    """
    Some part of the machine has no paths connecting it to the rest of the
    machine.
    """


class SDRAMEdgeSizeException(PacmanException):
    """
    A constant SDRAM partition has discovered its edges have
    inconsistent size requests.
    """


class PartitionMissingEdgesException(PacmanException):
    """
    After partitioning, a partition does not have the edges it expects.
    """


class MinimisationFailedError(PacmanException):
    """
    A routing table could not be minimised to reach a specified target.
    """
