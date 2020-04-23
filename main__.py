from abc import ABC, abstractmethod

from anytree import NodeMixin, RenderTree
from anytree.iterators import LevelOrderIter


class Operation(ABC, NodeMixin):
    def __init__(self):
        self.result = None

    def compute(self, input: str) -> None:
        self.result = self.execute(input)

    @abstractmethod
    def execute(self, input: str) -> str:
        pass

    def getOutput(self) -> str:
        return self.result


class AddId(Operation):
    def execute(self, input: str) -> str:
        return input + '_ID_'

class OutOp(Operation):
    def execute(self, input: str) -> None:
        print(input)


class AddNumber(Operation):
    def execute(self, input: str) -> str:
        return input + '_9_'


class OperationTree:
    def __init__(self):
        self.root: Operation = None

    def add(self, new: Operation, parent: Operation = None):
        if parent:
            new.parent = parent
        else:
            self.root = new

    def remove(self, op: Operation):
        for child in op.children:
            child.parent = op.parent
        if op == self.root:
            self.root = op.children[0] if op.children else None
        op.parent = None


class OperationHandler:
    def __init__(self, tree: OperationTree):
        self.tree: OperationTree = tree

    def notify(self, operation):
        pass

    def execute(self, input: str):
        for op in LevelOrderIter(self.tree.root):
            op.compute(op.parent.getOutput() if op.parent else input)
        # if self.tree:
        #     self.__rec_execute(self.tree, input)

    # @staticmethod
    # def __rec_execute(op: Operation, input):
    #     out = op.execute(input)
    #     for child_op in op.children:
    #         OperationHandler.__rec_execute(child_op, out)


if __name__ == "__main__":
    tree = OperationTree()
    add1 = AddId()
    add2 = AddNumber()
    add3 = AddNumber()
    tree.add(add1)
    tree.add(add2, add1)
    tree.add(add3, add2)
    tree.add(OutOp(), add3)
    tree.add(OutOp(), add2)
    print(RenderTree(add1))
    handler = OperationHandler(tree)
    handler.execute('I')

