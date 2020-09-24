"""实例：真·main"""

import argparse

import antlr4

from .MainVisitor import MainVisitor
from .generated.MiniDecafLexer import MiniDecafLexer
from .generated.MiniDecafParser import MiniDecafParser


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=str)
    parser.add_argument("output", type=str, nargs='?')
    return parser.parse_args()


def main():
    args: argparse.Namespace = parse_args()
    input_stream: antlr4.FileStream = antlr4.FileStream(args.input)
    token_stream: antlr4.CommonTokenStream = antlr4.CommonTokenStream(MiniDecafLexer(input_stream))
    parser: MiniDecafParser = MiniDecafParser(token_stream)
    parser._errHandler = antlr4.BailErrorStrategy()
    tree: MiniDecafParser.ProgramContext = parser.program()
    visitor: MainVisitor = MainVisitor()
    visitor.visit(tree)
    if args.output is not None:
        with open(args.output, mode='w') as file:
            file.write(visitor.asm_str)
    else:
        print(visitor.asm_str)
