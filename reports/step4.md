# Step4 实验报告

2018011334 谢云桐



## 实验内容

本阶段处理比较和逻辑表达式，处理的基本思路和上一阶段的加减乘除模相同，都是只使用 `t1, t0` 寄存器。 以比较类类运算（`> ,<, >=, <=`）为例，代码如下：

```python
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
```



## 思考题

1. 在表达式计算时，对于某一步运算，是否一定要先计算出所有的操作数的结果才能进行运算？

   不是。比如在 C （或者其他支持短路求值的语言）中，`false && (a && b) `  就不需要计算出 `(a && b)`，可以直接得出结果。

2. 在 MiniDecaf 中，我们对于短路求值未做要求，但在包括 C 语言的大多数流行的语言中，短路求值都是被支持的。为何这一特性广受欢迎？你认为短路求值这一特性会给程序员带来怎样的好处？

   短路求值可以省去不必要的运算，提高程序的运行效率（如思考题1中的例子）。而且可以简化代码，比如利用短路特性将判空和判断性质放到同一个条件中：

   ```c
   // without short-circuting
   if(a != NULL) {
     if(a == 0){
       ...
     }
   }
   // with short-circuting
   if(a ！= NULL && a==0) {
     ...
   }
   ```

   

## 参考材料

借鉴了 Java-Antlar 参考实现