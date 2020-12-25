# Step12 实验报告

2018011334 谢云桐



## 实验内容

本阶段实现数组，语法规则和实验指导书类似。本阶段的实验指导中还应该实现指针算术，但是在 step11 中已经实现了，相关内容可以参考上一次的实验报告。

首先实现数组类型，代码如下：

```python
class ArrayType(MiniDecafType):
    size: int
    base_type: MiniDecafType

    def __init__(self, base_type, length):
        super().__init__(f"ArrayType<{base_type}>({length})")
        self.base_type = base_type
        self.size = length * base_type.get_size()

    def __eq__(self, other):
        return isinstance(other, ArrayType) and self.size == other.get_size() and self.base_type == other.base_type

    def get_size(self):
        return self.size

    def reference(self):
        raise Exception("Cannot reference array.")

    def dereference(self):
        raise Exception("Cannot dereference array.")

    def value_category_cast(self, target_value_cat: ValueCategory):
        if target_value_cat == ValueCategory.lvalue:
            raise Exception("Cannot cast array to lvalue.")
        return self
```

然后实现数组的声明，以局部变量为例，代码如下：

```python
def __get_arr_type(self, ctx, arr_name):
    arr_type: MiniDecafType = self.visit(ctx.varType())
    arr_type = arr_type.value_category_cast(ValueCategory.lvalue)
    for i in range(len(ctx.Integer()) - 1, -1, -1):
      length = int(ctx.Integer(i).getText())
      if length > 0x7fffffff:
          raise Exception(f"{length} is too large for int.")
      if length <= 0:
          raise Exception(f"The size of array{arr_name} is negative")
          arr_type = ArrayType(arr_type, length)
		return arr_type

def visitArrayDecl(self, ctx: MiniDecafParser.ArrayDeclContext) -> MiniDecafType:
    arr_name = ctx.Identifier().getText()
    if self.symbol_table.lookup_top(arr_name) is not None:
        raise Exception(f"Redefine variable {arr_name}.")
    arr_type = self.__get_arr_type(ctx, arr_name)
    self.current_function.local_var_count += arr_type.get_size() // 4
    symbol = Symbol(arr_name, -4 * self.current_function.local_var_count, arr_type)
    self.symbol_table.add_symbol(symbol)
    return NoType()
```

最后实现数组/指针的下标访问，代码如下：

```python
    def visitArrayPostfix(self, ctx: MiniDecafParser.ArrayPostfixContext) -> MiniDecafType:
        # postfix[expression]
        postfix_type = self.__type_check(self.visit(ctx.postfix()))
        self.__type_check(self.visit(ctx.expression()), IntType, ValueCategory.rvalue)
        self.__pop('t1')  # expr
        self.__pop('t0')  # postfix
        if isinstance(postfix_type, PointerType):
            self.asm_str += (f"# pointer[int]\n"
                             f"\tslli t1, t1, 2\n"
                             f"\tadd t0, t0, t1\n")
            self.__push('t0')
            return postfix_type.dereference()
        elif isinstance(postfix_type, ArrayType):
            base_type = postfix_type.base_type
            self.asm_str += (f"# arr[int]\n"
                             f"\tli t2, {base_type.get_size()}\n"
                             f"\tmul t1, t1, t2\n"
                             f"\tadd t0, t0, t1\n")
            self.__push('t0')
            return base_type
        else:
            raise Exception(f"Subscript operator applied to {postfix_type}.")
```



## 思考题

1. 设有以下几个函数，其中局部变量 `a` 的起始地址都是 `0x1000`(4096)，请分别给出每个函数的返回值（用一个常量 minidecaf 表达式表示，例如函数 `A` 的返回值是 `*(int*)(4096 + 23 * 4)`）。

   ```c
    int A() {
        int a[100];
        return a[23];
    }
   
    int B() {
        int *p = (int*) 4096;
        return p[23];
    }
   
    int C() {
        int a[10][10];
        return a[2][3];
    }
   
    int D() {
        int *a[10];
        return a[2][3];
    }
   
    int E() {
        int **p = (int**) 4096;
        return p[2][3];
    }
   ```

   B:  `*(int*)(4096+23*4)`

   C:  `*(int*)((4096+2*10*4)+3*4)`

   D:  `*(int*)((*(int**)(4096+2*4))+3*4)`

   E: `*(int*)((*(int**)(4096+2*4))+3*4)`

2. C 语言规范规定，允许局部变量是可变长度的数组（[Variable Length Array](https://en.wikipedia.org/wiki/Variable-length_array)，VLA），在我们的实验中为了简化，选择不支持它。请你简要回答，如果我们决定支持一维的可变长度的数组(即允许类似 `int n = 5; int a[n];` 这种，但仍然不允许类似 `int n = ...; int m = ...; int a[n][m];` 这种)，而且要求数组仍然保存在栈上（即不允许用堆上的动态内存申请，如`malloc`等来实现它），应该在现有的实现基础上做出那些改动？

   > 提示：不能再像现在这样，在进入函数时统一给局部变量分配内存，在离开函数时统一释放内存。
   >
   > 当同时存在>= 2个可变长度的数组时，至少有一个数组的起始地址不能在编译时决定。
   >
   > 你可以认为可变长度的数组的长度不大于0是未定义行为，不需要处理。

   对于非 VLA 的局部变量，编译器的行为不变，即在函数开始前分配栈空间。遇到 VLA 变量声明时，再为 VLA 变量开辟栈空间（此时已经知道 VLA 的长度），也就是说在**运行时**分配 VLA 的栈空间。这样编译时不能确定栈大小，符号表中就不能记录 VLA 的起始地址、长度等信息，我们可以将其储存在栈上，需要使用时从栈上得到其信息。进入/退出函数时可能遇到一些问题，但是就本编译器目前的实现（进入时分配局部变量栈空间、记录 `fp`，退出时 `mv sp, fp`）来看，不需要做额外的处理。

# 

## 参考材料

借鉴了 Java-Antlar 参考实现

