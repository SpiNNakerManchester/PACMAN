try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from collections import defaultdict
import os

# Build a list of all project modules, as well as supplementary files
main_package = "pacman"
data_extensions = {".aplx", ".xml", ".json", ".xsd"}
main_package_dir = os.path.join(os.path.dirname(__file__), main_package)
start = len(main_package_dir)
packages = []
package_data = defaultdict(list)
for dirname, dirnames, filenames in os.walk(main_package_dir):
    if '__init__.py' in filenames:
        package = "{}{}".format(
            main_package, dirname[start:].replace(os.sep, '.'))
        packages.append(package)
    for filename in filenames:
        _, ext = os.path.splitext(filename)
        if ext in data_extensions:
            package = "{}{}".format(
                main_package, dirname[start:].replace(os.sep, '.'))
            package_data[package].append("*.{}".format(ext))
            break

setup(
    name="SpiNNaker_PACMAN",
    version="3.0.1",
    description="Partition and Configuration Manager",
    url="https://github.com/SpiNNakerManchester/PACMAN",
    license="GNU GPLv3.0",
    packages=packages,
    package_data=package_data,
    install_requires=[
        'SpiNNUtilities >= 3.0.0, < 4.0.0',
        'SpiNNMachine >= 3.0.0, < 4.0.0'
        'six', 'enum34', 'numpy', 'lxml', 'jsonschema',
        'rig >= 2.0.0, < 3.0.0']
)
