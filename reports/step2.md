# Step2 实验报告

2018011334 谢云桐



## 实验内容

本阶段处理单目运算符，本程序的处理方式是每次都用 `t0` 进行运算，运算完成以后便将结果入栈。 代码如下：

```python
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
```





## 思考题

1. 我们在语义规范中规定整数运算越界是未定义行为，运算越界可以简单理解成理论上的运算结果没有办法保存在32位整数的空间中，必须截断高于32位的内容。请设计一个表达式，只使用`-~!`这三个单目运算符和 $[0, 2^{31} - 1]$ 范围内的非负整数，使得运算过程中发生越界。

   ```c
   int main() {
     return -~2147483647;
   }
   ```

   2147483647 为最大的整数，即 `+0x7FFFFFFF`，`~` 取反后为 `0x80000000`，即 `-0x80000000`，对其取相反数应为 `+0x80000000`，在整数范围之外，发生越界。 

   

## 参考材料

借鉴了 Java-Antlar 参考实现