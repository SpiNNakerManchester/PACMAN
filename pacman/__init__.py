""" Provides various functions which together can be used to take a graph and\
    split it into pieces that can be loaded on to a machine, along with\
    routes between the pieces.\
    The main items provided are:
    
        * :py:class:`pacman.operations.partitioner.Partitioner`
        * :py:class:`pacman.operations.placer.Placer`
        * :py:class:`pacman.operations.routing_info_allocator.RoutingInfoAllocator`
        * :py:class:`pacman.operations.router.Router`
    
    Functional Requirements
    =======================
    
        * Creation of a graph of vertices to be partitioned, and edges\
          between the vertices indicating a directional communication between\
          the vertices.
            
            * Vertices will have a number of *atoms* - an atom cannot be\
              broken down in to anything smaller, and so each partitioned\
              vertex (sub-vertex) must contain at least 1 atom.
              
            * Vertices must be able to indicate what resources are required by\
              any given subset of the atoms.
            
            * A vertex can have a number of constraints which must be respected\
              by any algorithm which uses the graph.  Initially, these will\
              include:
              
                  * The maximum number of atoms which any sub-vertex can\
                    contain.
                  
                  * The chip and/or processor on to which the vertex should\
                    be placed.
                
                  * A set of vertices which should contain the same number of\
                    atoms after partitioning.
                    
                  * A set of vertices whose sub-vertices should be placed on\
                    the same chip if they contain the same atom.
                    
                  * A exact number of equal sized sub-vertices into which a\
                    vertex should be partitioned. 
                    
                  * The range of processors on a specific chip on to which the\
                    sub-vertices of the vertex should be placed.
            
            * It should be possible to create new constraints as the need\
              arises
              
            * An edge should provide functionality to create sub-edges of the\
              edge, to allow extensions of an edge and/or a sub-edge to\
              contain additional information about the edge and/or sub-edge
              
            * Multiple edges can exist between the same two vertices.
              
        * Creation of a subgraph of sub-vertices to be placed and/or routed,\
          with sub-edges between the sub-vertices. 
            
            * It must be possible to build this subgraph directly without\
              requiring that it is created by one of the other modules.
              
            * It is *not* required that there is a sub-edge between every pair\
              of sub-vertices with the same vertex.
              
            * Where a subgraph is created from a graph, it should be possible\
              to find the sub-vertices of a given vertex, and the sub-edges of\
              a given edge.
            
            * The subgraph does not have to reference a graph if it was not\
              created from a graph, and similarly the sub-vertices do not have\
              to reference a vertex, nor do the sub-edges have to reference an\
              edge.
              
            * A sub-vertex can have a number of constraints which must be\
              respected by any algorithm which uses the subgraph.
              
            * It should be possible to remove a sub-edge from a subgraph, to\
              allow later pruning of a subgraph that has been created\
              automatically from a graph.
              
            * Multiple sub-edges can exist between any two sub-vertices.
              
        * Creation of multicast routing info consisting of key/mask\
          combinations assigned to sub-edges of a given subgraph.
            
            * It must be possible to build this information directly without\
              requiring that it is created by one of the other modules.
              
            * There should be exactly one key/mask combination for each\
              sub-edge in the subgraph, which will represent all the keys\
              which will be sent in all packets from the sub-vertex at the\
              start of the sub-edge down that sub-edge.
              
            * It is possible for a sub-vertex to send several different keys\
              down several different sub-edges, but only one per sub-edge (but\
              note that it is acceptable for different keys to be assigned to\
              different sub-edges between the same two sub-vertices).
              
            * There should be no overlap between the key/mask combinations\
              of sub-edges which come from different sub-vertices i.e. no\
              two sub-edges which start at different sub-vertices should have\
              the same key/mask combination.
            
        * Partitioning of a graph with respect to a machine, such that the\
          resources consumed by each sub-vertex does not exceed those\
          provided by each processor on the machine.  This results in a\
          subgraph.
          
            * It should be possible to select from a range of partitioning\
              algorithms or provide one, although a default should be provided\
              in the absence of such a choice .
          
            * Any partitioning constraints should be met; if there are any\
              that cannot, or that are not understood by the algorithm in use\
              an exception should be thrown.  Non-partitioning constraints can\
              be ignored, although these can be used if it makes sense for\
              the given algorithm.
              
            * It should be possible to create at least one grouping of the\
              generated sub-vertices so that each group fits within the\
              resources provided by a single chip on the machine.
              
            * It should not be assumed that a given grouping of sub-vertices\
              will be the final grouping on the machine, although it is\
              acceptable to make hints through additional constraints about\
              what is likely to work.
              
            * The machine itself should not be altered by the partitioning, so\
              that it can be used in further processing.
              
            * The graph itself should not be altered by the partitioning, so\
              that it can be used in further processing.
                
            * No two sub-vertices created from a single vertex should contain\
              the same atom.
            
            * Any edges in the graph should be split with the vertices to\
              create a number of sub-edges, such that where there was a vertex\
              *v* connected to a vertex *w* by a single edge, there should be\
              a sub-edge between every sub-vertex of vertex *v* and every\
              sub-vertex of vertex *w*; for example, if there are 2\
              sub-vertices of *v* and *w*, and one edge between them, then\
              there will be 4 new sub-edges for this edge.
              
        * Placement of a subgraph on a given machine, such that the resources\
          required by any combination of sub-vertices placed on any chip in the\
          machine does not exceed the resources provided by that chip.  This\
          results in placements.
          
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
              
            * The subgraph itself should not be altered by placement so that\
              it can be used in further processing.
              
            * The returned placements should only contain a single placement\
              for each sub-vertex.
              
            * The placements should be such that the sub-vertices with\
              sub-edges between them must be able to communicate with each\
              other.
              
        * Allocation of multicast routing keys and masks to a subgraph such\
          that each sub-vertex sends out packets with a different key/mask\
          combination.  This results in multicast routing info.
          
            * This can use the placement information if required.  If an\
              algorithm requires placement information but none is provided\
              an exception is thrown.
              
        * Routing of sub-edges between sub-vertices with a given allocation of\
          routing keys and masks with respect to a given machine.  This results\
          in multicast routing tables.
        
            * It should be possible to choose from a range of routing\
              algorithms, or provide one, although a default should be provided\
              in the absence of such a choice
              
            * For any sub-vertex, following the routes from the placement of\
              the sub-vertex should result exactly in the set of placements of\
              the destination sub-vertices described by all the sub-edges which\
              start at that sub-vertex. No additional destination should be\
              reached, and no fewer than this set of destinations should be\
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
          should not iterate through a list of such objects, but should instead\
          maintain a mapping that allows access to such objects in O(1) time.\
          If this is not possible, *obj* should only provide access to a list\
          of *subobj* objects, allowing the caller to filter these themselves.\
          This will ensure that no misunderstanding can be made about the\
          speed of operation of a function.
        
    Use Cases
    =========
    
        * All the algorithms are used to take a simulation specified as a\
          :py:class:`~pacman.model.graph.graph.Graph` and ensure that each\
          :py:class:`~pacman.model.graph.vertex.Vertex` can be divided so that
          it can fit within the resources provided by a given machine, and\
          create routing tables to ensure that data is sent along each\
          specified :py:class:`~pacman.model.graph.edge.Edge` as requested, and\
          that no stray traffic should be received.   This is used to generate\
          data for a simulation which is then run on the machine.
        
        * A subset of the algorithms are used to take a pre-defined\
          :py:class:`~pacman.model.subgraph.subgraph.Subgraph` and pre-defined\
          :py:class:`~pacman.model.routing_info.routing_info.RoutingInfo`, and\
          generate :py:class:`~pacman.model.placements.placements.Placements`\
          and\
          :py:class:`~pacman.model.routing_tables.multicast_routing_tables.MulticastRoutingTables`
"""