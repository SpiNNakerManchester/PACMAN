from pacman.model.decorators.overrides import overrides
from pacman.model.graphs.abstract_virtual_vertex \
    import AbstractVirtualVertex
from pacman.model.graphs.application.abstract_application_vertex \
    import AbstractApplicationVertex
from pacman.model.resources.resource_container import ResourceContainer


class AbstractVirtualApplicationVertex(
        AbstractVirtualVertex, AbstractApplicationVertex):
    """ An application vertex that is virtual
    """

    __slots__ = ()

    @overrides(AbstractApplicationVertex.get_resources_used_by_atoms)
    def get_resources_used_by_atoms(self, vertex_slice, graph):
        return ResourceContainer()
