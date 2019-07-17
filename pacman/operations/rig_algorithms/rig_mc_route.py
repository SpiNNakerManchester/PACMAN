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

from six import iteritems
from spinn_utilities.progress_bar import ProgressBar
from pacman.utilities.rig_converters import (
    convert_from_rig_routes, convert_to_rig_graph_pure_mc,
    convert_to_rig_machine, convert_to_rig_placements,
    create_rig_machine_constraints, create_rig_graph_constraints)
from rig.place_and_route.route.ner import route


class RigMCRoute(object):
    """ Performs routing using rig algorithm
    """

    __slots__ = []

    def __call__(self, machine_graph, machine, plan_n_timesteps, placements):
        progress_bar = ProgressBar(7, "Routing")

        vertices_resources, nets, net_names = \
            convert_to_rig_graph_pure_mc(machine_graph, plan_n_timesteps)
        progress_bar.update()

        rig_machine = convert_to_rig_machine(machine)
        progress_bar.update()

        rig_constraints = create_rig_machine_constraints(machine)
        progress_bar.update()

        rig_constraints.extend(create_rig_graph_constraints(
            machine_graph, machine))
        progress_bar.update()

        rig_placements, rig_allocations = convert_to_rig_placements(
            placements, machine)
        progress_bar.update()

        rig_routes = route(
            vertices_resources, nets, rig_machine, rig_constraints,
            rig_placements, rig_allocations, "cores")
        rig_routes = {
            name: rig_routes[net] for net, name in iteritems(net_names)}
        progress_bar.update()

        routes = convert_from_rig_routes(rig_routes)
        progress_bar.update()
        progress_bar.end()

        return routes
