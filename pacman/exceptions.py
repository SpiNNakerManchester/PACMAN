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

import traceback


class PacmanException(Exception):
    """ Indicates a general exception from Pacman
    """


class PacmanInvalidParameterException(PacmanException):
    """ An exception that indicates that a parameter has an invalid value.
    """

    def __init__(self, parameter, value, problem):
        """
        :param parameter: The name of the parameter
        :type parameter: str
        :param value: The value of the parameter
        :type value: str
        :param problem: The problem with the value of the parameter
        :type problem: str
        """
        super(PacmanInvalidParameterException, self).__init__(
            parameter, value, problem)


class PacmanAlreadyExistsException(PacmanException):
    """ An exception that indicates that something already exists and that\
        adding another would be a conflict.
    """

    def __init__(self, item_type, item_id):
        """
        :param item_type: The type of the item that already exists
        :type item_type: str
        :param item_id: The ID of the item which is in conflict
        :type item_id: str
        """
        super(PacmanAlreadyExistsException, self).__init__(item_type, item_id)


class PacmanPartitionException(PacmanException):
    """ An exception that indicates that something went wrong with partitioning
    """

    def __init__(self, problem):
        """
        :param problem: The problem with the partitioning
        :type problem: str
        """
        super(PacmanPartitionException, self).__init__(problem)


class PacmanPlaceException(PacmanException):
    """ An exception that indicates that something went wrong with placement
    """

    def __init__(self, problem):
        """
        :param problem: The problem with the placement
        :type problem: str
        """
        super(PacmanPlaceException, self).__init__(problem)


class PacmanPruneException(PacmanException):
    """ An exception that indicates that something went wrong with pruning
    """

    def __init__(self, problem):
        """
        :param problem: The problem with the pruning
        :type problem: str
        """
        super(PacmanPruneException, self).__init__(problem)


class PacmanRouteInfoAllocationException(PacmanException):
    """ An exception that indicates that something went wrong with route info\
        allocation.
    """

    def __init__(self, problem):
        """
        :param problem: The problem with the allocation
        :type problem: str
        """
        super(PacmanRouteInfoAllocationException, self).__init__(problem)


class PacmanElementAllocationException(PacmanException):
    """ An exception that indicates that something went wrong with element\
        allocation.
    """

    def __init__(self, problem):
        """
        :param problem: The problem with the allocation
        :type problem: str
        """
        super(PacmanElementAllocationException, self).__init__(problem)


class PacmanRoutingException(PacmanException):
    """ An exception that indicates that something went wrong with routing.
    """

    def __init__(self, problem):
        """
        :param problem: The problem with the routing
        :type problem: str
        """
        super(PacmanRoutingException, self).__init__(problem)


class PacmanConfigurationException(PacmanException):
    """ An exception that indicates that something went wrong with \
        configuring some part of pacman.
    """

    def __init__(self, problem):
        """
        :param problem: The problem with the routing
        :type problem: str
        """
        super(PacmanConfigurationException, self).__init__(problem)


class PacmanNotExistException(PacmanException):
    """ An exception that indicates that a routing table entry was attempted\
        to be removed from a routing table which didn't have such an entry.
    """

    def __init__(self, problem):
        """
        :param problem: The problem with the routing
        :type problem: str
        """
        super(PacmanNotExistException, self).__init__(problem)


class PacmanAlgorithmFailedToCompleteException(PacmanException):
    """ An exception that indicates that a pacman algorithm ran from inside\
        the software stack has failed to complete for some unknown reason.
    """

    def __init__(self, algorithm, exception, tb):
        problem = (
            "Algorithm {} has crashed.\n"
            "    Inputs: {}\n"
            "    Error: {}\n"
            "    Stack: {}\n".format(
                algorithm.algorithm_id, algorithm.inputs, exception.message,
                traceback.format_exc(tb)))

        super(PacmanAlgorithmFailedToCompleteException, self).__init__(problem)
        self._exception = exception
        self._algorithm = algorithm
        self._traceback = tb

    @property
    def traceback(self):
        """ The traceback of the exception that caused this exception
        """
        return self._traceback

    @property
    def exception(self):
        """ The exception that caused this exception
        """
        return self._exception

    @property
    def algorithm(self):
        """ The algorithm that raised the exception
        """
        return self._algorithm


