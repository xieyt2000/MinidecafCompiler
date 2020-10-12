# Step5 实验报告

2018011334 谢云桐



## 实验内容

本阶段处理局部变量的声明与使用。Antlr 文件的修改与实验指导书基本相同，不同之处是我参考 Java 示例代码，将 `declaration` 和 `statement` 分开处理，代码如下：

```
blockItem
    : declaration
    | statement;

statement
    : 'return' expression ';' # retStatement
    | expression? ';'  # exprStatement
    ;

declaration
    : varType Identifier ('=' expression)? ';';
```

在程序中使用 `SymbolMap` 存储符号表，定义如下：

```python
from typing import Dict, Any, Type

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

```

Visitor 方面，需要完全重构原来对函数的访问，加入 prologue 和 epilogue，准备局部变量的栈空间并提供默认返回值。代码如下：

```python
    def visitFunction(self, ctx: MiniDecafParser.FunctionContext):
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
        for block_item in ctx.blockItem():
            self.visit(block_item)
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
```





## 思考题

1. 描述程序运行过程中函数栈帧的构成，分成哪几个部分？每个部分所用空间最少是多少？

   从高地址到低地址：

   - callee-saved register：如果使用被调用者负责保存的寄存器，需要在这里保存。一般来说至少有 `fp, ra`，需要8 bytes。
   - 局部变量：函数体内部定义的变量。可以为空（没有局部变量或者局部变量都存在寄存器中）。
   - 运算栈：进行比较复杂的运算时保存的临时结果。一般为空
   - 子函数参数：调用子函数时在寄存器中存不下的参数。由于 risc-v 可以用来传参的寄存器较多，一般为空。
   - 返回地址：调用子函数的返回地址。如果没有调用函数则为空，有的话为4 bytes。

2. 有些语言允许在同一个作用域中多次定义同名的变量，例如这是一段合法的 Rust 代码（你不需要精确了解它的含义，大致理解即可）：

   ```rust
   fn main() {
     let a = 0;
     let a = f(a);
     let a = g(a);
   }
   ```

   其中`f(a)`中的`a`是上一行的`let a = 0;`定义的，`g(a)`中的`a`是上一行的`let a = f(a);`。

   如果 MiniDecaf 也允许多次定义同名变量，并规定新的定义会覆盖之前的同名定义，请问在你的实现中，需要对定义变量和查找变量的逻辑做怎样的修改？

   定义变量时不再查重，直接修改/定义 `symbol_map` 中定义的值。查找逻辑无需修改。

## 参考材料

借鉴了 Java-Antlar 参考实现

