# Step6 实验报告

2018011334 谢云桐



## 实验内容

本阶段实现 `if` 语句和三目表达式，二者实现的逻辑比较相似，下面以 `if` 为例说明 visitor 的操作，代码如下：

```python
    def visitIfStatement(self, ctx: MiniDecafParser.IfStatementContext):
        cur_conditional_num = self.condition_num  # self.conditional_num may change during visiting
        self.condition_num += 1
        
        self.asm_str += f"# the {cur_conditional_num}th conditional (if)\n"
        self.visit(ctx.expression())
        self.__pop("t0")
        self.asm_str += (f"\tbeqz t0, .else{cur_conditional_num}\n"
                         f"# then\n")
        self.visit(ctx.statement(0))
        self.asm_str += (f"\tj .ifEnd{cur_conditional_num}\n"
                         f".else{cur_conditional_num}:\n")
        if len(ctx.statement()) > 1:  # with else statement
            self.visit(ctx.statement(1))
        self.asm_str += f".ifEnd{cur_conditional_num}:\n"
        return NoType()
```

新定义了一个成员变量 `condition_num` 记录当前条件跳转的个数，给 `label` 编号。处理逻辑就是如果条件为真，顺序执行后跳转到末尾，如果条件为假，跳转到 `.else` 后顺序执行到末尾。



## 思考题

1. Rust 和 Go 语言中的 if-else 语法与 C 语言中略有不同，它们都要求两个分支必须用大括号包裹起来，而且条件表达式不需要用括号包裹起来：

```Rust
if 条件表达式 {
  // 在条件为 true 时执行
} else {
  // 在条件为 false 时执行
}
```

请问相比 C 的语法，这两种语言的语法有什么优点？

必须使用大括号的优点是结构更清晰，可读性更高，而且不会出现悬吊 else 二义性这种问题。

不需要使用括号的优点是提醒开发者在 if 条件中要规范操作，如 Rust 在条件表达式中不能给变量赋值，但是 C 中却支持这种复杂操作：`if (a = 0, b = 0, a > b, a < b, a == b)`。当然这点并不绝对，如不使用括号的 Go 可以在条件表达式中定义变量，不过 Go 中定义变量的语法也较为规范（`if num := 0; num < 0`）。

## 参考材料

借鉴了 Java-Antlar 参考实现

