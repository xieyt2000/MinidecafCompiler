from typing import Dict

from .Type import MiniDecafType


class Symbol:
    sym_type: MiniDecafType
    offset: int  # relative position
    name: str

    def __init__(self, name: str, offset: int, sym_type: MiniDecafType):
        self.name = name
        self.offset = offset
        self.sym_type = sym_type

    def __str__(self):
        return f"{self.name}@{self.sym_type}:{self.offset}"


class SymbolMap:
    __symbol_map: Dict[str, Symbol]

    def __init__(self):
        self.__symbol_map = {}

    def lookup(self, name):
        return self.__symbol_map.get(name, None)

    def add(self, name, count, syn_type):
        self.__symbol_map[name] = Symbol(name, -4 * count, syn_type)
