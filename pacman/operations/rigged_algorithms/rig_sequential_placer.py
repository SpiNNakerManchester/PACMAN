"""A flexible greedy sequential placement algorithm, translated from RIG."""

from itertools import cycle

from six import next

#from rig.place_and_route.constraints import \
#    LocationConstraint, ReserveResourceConstraint
from pacman.model.placements import Placement