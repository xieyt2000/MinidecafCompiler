# Step8 实验报告

2018011334 谢云桐



## 实验内容

本阶段实现循环语句，首先在 `g4` 文件中加入新的语法规则：

```ANTLR
    | '{' blockItem* '}' # blockStatement
    | 'while' '(' expression ')' statement # whileStatement
    | 'for' '(' (declaration | expression? ';') expression? ';' expression? ')' statement # forStatement
    | 'do' statement 'while' '(' expression ')' ';' # doWhileStatement
    | 'break' ';' # breakStatement
    | 'continue' ';' # continueStatement
```

然后分别实现不同循环命令的 `visit` 规则，以最复杂的 `for` 循环为例：

```python
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
```

首先根据分号提取 `for (...)` 中三个可以为空的 `expression`。之后开始写入汇编指令：首先执行初始化和条件判断，然后循环体，最后执行自增后跳转至开始。在这个过程中要注意作用域以及当前循环栈（用于 `break` 和 `continue` 寻找对应 `label`）的管理。

## 思考题

1. 将循环语句翻译成 IR 有许多可行的翻译方法，例如 while 循环可以有以下两种翻译方式：


第一种（即实验指导中的翻译方式）：

1. `label BEGINLOOP_LABEL`：开始下一轮迭代
2. `cond 的 IR`
3. `beqz BREAK_LABEL`：条件不满足就终止循环
4. `body 的 IR`
5. `label CONTINUE_LABEL`：continue 跳到这
6. `br BEGINLOOP_LABEL`：本轮迭代完成
7. `label BREAK_LABEL`：条件不满足，或者 break 语句都会跳到这儿

第二种：

1. `cond 的 IR`
2. `beqz BREAK_LABEL`：条件不满足就终止循环
3. `label BEGINLOOP_LABEL`：开始下一轮迭代
4. `body 的 IR`
5. `label CONTINUE_LABEL`：continue 跳到这
6. `cond 的 IR`
7. `bnez BEGINLOOP_LABEL`：本轮迭代完成，条件满足时进行下一次迭代
8. `label BREAK_LABEL`：条件不满足，或者 break 语句都会跳到这儿

从执行的指令的条数这个角度（`label` 指令不计算在内，假设循环体至少执行了一次），请评价这两种翻译方式哪一种更好？

从指令执行条数的角度来看，第二种更好。第一种在最后一次循环体结束（包括使用 `continue` 提前结束 ）以后需要跳转两次（`br BEGINLOOP_LABEL, beqz BREAK_LABEL`）才能退出循环，而第二种不需要执行这两次跳转。



## 参考材料

借鉴了 Java-Antlar 参考实现

