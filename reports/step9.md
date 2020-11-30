# Step9 实验报告

2018011334 谢云桐



## 实验内容

本阶段实现函数，函数相关语法规则如下：

```ANTLR
function
    : varType Identifier '(' (varType Identifier (',' varType Identifier)*)? ')' '{' blockItem* '}' # defFunc
    | varType Identifier '(' (varType Identifier (',' varType Identifier)*)? ')' ';' # declareFunc
    ;
    
postfix
    : primary
    | Identifier '(' (expression (',' expression)*)? ')';
```

需要加入两个字典记录已经定义/声明的函数及其参数和返回值类型，访问函数定义代码如下：

```python
    def visitDefFunc(self, ctx: MiniDecafParser.DefFuncContext) -> MiniDecafType:
        self.current_function = self.FunctionInfo(ctx.Identifier(0).getText())
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
```



## 思考题

1. MiniDecaf 的函数调用时参数求值的顺序是未定义行为。试写出一段 MiniDecaf 代码，使得不同的参数求值顺序会导致不同的返回结果。

   ```c
   int add(int b, int c) {
     return b + c;
   }
   int main() {
     int a = 0;
     return add(a = a + 1, a)
   }
   ```

   根据不同的参数求值顺序，可能返回 `1` 或 `2`，因为本编译器的实现是从右向左求值，该函数返回 `1`。



## 参考材料

借鉴了 Java-Antlar 参考实现

