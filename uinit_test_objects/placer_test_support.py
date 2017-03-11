from pacman.model.graphs.application.abstract_application_vertex \
    import AbstractApplicationVertex
from pacman.model.graphs.machine.impl.simple_machine_vertex \
    import SimpleMachineVertex
from pacman.model.resources.resource_container import ResourceContainer
from pacman.model.resources.cpu_cycles_per_tick_resource \
    import CPUCyclesPerTickResource
from pacman.model.resources.dtcm_resource import DTCMResource
from pacman.model.resources.sdram_resource import SDRAMResource


def get_resources_used_by_atoms(lo_atom, hi_atom, vertex_in_edges):
    vertex = Vertex(1, None)
    cpu_cycles = vertex.get_cpu_usage_for_atoms(lo_atom, hi_atom)
    dtcm_requirement = vertex.get_dtcm_usage_for_atoms(lo_atom, hi_atom)
    sdram_requirement = vertex.get_sdram_usage_for_atoms(
        lo_atom, hi_atom, vertex_in_edges)
    # noinspection PyTypeChecker
    resources = ResourceContainer(cpu=CPUCyclesPerTickResource(cpu_cycles),
                                  dtcm=DTCMResource(dtcm_requirement),
                                  sdram=SDRAMResource(sdram_requirement))
    return resources


class Vertex(AbstractApplicationVertex):
    def __init__(self, n_atoms, label):
        AbstractApplicationVertex.__init__(self, label=label, n_atoms=n_atoms,
                                           max_atoms_per_core=256)
        self._model_based_max_atoms_per_core = 256

    def get_cpu_usage_for_atoms(self, lo_atom, hi_atom):
        return 10 * (hi_atom - lo_atom)

    def get_dtcm_usage_for_atoms(self, lo_atom, hi_atom):
        return 200 * (hi_atom - lo_atom)

    def get_sdram_usage_for_atoms(
            self, vertex_slice, graph):
        return 4000 + (50 * (vertex_slice.hi_atom - vertex_slice.lo_atom))


class MachineVertex(SimpleMachineVertex):
    def __init__(self, lo_atom, hi_atom, resources_required, label=None,
                 constraints=None):
        SimpleMachineVertex.__init__(self, lo_atom, hi_atom,
                                     resources_required, label=label,
                                     constraints=constraints)
        self._model_based_max_atoms_per_core = 256
