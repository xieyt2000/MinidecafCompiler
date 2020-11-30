import abc
from typing import List


class MiniDecafType(abc.ABC):
    @abc.abstractmethod
    def __init__(self, name):
        self.name = name

    @abc.abstractmethod
    def __eq__(self, other):
        pass

    @abc.abstractmethod
    def get_size(self):
        pass


class NoType(MiniDecafType):
    def get_size(self):
        raise Exception('Cannot get size of NoType.')

    def __init__(self):
        super().__init__("NoType")

    def __eq__(self, other):
        return isinstance(other, NoType)


class IntType(MiniDecafType):
    def get_size(self):
        return 4

    def __init__(self):
        super().__init__("IntType")

    def __eq__(self, other):
        return isinstance(other, IntType)


class FuncType:
    para_types: List[MiniDecafType]
    ret_type: MiniDecafType

    def __init__(self, ret_type, para_types):
        self.ret_type = ret_type
        self.para_types = para_types

    def __eq__(self, other):
        """
        :type other: FuncType
        """
        return (isinstance(other, FuncType) and
                self.ret_type == other.ret_type and
                self.para_types == other.para_types)
