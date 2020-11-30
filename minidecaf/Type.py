from typing import List


class MiniDecafType:
    def __init__(self, name):
        self.name = name


class NoType(MiniDecafType):
    def __init__(self):
        super().__init__("NoType")

    def __eq__(self, other):
        return isinstance(other, NoType)


class IntType(MiniDecafType):
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
