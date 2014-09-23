try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name="PACMAN",
    version="0.1-SNAPSHOT",
    description="Partition and Configuration Manager",
    url="https://github.com/SpiNNakerManchester/PACMAN",
    packages=['pacman',
            'pacman.model',
            'pacman.model.constraints',
            'pacman.model.partitionable_graph',
            'pacman.model.placements',
            'pacman.model.resources',
            'pacman.model.routing_info',
            'pacman.model.routing_tables',
            'pacman.model.partitioned_graph',
            'pacman.operations',
            'pacman.operations.partition_algorithms',
            'pacman.operations.placer_algorithms',
            'pacman.operations.router_algorithms',
            'pacman.operations.routing_info_allocator_algorithms',
            'pacman.utilities'],
    install_requires=['six', 'enum34', 'SpiNNMachine']
)
