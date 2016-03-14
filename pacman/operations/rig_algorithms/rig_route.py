from pacman.utilities import rig_converters
from rig.place_and_route.route.ner import route
from spinn_machine.progress_bar import ProgressBar


class RigRoute(object):
    """ Performs routing using rig algorithm
    """

    def __call__(self, partitioned_graph, machine, placements):
        progress_bar = ProgressBar(8, "Routing")

        vertices_resources, nets, net_names = \
            rig_converters.convert_to_rig_partitioned_graph(
                partitioned_graph)
        progress_bar.update()

        rig_machine = rig_converters.convert_to_rig_machine(machine)
        progress_bar.update()

        rig_constraints = rig_converters.create_rig_machine_constraints(
            machine)
        progress_bar.update()

        rig_constraints.extend(
            rig_converters.create_rig_partitioned_graph_constraints(
                partitioned_graph, rig_machine))
        progress_bar.update()

        rig_placements, rig_allocations = \
            rig_converters.convert_to_rig_placements(placements)
        progress_bar.update()

        rig_routes = route(
            vertices_resources, nets, rig_machine, rig_constraints,
            rig_placements, rig_allocations, "cores")
        rig_routes = {
            name: rig_routes[net] for net, name in net_names.iteritems()}
        progress_bar.update()

        placements = rig_converters.convert_from_rig_placements(
            rig_placements, rig_allocations, partitioned_graph)
        progress_bar.update()
        routes = rig_converters.convert_from_rig_routes(
            rig_routes, partitioned_graph)
        progress_bar.update()
        progress_bar.end()

        return {"routing_paths": routes}
