[![PyPi version](https://img.shields.io/pypi/v/SpiNNaker_PACMAN.svg?style=flat)](https://pypi.org/project/SpiNNaker_PACMAN/)
[![CI Check](https://github.com/SpiNNakerManchester/PACMAN/workflows/Python%20Actions/badge.svg?branch=master)](https://github.com/SpiNNakerManchester/PACMAN/actions?query=workflow%3A%22Python+Actions%22+branch%3Amaster)
[![Documentation Status](https://readthedocs.org/projects/pacman/badge/?version=latest)](https://pacman.readthedocs.io/en/latest/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/github/SpiNNakerManchester/PACMAN/badge.svg?branch=master)](https://coveralls.io/github/SpiNNakerManchester/PACMAN?branch=master)


This package provides utilities for partitioning, placing a routing on a
SpiNNaker machine

Requirements
============
In addition to a standard Python installation, this package depends on:

 - SpiNNMachine

These requirements can be install using `pip`:

    pip install SpiNNMachine

User Installation
=================
If you want to install for all users, run:

    sudo pip install PACMAN

If you want to install only for yourself, run:

    pip install PACMAN --user

To install in a `virtualenv`, with the `virtualenv` enabled, run:

    pip install PACMAN

_Using a virtual environment is recommended for all SpiNNaker software._

Developer Installation
======================
If you want to be able to edit the source code, but still have it referenced
from other Python modules, you can set the install to be a developer install.
In this case, download the source code, and extract it locally, or else clone
the git repository:

    git clone http://github.com/SpiNNakerManchester/PACMAN.git

To install as a development version which all users will then be able to use,
run the following where the code has been extracted:

    sudo pip install -e .

To install as a development version for only yourself, run:

    pip install -e . --user

To install as a development version in a `virtualenv`, with the `virutalenv`
enabled, run:

    pip install -e .

Test Installation
=================
To be able to run the unitests add [Test] to the pip installs above

    pip install -e .[Test]

Documentation
=============
[PACMAN python documentation](http://pacman.readthedocs.io)
<br>
[Combined python documentation](http://spinnakermanchester.readthedocs.io)


PACMAN Executor
===============
PACMAN contains a simple workflow execution system which allows the user to
specify a set of available algorithms which, when provided with a set of inputs
can produce a set of outputs.  The executor will then work out the order in
which the algorithms should be run (and indeed if the algorithms *can* be run)
by looking at the inputs required and outputs generated by each algorithm.

As well as parameters required by the algorithms, the workflow system
additionally supports the concept of "tokens".  A token can be used to represent
the action of an algorithm that does not produce a specific output.  For
example, on a SpiNNaker machine, this might include the loading of data or the
loading of application binaries, neither of which produces a Python object as
output, but performs and important task in any case.  Each token can also be
specified to be "part" of a whole task.  This allows an algorithm to declare
that it has done part of a task, and have a future algorithm require that all
of the task has been completed without knowing what parts need to be done.
Again, the example of loading of data can be used here where there may be
several algorithms that can load data in different ways but all the data must
be loaded before the application binaries are loaded; however the application
binary loader can just say that all data loading is done before execution,
avoiding the need to modify the algorithm in the event that a new algorithm
is created.

The arguments of the algorithms that *can* be represented as Python objects
are specified using semantic types.  These are simply represented as strings;
the values of the strings are only important in that they must match between
the inputs and outputs of algorithms in the flow for an algorithm to be
recognised as producing an output that another algorithm can use as an input.

Each algorithm to be run by this executor specifies:
 - The required inputs of the algorithm.  This can include both arguments of
   the algorithm and tokens required.
 - The optional inputs of the algorithm, again including both arguments and
   tokens.
 - The outputs generated by the algorithm, both as semantic types and tokens.

The executor is provided with:
 - A list of algorithms that must be executed.  If it is not possible to
   execute these, an error is raised.  These will be executed regardless of
   if the output of the algorithm is already available.
 - A list of algorithms that can be executed optionally to produce an output.
   If one of these algorithms generates an input type or a partial or complete
   token that is an optional input to a required algorithm, and no other
   required algorithm can generate this input, the optional algorithm *will* be
   run before that required algorithm.  An optional algorithm will not be run
   if it doesn't generate an output which is an input for another algorithm
   which isn't already provided in some other way.
 - A list of inputs to seed the workflow with.  This can be used to provide
   initial inputs to the workflow, or to stop an optional algorithm from
   executing by providing in advance the output that the algorithm generates.
 - A list of input tokens to seed the workflow with.  These can only be
   specified as complete tokens which are provided.  Partial tokens cannot
   currently be provided.
 - A list of required outputs that the workflow must generate.  In addition
   to the list of algorithms to run, these outputs must be generated by the
   workflow at some stage, or else an error is raised.
 - A list of required output tokens that the workflow must generate.  As with
   the outputs these must be generated by the workflow at some stage or else
   an error is raised.
