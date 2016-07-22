from pacman.utilities import rig_converters
from rig.place_and_route.place.sa import place
from rig.place_and_route.allocate.greedy import allocate
from rig.place_and_route.route.ner import route
from spinn_machine.utilities.progress_bar import ProgressBar


class RigPlaceAndRoute(object):
    """ Performs placement and routing using rig algorithms; both are done\
        to save conversion time
    """

    def __call__(self, machine_graph, machine):
        progress_bar = ProgressBar(9, "Placing and Routing")

        vertices_resources, nets, net_names = \
            rig_converters.convert_to_rig_graph(
                machine_graph)
        progress_bar.update()

        rig_machine = rig_converters.convert_to_rig_machine(machine)
        progress_bar.update()

        rig_constraints = rig_converters.create_rig_machine_constraints(
            machine)
        progress_bar.update()

        rig_constraints.extend(
            rig_converters.create_rig_graph_constraints(
                machine_graph, rig_machine))
        progress_bar.update()

        rig_placements = place(
            vertices_resources, nets, rig_machine, rig_constraints)
        progress_bar.update()

        rig_allocations = allocate(
            vertices_resources, nets, rig_machine, rig_constraints,
            rig_placements)
        progress_bar.update()

        rig_routes = route(
            vertices_resources, nets, rig_machine, rig_constraints,
            rig_placements, rig_allocations, "cores")
        rig_routes = {
            name: rig_routes[net] for net, name in net_names.iteritems()}
        progress_bar.update()

        placements = rig_converters.convert_from_rig_placements(
            rig_placements, rig_allocations, machine_graph)
        progress_bar.update()
        routes = rig_converters.convert_from_rig_routes(
            rig_routes, machine_graph)
        progress_bar.update()
        progress_bar.end()

        return placements, routes
