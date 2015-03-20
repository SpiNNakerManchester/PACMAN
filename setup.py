try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name="SpiNNaker_PACMAN",
    version="2015.003-alpha-03",
    description="Partition and Configuration Manager",
    url="https://github.com/SpiNNakerManchester/PACMAN",
    license="GNU GPLv3.0",
    packages=['pacman',
              'pacman.model',
              'pacman.model.abstract_classes',
              'pacman.model.constraints',
              'pacman.model.constraints.abstract_constraints',
              'pacman.model.constraints.key_allocator_constraints',
              'pacman.model.constraints.partitioner_constraints',
              'pacman.model.constraints.placer_constraints',
              'pacman.model.constraints.tag_allocator_constraints',
              'pacman.model.constraints.utility_constraints',
              'pacman.model.graph_mapper',
              'pacman.model.partitionable_graph',
              'pacman.model.partitioned_graph',
              'pacman.model.placements',
              'pacman.model.resources',
              'pacman.model.routing_info',
              'pacman.model.routing_tables',
              'pacman.model.tags',
              'pacman.operations',
              'pacman.operations.abstract_algorithms',
              'pacman.operations.partition_algorithms',
              'pacman.operations.placer_algorithms',
              'pacman.operations.router_algorithms',
              'pacman.operations.router_check_functionality',
              'pacman.operations.routing_info_allocator_algorithms',
              'pacman.operations.routing_info_allocator_algorithms.malloc_based_routing_allocator',
              'pacman.operations.tag_allocator_algorithms',
              'pacman.utilities'],
    install_requires=['six', 'enum34', 'numpy',
                      'SpiNNMachine >= 2015.003-alpha-01']
)
