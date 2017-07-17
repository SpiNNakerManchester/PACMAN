"""A flexible greedy sequential placement algorithm, translated from RIG."""

from itertools import cycle

from six import next

#from rig.place_and_route.constraints import \
#    LocationConstraint, ReserveResourceConstraint
#ignoring ReserveResourceConstraint - unnecessary functionality
from pacman.model.placements import Placement

#from rig.place_and_route.exceptions import \
#    InvalidConstraintError, InsufficientResourceError
from pacman.utilities.utility_objs import ResourceTracker