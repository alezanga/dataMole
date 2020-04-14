from data_preprocessor.operation import Operation


class InstanceOperation(Operation):
    """ Base class for operations that does not alter the columns of the frame, but only rows """
    @staticmethod
    def isOutputShapeKnown() -> bool:
        return True
