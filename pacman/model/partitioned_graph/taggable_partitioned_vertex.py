from pacman.model.partitioned_graph.partitioned_vertex import \
    PartitionedVertex
from pacman.exceptions import PacmanTagAllocationException

import logging


logger = logging.getLogger(__name__)

class TaggablePartitionedVertex(PartitionedVertex):
    """ Represents a sub-set of atoms from a AbstractConstrainedVertex
    """

    def __init__(self, resources_required, label, constraints=None):
        """
        :param resources_required: The approximate resources needed for
                                   the vertex
        :type resources_required:
        :py:class:`pacman.models.resources.resource_container.ResourceContainer`
        :param label: The name of the subvertex
        :type label: str
        :param constraints: The constraints of the subvertex
        :type constraints: iterable of\
                    :py:class:`pacman.model.constraints.abstract_constraint\
                    .AbstractConstraint`
        :raise pacman.exceptions.PacmanInvalidParameterException:
                    * If one of the constraints is not valid
        """
        PartitionedVertex.__init__(self, resources_required=resources_required,
                                   label=label, constraints=constraints)
        self._ip_tags = None
        self._reverse_ip_tags = None

    @property
    def ip_tags(self):
        """The IP tags that have been allocated to this vertex

        :return: The IP tags allocated to the vertex
        :rtype:
        :py:class:`pacman.models.resources.resource_container.ResourceContainer`
        :raise pacman.exceptions.TagAllocationException:
                    * if no tags have been allocated
        """
        if self._ip_tags is None:
           raise PacmanTagAllocationException("IP Tags requested but none \
                 allocated for vertex %s" % self._label)
        else: return self._ip_tags

    @property
    def reverse_ip_tags(self):
        """The reverse IP tags that have been allocated to this vertex

        :return: The reverse IP tags allocated to the vertex
        :rtype:
        :py:class:`pacman.models.resources.resource_container.ResourceContainer`
        :raise pacman.exceptions.TagAllocationException:
                    * if no tags have been allocated
        """
        if self._reverse_ip_tags is None:
           raise PacmanTagAllocationException("Reverse IP Tags requested but \
                 none allocated for vertex %s" % self._label)
        else: return self._reverse_ip_tags  

    def add_ip_tag(self, tag):
        if self._ip_tags is None:
           self._ip_tags = [tag]
        else: self._ip_tags.append(tag)

    def add_reverse_ip_tag(self, tag):
        if self._reverse_ip_tags is None:
           self._reverse_ip_tags = [tag]
        else: self._reverse_ip_tags.append(tag)
    
    @ip_tags.setter
    def ip_tags(self, tags):
        if self._ip_tags is None:
           self._ip_tags = tags
        else: self._ip_tags.extend(tags)

    @reverse_ip_tags.setter
    def reverse_ip_tags(self, tags):
        if self._reverse_ip_tags is None:
           self._reverse_ip_tags = tags
        else: self._reverse_ip_tags.extend(tags)
