import networkx as nx
from networkx.algorithms.dag import topological_sort


# from joblib import Memory


# FIXME: Eventualmente memorizzare con joblib


class OperationHandler:
    """ Executes a DAG """

    def __init__(self, graph: nx.DiGraph):
        self.graph: nx.DiGraph = graph
        # self.__memoryContext = Memory(cachedir='/tmp', verbose=1)

    def execute(self):
        import data_preprocessor.flow as flow

        operation: flow.OperationNode
        for operation in topological_sort(self.graph):
            result = operation.compute()
            for child in self.graph.successors(operation):
                child.addInputArgument(result)
