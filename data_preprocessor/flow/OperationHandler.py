import networkx as nx
from networkx.algorithms.dag import topological_sort

# FIXME: Eventualmente memorizzare con joblib
from data_preprocessor.flow.OperationDag import OperationDag


# from joblib import Memory


class OperationHandler:
    """ Executes a DAG """

    def __init__(self, graph: OperationDag):
        self.graph: nx.DiGraph = graph.getNxGraph()
        # self.__memoryContext = Memory(cachedir='/tmp', verbose=1)

    def execute(self):
        import data_preprocessor.flow as flow

        node_id: int
        child: int
        for node_id in topological_sort(self.graph):
            # Get node by id
            node: flow.OperationNode = self.graph.nodes[node_id]['op']
            # Compute result (with input)
            result = node.compute()
            # Clear eventual input, since now I have result
            node.clearInputArgument()
            # Add result as input to children
            for child_id in self.graph.successors(node_id):
                child: flow.OperationNode = self.graph.nodes[child_id]['op']
                child.addInputArgument(result, op_id=node_id)
            # Delete result (will live only in children)
            del result
