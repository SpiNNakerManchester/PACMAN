This package provides utilities for partitioning, placing a routing on a
SpiNNaker machine

Requirements
============
In addition to a standard Python installation, this package depends on:

 - six
 - enum34
 - SpiNNMachine

These requirements can be install using `pip`:

    pip install six
    pip install enum34
    pip install SpiNNMachine

User Installation
=================
If you want to install for all users, run:

    sudo pip install PACMAN

If you want to install only for yourself, run:

    pip install PACMAN --user

To install in a `virtualenv`, with the `virtualenv` enabled, run:

    pip install PACMAN

Developer Installation
======================
If you want to be able to edit the source code, but still have it referenced
from other Python modules, you can set the install to be a developer install.
In this case, download the source code, and extract it locally, or else clone
the git repository:

    git clone http://github.com/SpiNNakerManchester/PACMAN.git

To install as a development version which all users will then be able to use,
run the following where the code has been extracted:

    sudo python setup.py develop

To install as a development version for only yourself, run:

    python setup.py develop --user

To install as a development version in a `virtualenv`, with the `virutalenv`
enabled, run:

    python setup.py develop

Documentation
=============
[PACMAN python documentation](http://pacman.readthedocs.io)

[Combined python documentation](http://spinnakermanchester.readthedocs.io)