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

#from rig.place_and_route.place.utils import \
#    subtract_resources, overallocated, \
#    apply_reserve_resource_constraint, apply_same_chip_constraints, \
#    finalise_same_chip_constraints
from pacman.model.graphs.machine import machine_vertex
#Rig seems to allocate resources differently to (read: in a much more slapdash
#way than) PACMAN. Might be one of the reasons it's faster? Let's see what
#happens if we twist it to work with PACMAN's resource tracker.


class RigSequentialPlacer(object):
