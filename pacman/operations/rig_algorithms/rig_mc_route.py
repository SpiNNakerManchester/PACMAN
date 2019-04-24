from six import iteritems
from spinn_utilities.progress_bar import ProgressBar
from pacman.utilities.rig_converters import (
    convert_from_rig_routes, convert_to_rig_graph_pure_mc,
    convert_to_rig_machine, convert_to_rig_placements,
    create_rig_machine_constraints, create_rig_graph_constraints)
from pacman.minirig.place_and_route.route.ner import route


class RigMCRoute(object):
    """ Performs routing using rig algorithm
    """

    __slots__ = []

    def __call__(self, machine_graph, machine, placements):
        progress_bar = ProgressBar(7, "Routing")

        vertices_resources, nets, net_names = convert_to_rig_graph_pure_mc(
            machine_graph)
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
        rig_routes2 = {
            name: rig_routes[net] for net, name in iteritems(net_names)}
        progress_bar.update()

        routes = convert_from_rig_routes(rig_routes2)
        progress_bar.update()
        progress_bar.end()

        return routes
