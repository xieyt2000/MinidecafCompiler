import abc
from enum import Enum
from typing import List


class ValueCategory(Enum):
    lvalue = 1
    rvalue = 2


class MiniDecafType(abc.ABC):

    def __init__(self, name, value_cat: ValueCategory = ValueCategory.rvalue):
        self.name = name
        self.value_cat = value_cat

    @abc.abstractmethod
    def __eq__(self, other):
        pass

    @abc.abstractmethod
    def get_size(self):
        pass

    @abc.abstractmethod
    def reference(self):  # &
        pass

    @abc.abstractmethod
    def dereference(self):  # *
        pass

    @abc.abstractmethod
    def value_category_cast(self, target_value_cat: ValueCategory):
        pass


class NoType(MiniDecafType):
    def reference(self):
        raise Exception('Cannot reference NoType.')

    def dereference(self):
        raise Exception('Cannot deference NoType.')

    def value_category_cast(self, target_value_cat: ValueCategory):
        return self

    def get_size(self):
        raise Exception('Cannot get size of NoType.')

    def __init__(self):
        super().__init__("NoType")

    def __eq__(self, other):
        return isinstance(other, NoType)


class PointerType(MiniDecafType):

    def __init__(self, level, value_cat=ValueCategory.rvalue):
        super().__init__(f"PointerType<{level}>", value_cat)
        self.level = level  # level of pointers == num of *

    def __eq__(self, other):
        return isinstance(other, PointerType) and self.level == other.level

    def get_size(self):
        return 4

    def reference(self):
        if self.value_cat == ValueCategory.lvalue:
            return PointerType(self.level + 1)
        raise Exception('Cannot reference rvalue pointer.')

    def dereference(self):
        if self.level > 1:
            return PointerType(self.level - 1, ValueCategory.lvalue)
        else:
            return IntType(ValueCategory.lvalue)

    def value_category_cast(self, target_value_cat: ValueCategory):
        return PointerType(self.level, target_value_cat)


class IntType(MiniDecafType):
    def reference(self):
        if self.value_cat == ValueCategory.lvalue:
            return PointerType(1)
        raise Exception('Cannot reference rvalue int.')

    def dereference(self):
        raise Exception('Cannot dereference int.')

    def value_category_cast(self, target_value_cat: ValueCategory):
        return IntType(target_value_cat)

    def get_size(self):
        return 4

    def __init__(self, value_cat=ValueCategory.rvalue):
        super().__init__("IntType", value_cat)

    def __eq__(self, other):
        return isinstance(other, IntType) and self.value_cat == other.value_cat


class ArrayType(MiniDecafType):
    size: int
    base_type: MiniDecafType

    def __init__(self, base_type, length):
        super().__init__(f"ArrayType<{base_type}>({length})")
        self.base_type = base_type
        self.size = length * base_type.get_size()

    def __eq__(self, other):
        return isinstance(other, ArrayType) and self.size == other.get_size() and self.base_type == other.base_type

    def get_size(self):
        return self.size

    def reference(self):
        raise Exception("Cannot reference array.")

    def dereference(self):
        raise Exception("Cannot dereference array.")

    def value_category_cast(self, target_value_cat: ValueCategory):
        if target_value_cat == ValueCategory.lvalue:
            raise Exception("Cannot cast array to lvalue.")
        return self


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
