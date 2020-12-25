# Step11 实验报告

2018011334 谢云桐



## 实验内容

本阶段实现指针，语法规则和实验指导书类似。为了实现指针，需要先实现左值分析和类型检查，内容较多。

### 左值分析

首先在类型基类中加入左右值属性 ：

```python
class ValueCategory(Enum):
    lvalue = 1
    rvalue = 2


class MiniDecafType(abc.ABC):

    def __init__(self, name, value_cat: ValueCategory = ValueCategory.rvalue):
        self.name = name
        self.value_cat = value_cat
        
    @abc.abstractmethod
    def value_category_cast(self, target_value_cat: ValueCategory):
        pass
```

然后在各子类中实现左值相关方法，并在 `MainVisitor` 中实现左值分析，如在读入变量左值时使用地址：

```python
def __read_var(self, symbol: Symbol):
    self.asm_str += (f"# read variable {symbol.name} as lvalue\n"
                     f"\taddi t0, fp, {symbol.offset}\n")

def __read_global_var(self, name):
    self.asm_str += (f"# read global variable {name} as lvalue\n"
                     f"\tla t0, {name}\n")
```

检查左值使用并且在将左值作为右值使用时将地址转化为值：

```python
def type_check(self, type_actual: MiniDecafType, type_expect=MiniDecafType,
               value_cat_req=ValueCategory.rvalue) -> MiniDecafType:
    if value_cat_req == ValueCategory.lvalue and type_actual.value_cat == ValueCategory.rvalue:
        raise Exception('Expect lvalue but got rvalue.')
    if value_cat_req == ValueCategory.rvalue and type_actual.value_cat == ValueCategory.lvalue:
        self.__pop('t0')
        self.asm_str += ("# cast lvalue to rvalue\n"
                         f"\t lw t0, 0(t0)\n")
        self.__push('t0')
        return type_actual.value_category_cast(ValueCategory.rvalue)
    return type_actual.value_category_cast(value_cat_req)
```

### 类型检查

在左值分析中定义的 `type_check` 中加入下句完成类型检查的基础函数：

```python
if not issubclass(type(type_actual), type_expect):
        raise Exception(f'Expect type {type(type_expect).__name__} but got {type(type_actual).__name__}.')
```

在有类型要求的地方加入类型检查，如 `Equality` 逻辑表达式：

```python
def visitEquality(self, ctx: MiniDecafParser.EqualityContext) -> MiniDecafType:
    if len(ctx.children) > 1:  # equ op rel
        equ_type = self.__type_check(self.visit(ctx.equality()))
        rel_type = self.__type_check(self.visit(ctx.relational()))
        if equ_type != rel_type:
            raise Exception("Equality operator with different type.")
```

### 指针

实现指针类：

```python
class PointerType(MiniDecafType):

    def __init__(self, level, value_cat=ValueCategory.rvalue):
        super().__init__(f"PointerType<{level}>", value_cat)
        self.level = level  # level of pointers == num of *

    def __eq__(self, other):
        return isinstance(other, PointerType) and self.level == other.level

    def get_size(self):
        return 4

    def reference(self):
        if self.value_cat == ValueCategory.lvalue:
            return PointerType(self.level + 1)
        raise Exception('Cannot reference rvalue pointer.')

    def dereference(self):
        if self.level > 1:
            return PointerType(self.level - 1, ValueCategory.lvalue)
        else:
            return IntType(ValueCategory.lvalue)

    def value_category_cast(self, target_value_cat: ValueCategory):
        return PointerType(self.level, target_value_cat)
```

有关指针的运算符：

```python
def visitOpUnary(self, ctx: MiniDecafParser.OpUnaryContext) -> MiniDecafType:
    var_type: MiniDecafType = self.visit(ctx.unary())
    operator: str = ctx.children[0].getText()
    if operator == '*':
        return self.__type_check(var_type).dereference()
    elif operator == '&':
        return var_type.reference()
```



## 思考题

1. 为什么类型检查要放到名称解析之后？

   > 名称解析的阶段任务就是把 **AST 中出现的每个变量名关联到对应的变量**
   >
   > ​	-- step7 实验指导

   因此没有名称解析，编译器不知道每个变量名所对应的符号表变量，自然也不知道它的类型，无法检查

2. MiniDecaf 中一个值只能有一种类型，但在很多语言中并非如此，请举出一个反例。

   在 C 语言中，`int a = 1` 和 `char a = 1` 都是合法的写法，1这个值在这里有不同的类型。

   在 python，js 等脚本语言中一个变量没有特定的类型，如 `a = 1 \ a = []`。

   C 语言的 union 可以在同一块内存中存储不同类型的变量。

2. 在本次实验中我们禁止进行指针的比大小运算。请问如果要实现指针大小比较需要注意什么问题？可以和原来整数比较的方法一样吗？

   根据 C 语言的标准，指针大小的比较需要进行类型检查（包括指针的级数），并且要注意指针是无符号整数。



## 参考材料

借鉴了 Java-Antlar 参考实现

