# Step7 实验报告

2018011334 谢云桐



## 实验内容

本阶段实现块语句，本身语义很简单，主要是引入了作用域的概念，需要将原来的 `symbol_map` 替换成 `symbol_table`，利用栈实现不同作用域中的变量映射。`SymbolTable` 定义如下：

```python
class SymbolTable:
    __symbol_table: List[SymbolMap]

    def __init__(self):
        self.__symbol_table = []

    def lookup_all(self, name):
        # lookup in inner block first
        for symbol_map in reversed(self.__symbol_table):
            if symbol_map.lookup(name) is not None:
                return symbol_map.lookup(name)
        return None

    def lookup_top(self, name):
        return self.__symbol_table[-1].lookup(name)

    def pop_scope(self):
        self.__symbol_table.pop()

    def add_scope(self):
        self.__symbol_table.append(SymbolMap())

    def add_symbol(self, symbol: Symbol):
        self.__symbol_table[-1].add(symbol)
```



## 思考题

1. 请将下述 MiniDecaf 代码中的 `???` 替换为一个 32 位整数，使得程序运行结束后会返回 0。

   ```c++
   int main() {
    int x = ???;
    if (x) {
        return x;
    } else {
        int x = 2;
    }
    return x;
   }
   ```

   `int x = 0;`  在 `if` 语句中进入 `else` 块，定义一个新的 `x`，`else` 块执行结束后作用域被弹出，`return x` 使用的仍是最初定义的 `x`

   

2. 在实验指导中，我们提到“就 MiniDecaf 而言，名称解析的代码也可以嵌入 IR 生成里”，但不是对于所有语言都可以把名称解析嵌入代码生成。试问被编译的语言有什么特征时，名称解析作为单独的一个阶段在 IR 生成之前执行会更好？

   当语言有变量提升（hoisting）特性时，名称解析作为一个单独阶段更好。变量提升指的是变量的作用域为整个代码块，包括其声明之前，相当于将变量的声明提升到了代码块的开头。主流语言中基本只有 Javascript 和 Go 有这一特性，而且其在很多程度上已经不被推荐使用。JavaScript 中示例如下：

   ```javascript
   x = 5; // Assign 5 to x
   
   elem = document.getElementById("demo"); // Find an element
   elem.innerHTML = x;                     // Display x in the element
   
   var x; // Declare x
   ```

   对于有该特性的语言，必须事先构造好每个作用域的变量符号表后再生成IR，否则在前面的赋值语句无法得知后面的定义，因此名称解析作为一个单独的阶段会更好



## 参考材料

借鉴了 Java-Antlar 参考实现

