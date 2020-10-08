from .generated.MiniDecafVisitor import MiniDecafVisitor
from .generated.MiniDecafParser import MiniDecafParser
from antlr4.tree.Tree import TerminalNodeImpl
from .Type import NoType, IntType
from .constants import OPERATOR2ASM


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
        self.__ret()
        return NoType()

    def visitExpression(self, ctx: MiniDecafParser.ExpressionContext):
        return self.visit(ctx.unary())

    def visitUnary(self, ctx: MiniDecafParser.UnaryContext):
        if len(ctx.children) == 1:  # single number
            num: TerminalNodeImpl = ctx.Integer()
            # overflow
            if int(num.getText()) > 0x7fffffff:
                raise Exception("Int too large")
            self.asm_str += f"\tli t0, {num.getText()}\n"
            self.__push('t0')
            return IntType()
        else:  # unary wit operator
            self.visit(ctx.unary())
            operator: str = ctx.children[0].getText()
            self.__pop('t0')
            self.asm_str += OPERATOR2ASM[operator] + '\n'
            self.__push('t0')
            return IntType()

    def __pop(self, reg: str):
        self.asm_str += (f"# pop {reg}\n"
                         f"\tlw {reg}, 0(sp)\n"
                         f"addi sp, sp, 4\n")  # stack ptr

    def __push(self, reg: str):
        self.asm_str += (f"# push {reg}\n"
                         f"\taddi sp, sp, -4\n"  # stack ptr
                         f"\tsw {reg}, 0(sp)\n")

    def __ret(self):
        self.asm_str += f"# ret\n"
        self.__pop('a0')
        self.asm_str += f"\tret\n"
