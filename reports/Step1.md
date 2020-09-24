# Step1 实验报告

2018011334 谢云桐



## 实验内容

本程序使用 Antlar 生成语法分析树，不使用中间码，直接用 Antlar 的 Visitor 生成汇编代码。

Step1 要求处理只有一个 `return` 的 `main` 函数，涉及到的逻辑很少，词法语法简单，`MiniDecaf.g4` 代码如下：

```
grammar MiniDecaf;

//parser
program
    : function EOF;

function
    : varType Identifier '(' ')' '{' statement '}';

// 'type' conflict with python keyword, so rename to varType
varType
    : 'int';

statement
    : 'return' expression ';';

expression
    : Integer;


// lexer
WhiteSpace
    : [ \t\r\n\u000C] -> skip;

Identifier
    : [a-zA-Z_] [a-zA-Z_0-9]*;

Integer
    : [0-9]+;

```

重写 `MiniDecafVisitor` 中的几种 `VisitXXX`，直接在其中生成汇编代码串，代码如下：

```python
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
```

本次实验中语法的结构都比较简单，不再赘述。



## 思考题

1. 修改 minilexer 的输入（`lexer.setInput` 的参数），使得 lex 报错，给出一个简短的例子。

   输入不能识别的 token 即可，可以直接输入一个未在任何定义中出现的字符，如：

   ```c
   我
   ```

2. 修改 minilexer 的输入，使得 lex 不报错但 parse 报错，给出一个简短的例子。

   输入合法的token，但是语法错误，如

   ```c
   int main{}
   ```

3. 在 riscv 中，哪个寄存器是用来存储函数返回值的？

   寄存器使用惯例规定，返回值保存在 `a0, a1`。

## 参考材料

`Makefile` 等编译运行指令、Antlar API 的使用借鉴了 Python-Antlar 参考实现

ANTLR 代码及运行逻辑（单遍）借鉴了 Java-Antlar 参考实现