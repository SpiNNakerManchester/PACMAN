class ResourceContainer(object):
    """ A container of resources that might be used by a vertex in a graph
    """

    def __init__(self, resources):
        """

        :param resources: The resources used
        :type resources: list of AbstractResource

        """

        # Store the resources by class of resource
        self._resources = {
            resource.__class__: resource for resource in resources
        }

    def get_resource_by_type(self, resource_type):
        """ Get a resource based on the type of the resource
        """
        if resource_type in self._resources:
            return self._resources[resource_type]
        return None

    def __getitem__(self, resource_type):
        return self.get_resource_by_type[resource_type]
