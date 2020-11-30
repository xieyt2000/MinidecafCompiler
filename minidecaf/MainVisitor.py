from typing import List, Dict

from antlr4.tree.Tree import TerminalNodeImpl

from .Symbol import Symbol, SymbolTable
from .Type import NoType, IntType, MiniDecafType, FuncType
from .constants import UNOPR2ASM, BIOPR2ASM
from .generated.MiniDecafParser import MiniDecafParser
from .generated.MiniDecafVisitor import MiniDecafVisitor


class MainVisitor(MiniDecafVisitor):
    declare_global_var_dict: Dict[str, MiniDecafType]
    init_global_var_dict: Dict[str, MiniDecafType]
    define_func_dict: Dict[str, FuncType]
    declare_func_dict: Dict[str, FuncType]

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
        # function dict
        self.declare_func_dict = {}
        self.define_func_dict = {}
        # global var dict
        self.declare_global_var_dict = {}
        self.init_global_var_dict = {}

    def visitProgram(self, ctx: MiniDecafParser.ProgramContext) -> MiniDecafType:
        for child in ctx.children:
            self.visit(child)
        for name, var_type in self.declare_global_var_dict.items():
            if name not in self.init_global_var_dict:
                self.asm_str += f"\t.comm {name}, {var_type.get_size()}, 4\n"
        if not self.contains_main:
            raise Exception("No main function.")
        return NoType()

    def visitDeclareFunc(self, ctx: MiniDecafParser.DeclareFuncContext) -> MiniDecafType:
        func_name: str = ctx.Identifier(0).getText()
        if func_name in self.declare_global_var_dict:
            raise Exception(f"{func_name} is already defined as a global variable.")
        func_type = self.__get_func_type(ctx)
        if self.declare_func_dict.get(func_name, func_type) != func_type:
            raise Exception(f"Declare functions {func_name} but different signature.")
        self.declare_func_dict[func_name] = func_type
        return NoType()

    def visitDefFunc(self, ctx: MiniDecafParser.DefFuncContext) -> MiniDecafType:
        self.current_function = self.FunctionInfo(ctx.Identifier(0).getText())
        if self.current_function.name in self.declare_global_var_dict:
            raise Exception(f"{self.current_function.name} is already defined as a global variable.")
        if self.current_function.name == "main":
            self.contains_main = True
        self.asm_str += (f"\t.text\n"  # .text notation
                         f"\t.global {self.current_function.name}\n"  # global label
                         f"{self.current_function.name}:\n")  # label name
        # add func type
        if self.current_function.name in self.define_func_dict:
            raise Exception(f"Redefine function {self.current_function.name}.")
        func_type = self.__get_func_type(ctx)
        if self.declare_func_dict.get(self.current_function.name, func_type) != func_type:
            raise Exception(f"{self.current_function.name} definition and declaration conflict.")
        self.declare_func_dict[self.current_function.name] = func_type
        self.define_func_dict[self.current_function.name] = func_type

        self.asm_str += "# function prologue\n"
        self.__push('ra')
        self.__push('fp')
        self.asm_str += "\tmv fp, sp\n"
        prologue_end = len(self.asm_str)
        # new scope
        self.symbol_table.add_scope()
        # get parameters
        for i in range(1, len(ctx.Identifier())):
            para_name = ctx.Identifier(i).getText()
            if self.symbol_table.lookup_top(para_name) is not None:
                raise Exception(f"Two parameters named as {para_name}.")
            if i < 9:  # load a[i-1] into stack
                self.current_function.local_var_count += 1
                self.asm_str += f"\tsw a{i - 1}, {-4 * i}(fp)\n"
                self.symbol_table.add_symbol(Symbol(para_name, -4 * i, func_type.para_types[i - 1]))
            else:  # currently in stack above ra and fp
                self.symbol_table.add_symbol(Symbol(para_name, 4 * (i - 9 + 2), func_type.para_types[i - 1]))

        # begin visiting
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

    def visitGlobalVar(self, ctx: MiniDecafParser.GlobalVarContext) -> MiniDecafType:
        var_name = ctx.Identifier().getText()
        if var_name in self.declare_func_dict:
            raise Exception(f"{var_name} is already defined as a function.")
        var_type = self.visit(ctx.varType())
        if self.declare_func_dict.get(var_name, var_type) != var_type:
            raise Exception(f"{var_name} is already defined with a different type.")
        self.declare_global_var_dict[var_name] = var_type

        num = ctx.Integer()
        if num is not None:
            if var_name in self.init_global_var_dict:
                raise Exception(f"{var_name} is already initialized")
            self.init_global_var_dict[var_name] = var_type
            self.asm_str += ("\t.data\n"
                             "\t.align 4\n"
                             f"{var_name}:\n"
                             f"\t.word {num.getText()}\n")
        return NoType()

    def visitDeclaration(self, ctx: MiniDecafParser.DeclarationContext) -> MiniDecafType:
        name: str = ctx.Identifier().getText()
        if self.symbol_table.lookup_top(name) is not None:
            raise Exception(f"Redefine variable {name}.")
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
            self.__write_local_var(symbol)
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
        # if continue. run increment and go to condition
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
            raise Exception("Break statement is not in any loop.")
        self.asm_str += (f"# break\n"
                         f"\tj .loopEnd{self.loop_stack[-1]}\n")
        return NoType()

    def visitContinueStatement(self, ctx: MiniDecafParser.ContinueStatementContext) -> MiniDecafType:
        if not self.loop_stack:
            raise Exception("Continue statement is not in any loop.")
        self.asm_str += (f"# contine\n"
                         f"\tj .continue{self.loop_stack[-1]}\n")
        return NoType()

    def visitExpression(self, ctx: MiniDecafParser.ExpressionContext) -> MiniDecafType:
        if len(ctx.children) == 1:  # conditional
            return self.visit(ctx.conditional())
        # ident = expression
        name: str = ctx.Identifier().getText()
        self.visit(ctx.expression())
        local_var: Symbol = self.symbol_table.lookup_all(name)
        if local_var is not None:
            self.__pop('t0')
            self.__write_local_var(local_var)
            self.__push('t0')
            return local_var.sym_type
        elif name in self.declare_global_var_dict:
            self.__pop('t0')
            self.__write_global_var(name)
            self.__push('t0')
            return self.declare_global_var_dict[name]
        else:
            raise Exception(f"{name} is undefined.")

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
        if len(ctx.children) == 1:  # postfix
            return self.visit(ctx.postfix())
        else:  # op una
            self.visit(ctx.unary())
            operator: str = ctx.children[0].getText()
            self.__pop('t0')
            self.asm_str += (f"# calculate {operator}\n"
                             f"\t{UNOPR2ASM[operator]}\n")
            self.__push('t0')
            return IntType()

    def visitPostfix(self, ctx: MiniDecafParser.PostfixContext) -> MiniDecafType:
        if len(ctx.children) == 1:  # primary
            return self.visit(ctx.primary())
        else:  # call function
            name = ctx.Identifier().getText()
            if name not in self.declare_func_dict:
                raise Exception(f"Calling undeclared function {name}.")
            fun_type = self.declare_func_dict[name]
            if len(fun_type.para_types) != len(ctx.expression()):
                raise Exception(f"{name} arguments mismatch")
            self.asm_str += "# fill arguments\n"
            for i in range(len(ctx.expression()) - 1, -1, -1):
                self.visit(ctx.expression(i))
                if i < 8:
                    self.__pop(f'a{i}')
            self.asm_str += f"\tcall {name}\n"
            self.__push('a0')  # ret val
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
        local_var = self.symbol_table.lookup_all(name)
        if local_var is not None:
            self.__read_var(local_var)
            self.__push('t0')
            return local_var.sym_type
        elif name in self.declare_global_var_dict:
            self.__read_global_var(name)
            self.__push('t0')
            return self.declare_global_var_dict[name]
        else:
            raise Exception(f"{name} is undefined.")

    def visitVarType(self, ctx: MiniDecafParser.VarTypeContext) -> MiniDecafType:
        return IntType()

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

    def __write_local_var(self, var: Symbol):  # write var with val in t0
        self.asm_str += (f"# write variable {var.name}\n"
                         f"\tsw t0, {var.offset}(fp)\n")

    def __write_global_var(self, name):  # write var with val in t0
        self.asm_str += (f"# write global variable {name}\n"
                         f"\tla t1, {name}\n"
                         f"\tsw t0, 0(t1)\n")

    def __read_var(self, symbol: Symbol):
        self.asm_str += (f"# read variable {symbol.name}\n"
                         f"\tlw t0, {symbol.offset}(fp)\n")

    def __read_global_var(self, name):
        self.asm_str += (f"# read global variable {name}\n"
                         f"\tla t1, {name}\n"
                         f"\tlw t0, 0(t1)\n")

    def __logic_operation(self, operator: str):
        self.__pop('t1')
        self.__pop('t0')
        self.__set_bool('t1')
        self.__set_bool('t0')
        self.asm_str += (f"# calculate {operator}\n"
                         f"\t{operator} t0, t0, t1\n")
        self.__push('t0')

    def __get_func_type(self, ctx) -> FuncType:
        ret_type: MiniDecafType = self.visit(ctx.varType(0))
        para_types: List[MiniDecafType] = []
        for i in range(1, len(ctx.varType())):
            para_types.append(self.visit(ctx.varType(i)))
        func_type = FuncType(ret_type, para_types)
        return func_type
