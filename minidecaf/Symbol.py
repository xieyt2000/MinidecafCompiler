from typing import Dict, List

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

    def add(self, symbol: Symbol):
        self.__symbol_map[symbol.name] = symbol


class SymbolTable:
    __symbol_table: List[SymbolMap]

    def __init__(self):
        self.__symbol_table = []

    def lookup_all(self, name):
        # lookup in inner block first
        for symbol_map in reversed(self.__symbol_table):
            if symbol_map.lookup(name) is not None:
                return symbol_map.lookup(name)
        return None

    def lookup_top(self, name):
        return self.__symbol_table[-1].lookup(name)

    def pop_scope(self):
        self.__symbol_table.pop()

    def add_scope(self):
        self.__symbol_table.append(SymbolMap())

    def add_symbol(self, symbol: Symbol):
        self.__symbol_table[-1].add(symbol)
