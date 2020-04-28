import networkx as nx
from networkx.algorithms.dag import topological_sort


# from joblib import Memory


# FIXME: Eventualmente memorizzare con joblib
from data_preprocessor.flow.OperationDag import OperationDag


class OperationHandler:
    """ Executes a DAG """

    def __init__(self, graph: OperationDag):
        self.graph: nx.DiGraph = graph.getNxGraph()
        # self.__memoryContext = Memory(cachedir='/tmp', verbose=1)

    def execute(self):
        import data_preprocessor.flow as flow

        node: flow.OperationNode
        for node in topological_sort(self.graph):
            # Compute result (with input)
            result = node.compute()
            # Clear eventual input, since now I have result
            node.clearInputArgument()
            # Add result as input to children
            for child in self.graph.successors(node):
                child.addInputArgument(result, op_id=node.uid)
            # Delete result (will live only in children)
            del result
