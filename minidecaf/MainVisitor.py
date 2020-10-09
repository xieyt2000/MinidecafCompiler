from antlr4.tree.Tree import TerminalNodeImpl

from .Type import NoType, IntType
from .constants import UNOPR2ASM, BIOPR2ASM
from .generated.MiniDecafParser import MiniDecafParser
from .generated.MiniDecafVisitor import MiniDecafVisitor


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
        return NoType()

    def visitStatement(self, ctx: MiniDecafParser.StatementContext):
        self.visit(ctx.expression())
        self.__ret()
        return NoType()

    def visitExpression(self, ctx: MiniDecafParser.ExpressionContext):
        return self.visit(ctx.logical_or())

    def __logic_operation(self, operator: str):
        self.__pop('t1')
        self.__pop('t0')
        self.__set_bool('t1')
        self.__set_bool('t0')
        self.asm_str += f"\t{operator} t0, t0, t1\n"
        self.__push('t0')

    def visitLogical_or(self, ctx: MiniDecafParser.Logical_orContext):
        if len(ctx.children) > 1:  # or || and
            self.visit(ctx.logical_or())
            self.visit(ctx.logical_and())
            self.__logic_operation('or')
            return IntType()
        else:  # and
            return self.visit(ctx.logical_and())

    def visitLogical_and(self, ctx: MiniDecafParser.Logical_andContext):
        if len(ctx.children) > 1:  # and || equ
            self.visit(ctx.logical_and())
            self.visit(ctx.equality())
            self.__logic_operation('and')
            return IntType()
        else:  # equ
            return self.visit(ctx.equality())

    def visitEquality(self, ctx: MiniDecafParser.EqualityContext):
        if len(ctx.children) > 1:  # equ op rel
            self.visit(ctx.equality())
            self.visit(ctx.relational())
            self.__pop('t1')
            self.__pop('t0')
            self.asm_str += '\t' + BIOPR2ASM['-'] + '\n'  # t0 = t0 - t1
            operator: str = ctx.children[1].getText()
            self.asm_str += '\t' + BIOPR2ASM[operator] + '\n'
            self.__push('t0')
            return IntType()
        else:  # rel
            return self.visit(ctx.relational())

    def visitRelational(self, ctx: MiniDecafParser.RelationalContext):
        if len(ctx.children) > 1:  # rel op add
            self.visit(ctx.relational())
            self.visit(ctx.additive())
            self.__pop('t1')
            self.__pop('t0')
            operator: str = ctx.children[1].getText()
            self.asm_str += '\t' + BIOPR2ASM[operator] + '\n'
            self.__push('t0')
            return IntType
        else:  # add
            return self.visit(ctx.additive())

    def visitAdditive(self, ctx: MiniDecafParser.AdditiveContext):
        if len(ctx.children) > 1:  # add op mul
            self.visit(ctx.additive())
            self.visit(ctx.multiplicative())
            self.__pop('t1')
            self.__pop('t0')
            operator: str = ctx.children[1].getText()
            self.asm_str += '\t' + BIOPR2ASM[operator] + '\n'
            self.__push("t0")
            return IntType()
        else:  # mul
            return self.visit(ctx.multiplicative())

    def visitMultiplicative(self, ctx: MiniDecafParser.MultiplicativeContext):
        if len(ctx.children) > 1:  # mul op una
            self.visit(ctx.multiplicative())
            self.visit(ctx.unary())
            operator: str = ctx.children[1].getText()
            self.__pop('t1')
            self.__pop('t0')
            self.asm_str += '\t' + BIOPR2ASM[operator] + '\n'
            self.__push("t0")
            return IntType()
        else:  # una
            return self.visit(ctx.unary())

    def visitUnary(self, ctx: MiniDecafParser.UnaryContext):
        if len(ctx.children) == 1:  # primary
            return self.visit(ctx.primary())
        else:  # op una
            self.visit(ctx.unary())
            operator: str = ctx.children[0].getText()
            self.__pop('t0')
            self.asm_str += '\t' + UNOPR2ASM[operator] + '\n'
            self.__push('t0')
            return IntType()

    def visitNumPrimary(self, ctx: MiniDecafParser.NumPrimaryContext):
        num: TerminalNodeImpl = ctx.Integer()
        # overflow
        if int(num.getText()) > 0x7fffffff:
            raise Exception("Int too large")
        self.asm_str += f"\tli t0, {num.getText()}\n"
        self.__push('t0')
        return IntType()

    def visitParenthesizedPrimary(self, ctx: MiniDecafParser.ParenthesizedPrimaryContext):
        return self.visit(ctx.expression())

    def __pop(self, reg: str):
        self.asm_str += (f"# pop {reg}\n"
                         f"\tlw {reg}, 0(sp)\n"
                         f"\taddi sp, sp, 4\n")  # stack ptr

    def __push(self, reg: str):
        self.asm_str += (f"# push {reg}\n"
                         f"\taddi sp, sp, -4\n"  # stack ptr
                         f"\tsw {reg}, 0(sp)\n")

    def __ret(self):
        self.asm_str += f"# ret\n"
        self.__pop('a0')
        self.asm_str += f"\tret\n"

    def __set_bool(self, reg):  # set a reg to bool according to data stored in it
        self.asm_str += f"\tsnez {reg}, {reg}\n"
