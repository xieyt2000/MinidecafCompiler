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