class PacmanExternalAlgorithmFailedToCompleteException(PacmanException):
    """ An exception that indicates that an algorithm ran from outside\
        the software stack has failed to complete for some unknown reason.
    """


class PacmanAlgorithmFailedToGenerateOutputsException(PacmanException):
    """ An exception that indicates that an algorithm has not generated the\
        correct outputs for some unknown reason.
    """


class PacmanAlreadyPlacedError(ValueError):
    """ An exception that indicates multiple placements are being made for a\
        vertex.
    """


class PacmanNotPlacedError(KeyError):
    """ An exception that indicates no placements are made for a vertex.
    """


class PacmanProcessorAlreadyOccupiedError(ValueError):
    """ An exception that indicates multiple placements are being made to a\
        processor.
    """


class PacmanProcessorNotOccupiedError(KeyError):
    """ An exception that indicates that no placement has been made to a\
        processor.
    """


class PacmanProcessorNotAvailableError(PacmanException):
    """ An exception that indicates that a processor is unavailable for some\
        reason.
    """

    def __init__(self, x, y, p):
        msg = "The processor {} {} {} is not available. " \
              "This may be caused by a clash between a ChipAndCoreConstraint"\
              " and the processor still being in use from a previous run." \
              .format(x, y, p)
        # Call the base class constructor with the parameters it needs
        super(PacmanProcessorNotAvailableError, self).__init__(msg)


class PacmanValueError(ValueError, PacmanException):
    """ An exception that indicates that a value is invalid for some reason.
    """


class PacmanNotFoundError(KeyError, PacmanException):
    """ An exception that indicates that some object has not been found when\
        requested.
    """


class PacmanTypeError(TypeError, PacmanException):
    """ An exception that indicates that an object is of incorrect type.
    """


class PacmanNoMergeException(PacmanException):
    """ An exception that indicates to indicate that there are no merges worth\
        performing.
    """


class PacmanCanNotFindChipException(PacmanException):
    """ An exception that indicates the chip was not in the list of chips.
    """
    def __init__(self, problem):
        """
        :param problem: The problem with the partitioning
        :type problem: str
        """
        super(PacmanCanNotFindChipException, self).__init__(problem)


class MachineHasDisconnectedSubRegion(PacmanException):
    """Some part of the machine has no paths connecting it to the rest of the
    machine.
    """
    pass


class SDRAMEdgeSizeException(PacmanException):
    """ raised when a constant SDRAM partition discovers its edges have\
    inconsistent size requests
    """


class MinimisationFailedError(PacmanException):
    """Raised when a routing table could not be minimised to reach a specified
    target.

    Attributes
    ----------
    target_length : int
        The target number of routing entries.
    final_length : int
        The number of routing entries reached when the algorithm completed.
        (final_length > target_length)
    chip : (x, y) or None
        The coordinates of the chip on which routing table minimisation first
        failed. Only set when minimisation is performed across many chips
        simultaneously.
    """

    def __init__(self, target_length, final_length=None, chip=None):
        self.chip = chip
        self.target_length = target_length
        self.final_length = final_length

    def __str__(self):
        if self.chip is not None:
            x, y = self.chip
            text = ("Could not minimise routing table for "
                    "({}, {}) ".format(x, y))
        else:
            text = "Could not minimise routing table "

        text += "to fit in {} entries.".format(self.target_length)

        if self.final_length is not None:
            text += " Best managed was {} entries.".format(self.final_length)

        return text
