from typing import List

from antlr4.tree.Tree import TerminalNodeImpl

from .Symbol import Symbol, SymbolTable
from .Type import NoType, IntType, MiniDecafType
from .constants import UNOPR2ASM, BIOPR2ASM
from .generated.MiniDecafParser import MiniDecafParser
from .generated.MiniDecafVisitor import MiniDecafVisitor


class MainVisitor(MiniDecafVisitor):
    class FunctionInfo:
        name: str

        def __init__(self, name):
            self.name = name
            self.local_var_count = 0

    current_function: FunctionInfo

    def __init__(self):
        self.contains_main = False
        self.asm_str = ""
        self.symbol_table = SymbolTable()
        # statement count use for label numbering
        self.condition_count = 0
        self.loop_count = 0

        self.loop_stack = []  # loop number stack for break and continue

    def visitProgram(self, ctx: MiniDecafParser.ProgramContext) -> MiniDecafType:
        self.visit(ctx.function())
        if not self.contains_main:
            raise Exception("No main function.")
        return NoType()

    def visitFunction(self, ctx: MiniDecafParser.FunctionContext) -> MiniDecafType:
        self.current_function = self.FunctionInfo(ctx.Identifier().getText())
        if self.current_function.name == "main":
            self.contains_main = True
        self.asm_str += (f"\t.text\n"  # .text notation
                         f"\t.global {self.current_function.name}\n"  # global label
                         f"{self.current_function.name}:\n")  # label name
        self.asm_str += "# function prologue\n"
        self.__push('ra')
        self.__push('fp')
        self.asm_str += "\tmv fp, sp\n"
        prologue_end = len(self.asm_str)
        # new scope
        self.symbol_table.add_scope()
        for block_item in ctx.blockItem():
            self.visit(block_item)
        # pop scope
        self.symbol_table.pop_scope()
        # stack space for local var
        self.asm_str = (self.asm_str[:prologue_end] +
                        f"\taddi sp, sp, {-4 * self.current_function.local_var_count}\n"
                        f"# prologue end\n" +
                        self.asm_str[prologue_end:])
        self.asm_str += "# return 0 as default\n"
        self.__push("zero")
        self.asm_str += (f"# epilogue\n"
                         f".exit.{self.current_function.name}:\n"
                         f"\tlw a0, 0(sp)\n"
                         f"\tmv sp, fp\n")
        self.__pop("fp")
        self.__pop("ra")
        self.asm_str += "\tret\n\n"
        return NoType()

    def visitDeclaration(self, ctx: MiniDecafParser.DeclarationContext) -> MiniDecafType:
        name: str = ctx.Identifier().getText()
        if self.symbol_table.lookup_top(name) is not None:
            raise Exception(f"redefine {name}.")
        self.current_function.local_var_count += 1
        symbol = Symbol(
            name, -4 * self.current_function.local_var_count, IntType()
        )
        self.symbol_table.add_symbol(symbol)
        # initialize
        expression = ctx.expression()
        if expression is not None:
            self.visit(expression)
            self.__pop('t0')
            self.__write_var(symbol)
        return NoType()

    def visitExprStatement(self, ctx: MiniDecafParser.ExprStatementContext) -> MiniDecafType:
        expresion = ctx.expression()
        if expresion is not None:
            self.visit(ctx.expression())
            self.__pop('t0')  # expression won't be used again
        return NoType()

    def visitRetStatement(self, ctx: MiniDecafParser.RetStatementContext) -> MiniDecafType:
        self.visit(ctx.expression())
        self.asm_str += f"\tj .exit.{self.current_function.name}\n"
        return NoType()

    def visitIfStatement(self, ctx: MiniDecafParser.IfStatementContext) -> MiniDecafType:
        cur_conditional_count = self.condition_count  # self.conditional_count may change during visiting
        self.condition_count += 1

        self.asm_str += f"# the {cur_conditional_count}th conditional (if)\n"
        self.visit(ctx.expression())
        self.__pop("t0")
        self.asm_str += (f"\tbeqz t0, .else{cur_conditional_count}\n"
                         f"# then\n")
        self.visit(ctx.statement(0))
        self.asm_str += (f"\tj .ifEnd{cur_conditional_count}\n"
                         f".else{cur_conditional_count}:\n")
        if len(ctx.statement()) > 1:  # with else statement
            self.visit(ctx.statement(1))
        self.asm_str += f".ifEnd{cur_conditional_count}:\n"
        return NoType()

    def visitBlockStatement(self, ctx: MiniDecafParser.BlockStatementContext) -> MiniDecafType:
        self.symbol_table.add_scope()
        for block_item in ctx.blockItem():
            self.visit(block_item)
        self.symbol_table.pop_scope()
        return NoType()

    def visitWhileStatement(self, ctx: MiniDecafParser.WhileStatementContext) -> MiniDecafType:
        cur_loop_count = self.loop_count
        self.loop_count += 1
        self.asm_str += (f"# the {cur_loop_count} loop (while)\n"
                         f".continue{cur_loop_count}:\n")
        self.visit(ctx.expression())
        self.__pop('t0')
        self.asm_str += f"\tbeqz t0, .loopEnd{cur_loop_count}\n"
        self.loop_stack.append(cur_loop_count)
        self.visit(ctx.statement())
        self.loop_stack.pop()
        self.asm_str += f"\tj .continue{cur_loop_count}\n" \
                        f".loopEnd{cur_loop_count}:\n"
        return NoType()

    def visitForStatement(self, ctx: MiniDecafParser.ForStatementContext) -> MiniDecafType:
        cur_loop_count = self.loop_count
        self.loop_count += 1
        semicolon_count = 0  # count semicolon to determine expression position
        self.asm_str += f"# the {cur_loop_count} loop (for)\n"
        for_expression: List[MiniDecafParser.ExpressionContext] = [None] * 3
        for child in ctx.children:
            if ';' in child.getText():
                semicolon_count += 1
            if isinstance(child, MiniDecafParser.ExpressionContext):
                for_expression[semicolon_count] = child
        self.symbol_table.add_scope()
        if for_expression[0] is not None:  # init with expression
            self.visit(for_expression[0])
            self.__pop('t0')  # expression won't be used again
        if ctx.declaration() is not None:  # init with declaration
            self.visit(ctx.declaration())
        self.asm_str += f".loopBegin{cur_loop_count}:\n"
        if for_expression[1] is not None:  # condition
            self.visit(for_expression[1])
            self.__pop('t1')
            self.asm_str += f"beqz t1, .loopEnd{cur_loop_count}\n"
        self.loop_stack.append(cur_loop_count)
        self.symbol_table.add_scope()
        self.visit(ctx.statement())
        self.symbol_table.pop_scope()
        self.loop_stack.pop()
        # if continue. run increment and go to conditino
        self.asm_str += f".continue{cur_loop_count}:\n"
        if for_expression[2] is not None:  # increment
            self.visit(for_expression[2])
            self.__pop('t0')
        self.symbol_table.pop_scope()
        self.asm_str += f"\tj .loopBegin{cur_loop_count}\n" \
                        f".loopEnd{cur_loop_count}:\n"
        return NoType()

    def visitDoWhileStatement(self, ctx: MiniDecafParser.DoWhileStatementContext) -> MiniDecafType:
        cur_loop_count = self.loop_count
        self.loop_count += 1
        self.asm_str += f"# the {cur_loop_count} loop (do while)\n"
        self.asm_str += f".loopBegin{cur_loop_count}:\n"
        self.loop_stack.append(cur_loop_count)
        self.visit(ctx.statement())
        self.loop_stack.pop()
        self.asm_str += f".continue{cur_loop_count}:\n"
        self.visit(ctx.expression())
        self.__pop('t0')  # expression won't be used again
        self.asm_str += f"\tbnez t0, .loopBegin{cur_loop_count}\n" \
                        f".loopEnd{cur_loop_count}:\n"
        return NoType()

    def visitBreakStatement(self, ctx: MiniDecafParser.BreakStatementContext) -> MiniDecafType:
        if not self.loop_stack:
            raise Exception("break statement is not in any loop.")
        self.asm_str += (f"# break\n"
                         f"\tj .loopEnd{self.loop_stack[-1]}\n")
        return NoType()

    def visitContinueStatement(self, ctx: MiniDecafParser.ContinueStatementContext) -> MiniDecafType:
        if not self.loop_stack:
            raise Exception("continue statement is not in any loop.")
        self.asm_str += (f"# contine\n"
                         f"\tj .continue{self.loop_stack[-1]}\n")
        return NoType()

    def visitExpression(self, ctx: MiniDecafParser.ExpressionContext) -> MiniDecafType:
        if len(ctx.children) == 1:  # conditional
            return self.visit(ctx.conditional())
        # ident = expression
        name: str = ctx.Identifier().getText()
        var: Symbol = self.symbol_table.lookup_all(name)
        if var is None:
            raise Exception(f"{name} is undefined.")
        self.visit(ctx.expression())
        self.__pop('t0')
        self.__write_var(var)
        self.__push('t0')
        return var.sym_type

    def visitConditional(self, ctx: MiniDecafParser.ConditionalContext) -> MiniDecafType:
        if len(ctx.children) == 1:  # or
            return self.visit(ctx.logicalOr())
        cur_conditional_count = self.condition_count
        self.condition_count += 1
        self.asm_str += f"# the {cur_conditional_count}th conditional (ternary)\n"
        self.visit(ctx.logicalOr())
        self.__pop('t0')
        self.asm_str += f"\tbeqz t0, .else{cur_conditional_count}\n"
        self.visit(ctx.expression())
        self.asm_str += f"\tj .terEnd{cur_conditional_count}\n" \
                        f".else{cur_conditional_count}:\n"
        self.visit(ctx.conditional())
        self.asm_str += f".terEnd{cur_conditional_count}:\n"
        return IntType()

    def visitLogicalOr(self, ctx: MiniDecafParser.LogicalOrContext) -> MiniDecafType:
        if len(ctx.children) > 1:  # or || and
            self.visit(ctx.logicalOr())
            self.visit(ctx.logicalAnd())
            self.__logic_operation('or')
            return IntType()
        else:  # and
            return self.visit(ctx.logicalAnd())

    def visitLogicalAnd(self, ctx: MiniDecafParser.LogicalAndContext) -> MiniDecafType:
        if len(ctx.children) > 1:  # and || equ
            self.visit(ctx.logicalAnd())
            self.visit(ctx.equality())
            self.__logic_operation('and')
            return IntType()
        else:  # equ
            return self.visit(ctx.equality())

    def visitEquality(self, ctx: MiniDecafParser.EqualityContext) -> MiniDecafType:
        if len(ctx.children) > 1:  # equ op rel
            self.visit(ctx.equality())
            self.visit(ctx.relational())
            self.__pop('t1')
            self.__pop('t0')
            operator: str = ctx.children[1].getText()
            self.asm_str += (f"# calculate {operator}\n"
                             f"\t{BIOPR2ASM['-']}\n"  # t0 = t0 - t1
                             f"\t{BIOPR2ASM[operator]}\n")
            self.__push('t0')
            return IntType()
        else:  # rel
            return self.visit(ctx.relational())

    def visitRelational(self, ctx: MiniDecafParser.RelationalContext) -> MiniDecafType:
        if len(ctx.children) > 1:  # rel op add
            self.visit(ctx.relational())
            self.visit(ctx.additive())
            self.__pop('t1')
            self.__pop('t0')
            operator: str = ctx.children[1].getText()
            self.asm_str += (f"# calculate {operator}\n"
                             f"\t{BIOPR2ASM[operator]}\n")
            self.__push('t0')
            return IntType()
        else:  # add
            return self.visit(ctx.additive())

    def visitAdditive(self, ctx: MiniDecafParser.AdditiveContext) -> MiniDecafType:
        if len(ctx.children) > 1:  # add op mul
            self.visit(ctx.additive())
            self.visit(ctx.multiplicative())
            self.__pop('t1')
            self.__pop('t0')
            operator: str = ctx.children[1].getText()
            self.asm_str += (f"# calculate {operator}\n"
                             f"\t{BIOPR2ASM[operator]}\n")
            self.__push("t0")
            return IntType()
        else:  # mul
            return self.visit(ctx.multiplicative())

    def visitMultiplicative(self, ctx: MiniDecafParser.MultiplicativeContext) -> MiniDecafType:
        if len(ctx.children) > 1:  # mul op una
            self.visit(ctx.multiplicative())
            self.visit(ctx.unary())
            operator: str = ctx.children[1].getText()
            self.__pop('t1')
            self.__pop('t0')
            self.asm_str += (f"# calculate {operator}\n"
                             f"\t{BIOPR2ASM[operator]}\n")
            self.__push("t0")
            return IntType()
        else:  # una
            return self.visit(ctx.unary())

    def visitUnary(self, ctx: MiniDecafParser.UnaryContext) -> MiniDecafType:
        if len(ctx.children) == 1:  # primary
            return self.visit(ctx.primary())
        else:  # op una
            self.visit(ctx.unary())
            operator: str = ctx.children[0].getText()
            self.__pop('t0')
            self.asm_str += (f"# calculate {operator}\n"
                             f"\t{UNOPR2ASM[operator]}\n")
            self.__push('t0')
            return IntType()

    def visitNumPrimary(self, ctx: MiniDecafParser.NumPrimaryContext) -> MiniDecafType:
        num: TerminalNodeImpl = ctx.Integer()
        # overflow
        if int(num.getText()) > 0x7fffffff:
            raise Exception(f"{int(num.getText())} is too large for int.")
        self.asm_str += (f"# load number {num}\n"
                         f"\tli t0, {num.getText()}\n")
        self.__push('t0')
        return IntType()

    def visitParenthesizedPrimary(self, ctx: MiniDecafParser.ParenthesizedPrimaryContext) -> MiniDecafType:
        return self.visit(ctx.expression())

    def visitIdentPrimary(self, ctx: MiniDecafParser.IdentPrimaryContext) -> MiniDecafType:
        name: str = ctx.Identifier().getText()
        var = self.symbol_table.lookup_all(name)
        if var is None:
            raise Exception(f"{name} is undefined.")
        self.__read_var(var)
        self.__push('t0')
        return var.sym_type

    def __pop(self, reg: str):
        self.asm_str += (f"# pop {reg}\n"
                         f"\tlw {reg}, 0(sp)\n"
                         f"\taddi sp, sp, 4\n")  # stack ptr

    def __push(self, reg: str):
        self.asm_str += (f"# push {reg}\n"
                         f"\taddi sp, sp, -4\n"  # stack ptr
                         f"\tsw {reg}, 0(sp)\n")

    def __set_bool(self, reg):  # set a reg to bool according to data stored in it
        self.asm_str += (f"# set bool\n"
                         f"\tsnez {reg}, {reg}\n")

    def __write_var(self, var: Symbol):
        self.asm_str += (f"# write variable {var.name}\n"
                         f"\tsw t0, {var.offset}(fp)\n")

    def __read_var(self, symbol: Symbol):
        self.asm_str += (f"# read variable {symbol.name}\n"
                         f"\tlw t0, {symbol.offset}(fp)\n")

    def __logic_operation(self, operator: str):
        self.__pop('t1')
        self.__pop('t0')
        self.__set_bool('t1')
        self.__set_bool('t0')
        self.asm_str += (f"# calculate {operator}\n"
                         f"\t{operator} t0, t0, t1\n")
        self.__push('t0')
