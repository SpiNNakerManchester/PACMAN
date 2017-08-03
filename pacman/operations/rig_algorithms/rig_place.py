from pacman.utilities import rig_converters
from rig.place_and_route.place.hilbert import place
from rig.place_and_route.allocate.greedy import allocate
from spinn_utilities.progress_bar import ProgressBar
from spinn_utilities.timer import Timer


class RigPlace(object):
    """ Performs placement and routing using rig algorithms; both are done\
        to save conversion time
    """

    __slots__ = []

    def __call__(self, machine_graph, machine):
        progress_bar = ProgressBar(7, "Placing")

        vertices_resources, nets, _ = \
            rig_converters.convert_to_rig_graph(machine_graph)
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

        time = Timer()
        time.start_timing()

        rig_placements = place(
            vertices_resources, nets, rig_machine, rig_constraints)
        x = time.take_sample()
        print x
        progress_bar.update()

        rig_allocations = allocate(
            vertices_resources, nets, rig_machine, rig_constraints,
            rig_placements)
        progress_bar.update()

        placements = rig_converters.convert_from_rig_placements(
            rig_placements, rig_allocations, machine_graph)
        progress_bar.update()
        progress_bar.end()

        return placements
