# Step10 实验报告

2018011334 谢云桐



## 实验内容

本阶段实现全局变量，语法规则十分简单：

```ANTLR
globalVar
    : varType Identifier ('=' Integer)? ';';
```

需要加入两个字典记录已经定义/声明的全局变量及其类型，代码如下：

```python
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
```



## 思考题

1. 请给出将全局变量 `a` 的值读到寄存器 `t0` 所需的 riscv 指令序列。

   ```assembly
   la t1, a
   lw t0, 0(t1)
   ```

   

## 参考材料

借鉴了 Java-Antlar 参考实现

