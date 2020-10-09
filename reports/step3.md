# Step3 实验报告

2018011334 谢云桐



## 实验内容

本阶段处理二元运算符，本程序的处理方式是每次都从栈中读取数据，用 `t0` 存储第一个运算数和运算结果，用 `t1` 存储第二个运算数，运算完成以后便将结果入栈。 以加法类运算（+/-）为例，代码如下：

```python
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
```



## 思考题

1. 请给出将寄存器 `t0` 中的数值压入栈中所需的 riscv 汇编指令序列；请给出将栈顶的数值弹出到寄存器 `t0` 中所需的 riscv 汇编指令序列。

   ```assembly
   # push t0
   addi sp, sp, -4
   sw t0, 0(sp)
   
   # pop t0
   lw t0, 0(sp)
   addi sp, sp, 4
   ```


2. 语义规范中规定“除以零、模零都是未定义行为”，但是即使除法的右操作数不是 0，仍然可能存在未定义行为。请问这时除法的左操作数和右操作数分别是什么？请将这时除法的左操作数和右操作数填入下面的代码中，分别在你的电脑（请标明你的电脑的架构，比如 x86-64 或 ARM）中和 RISCV-32 的 qemu 模拟器中编译运行下面的代码，并给出运行结果。（编译时请不要开启任何编译优化）

   ```c
   #include <stdio.h>
   
   int main() {
     int a = -0x80000000;
     int b = -1;
     printf("%d\n", a / b);
     return 0;
   }
   ```

   在 x86-64（Ubuntu + gcc）下编译运行结果指令如下：

   ```bash
   $ gcc -o i i.c
   $ ./i
   ```

   结果如下：

   ```bash
   Floating point exception (core dumped)
   ```

    RISCV-32 的 qemu 模拟器中编译运行指令如下：

   ```bash
   $ riscv64-unknown-elf-gcc -march=rv32im -mabi=ilp32 i.c
   $ qemu-riscv32 a.out
   ```

   结果如下：

   ```bash
   -2147483648
   ```



## 参考材料

借鉴了 Java-Antlar 参考实现