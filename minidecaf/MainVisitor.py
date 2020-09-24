from .generated.MiniDecafVisitor import MiniDecafVisitor
from .generated.MiniDecafParser import MiniDecafParser
from antlr4.tree.Tree import TerminalNodeImpl
from .Type import NoType, IntType


class MainVisitor(MiniDecafVisitor):

    def __init__(self):
        self.contains_main = False
        self.current_func = ""
        self.asm_str = ""

    def visitProgram(self, ctx: MiniDecafParser.ProgramContext):
        self.visit(ctx.function())
        if not self.contains_main:
            raise Exception("No main function")
        return NoType()

    def visitFunction(self, ctx: MiniDecafParser.FunctionContext):
        self.current_func = ctx.Identifier().getText()
        if self.current_func == "main":
            self.contains_main = True
        self.asm_str += (f"\t.text\n"  # .text notation
                         f"\t.global {self.current_func}\n"  # global label
                         f"{self.current_func}:\n")  # label name
        self.visit(ctx.statement())

    def visitStatement(self, ctx: MiniDecafParser.StatementContext):
        self.visit(ctx.expression())
        self.asm_str += "\tret\n"  # ret
        return NoType()

    def visitExpression(self, ctx: MiniDecafParser.ExpressionContext):
        num: TerminalNodeImpl = ctx.Integer()
        # overflow
        if int(num.getText()) > 0x7fffffff:
            raise Exception("Int too large")
        self.asm_str += f"\tli a0, {num.getText()}\n"  # return value
        return IntType()
