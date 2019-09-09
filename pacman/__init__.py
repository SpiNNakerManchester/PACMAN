# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

""" Provides various functions which together can be used to take a graph and\
    split it into pieces that can be loaded on to a machine, along with\
    routes between the pieces.

    Functional Requirements
    =======================

        * Creation of an Application Graph of Vertices indicating points of\
          computation within the graph and Edges between the vertices\
          indicating a directional communication between the vertices;\
          and a similar Machine Graph.

            * Vertices in the Application Graph will have a number of *atoms*\
              - an atom cannot be broken down in to anything smaller.

            * Vertices in the Application Graph must be able to indicate what\
              machine resources are required by any given subset of the atoms.

            * Vertices in the Machine Graph must be able to fit on a single\
              chip of the machine in terms of resource usage.

            * A Vertex can have a number of constraints which must be\
              respected by any algorithm which uses the graph.  Algorithms\
              must check that they can support the given constraints and must\
              fail if they cannot.  Provided constraints include support for:

                  * The maximum number of atoms which any Machine Graph Vertex\
                    can contain for a given Application Graph vertex

                  * The chip and/or processor on to which a Machine Graph\
                    Vertex should be placed.

                  * A set of Application Graph Vertices whose corresponding\
                    Machine Graph vertices should contain the same number of\
                    atoms.

                  * A set of Application Graph Vertices whose corresponding\
                    Machine Graph vertices should be placed on the same chip\
                    if they contain the same atom.

            * It should be possible to create new constraints as the need\
              arises.

            * Multiple edges can exist between the same two vertices.

            * It must be possible to build the Machine Graph directly without\
              requiring that it is created by one of the other modules.

            * It is *not* required that there is a Machine Graph Edge between\
              every pair of Machine Graph Vertex from the same Application\
              Graph Vertex.

            * Where a Machine Graph is created from an Application Graph, it\
              should be possible to find the corresponding Vertices and Edges\
              from one graph to the other.

        * Creation of multicast routing info consisting of key/mask\
          combinations assigned to Edges of the Machine Graph.

            * It must be possible to build this information directly without\
              requiring that it is created by one of the other modules.

            * There should be exactly one key/mask combination for each\
              Edge in the Machine Graph, which will represent all the keys\
              which will be sent in all packets from the Vertex at the\
              start of the Edge down that Edge.

            * It is possible for a Vertex to send several different keys\
              down several different Edges, but only one per Edge (but\
              note that it is acceptable for different keys to be assigned to\
              different Edges between the same two Vertices).

            * There should be no overlap between the key/mask combinations\
              of Edges which come from different Vertices i.e. no\
              two Edges which start at different Vertices should have\
              the same key/mask combination.

        * Partitioning of an Application graph with respect to a machine, such\
          that the resources consumed by each Vertex does not exceed those\
          provided by each chip on the machine.

            * It should be possible to select from a range of partitioning\
              algorithms or provide one, although a default should be provided\
              in the absence of such a choice .

            * Any partitioning constraints should be met; if there are any\
              that cannot, or that are not understood by the algorithm in use\
              an exception should be thrown.  Non-partitioning constraints can\
              be ignored, although these can be used if it makes sense for\
              the given algorithm.

            * It must be possible to create at least one grouping of the\
              generated Vertices so that each group fits within the\
              resources provided by a single chip on the machine.

            * It should not be assumed that a given grouping of Vertices\
              will be the final grouping on the machine, although it is\
              acceptable to make hints through additional constraints about\
              what is likely to work.

            * The machine itself must not be altered by the partitioning, so\
              that it can be used in further processing.

            * The graph itself must not be altered by the partitioning, so\
              that it can be used in further processing.

            * No two Machine Graph Vertices created from a single Application\
              Graph Vertex can contain the same atom.

            * Any Edges in the Application Graph must be split with the\
              Vertices to create a number of Machine Graph edges, such that\
              where there was a vertex *v* connected to a vertex *w* by a\
              single edge in the Application Graph, there should be\
              an Edge in the Machine Graph between every Vertex of\
              Application Graph Vertex *v* and every Vertex of Application\
              Graph Vertex *w*; for example, if there are 2\
              Machine Graph Vertices for each of *v* and *w*, and one Edge\
              between them in the Application Graph, then there will be 4 \
              new Edges in the Machine Graph for this Edge.

        * Placement of a Machine Graph on a given machine, such that the\
          resources required by any combination of Vertices placed on any\
          chip in the machine does not exceed the resources provided by that\
          chip.

            * It should be possible to choose from a range of placement\
              algorithms or provide one, although a default should be provided\
              in the absence of such a choice.

            * Any placement constraints should be met; if there are any that\
              cannot, or that are not understood by placement algorithm, an\
              exception should be thrown.  Non-placement constraints can be\
              ignored, although these can be used if it makes sense for the\
              given algorithm.

            * The machine itself should not be altered by placement so that\
              it can be used in further processing.

            * The graph itself should not be altered by placement so that\
              it can be used in further processing.

            * The returned placements should only contain a single placement\
              for each vertex.

            * The placements should be such that the vertices with\
              edges between them must be able to communicate with each\
              other.

        * Allocation of multicast routing keys and masks to a Machine Graph\
          such that each vertex sends out packets with a different key/mask\
          combination.

            * This can use the placement information if required.  If an\
              algorithm requires placement information but none is provided\
              an exception is thrown.

        * Routing of edges between vertices with a given allocation of\
          routing keys and masks with respect to a given machine.

            * It should be possible to choose from a range of routing\
              algorithms, or provide one, although a default should be\
              provided in the absence of such a choice

            * For any vertex, following the routes from the placement of\
              the vertex should result exactly in the set of placements of\
              the destination vertices described by all the edges\
              which start at that vertex. No additional destination should\
              be reached, and no fewer than this set of destinations should be\
              reached.

        * It should be possible to call each of the modules independently.\
          There should be no assumption that one of the other modules has\
          produced the data input for any other module.

        * There should be no assumption about how the inputs and outputs\
          are stored.

        * Any utility functions that provide access to internal structures\
          within a data structure should operate in approximately O(1) time;\
          for example, where an object of type *obj* holds a number of objects\
          of type *subobj* with property *prop*, requesting a list of *subobj*\
          objects contained within *obj* with property value *prop* = *value*\
          should not iterate through a list of such objects, but should\
          instead maintain a mapping that allows access to such objects in\
          O(1) time. If this is not possible, *obj* should only provide access\
          to a list of *subobj* objects, allowing the caller to filter these\
          themselves. This will ensure that no misunderstanding can be made\
          about the speed of operation of a function.

"""
from pacman._version import __version__  # NOQA
from pacman._version import __version_name__  # NOQA
from pacman._version import __version_month__  # NOQA
from pacman._version import __version_year__  # NOQA
