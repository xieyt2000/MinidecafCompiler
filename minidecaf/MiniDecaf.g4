grammar MiniDecaf;

//parser
program
    : function EOF;

function
    : varType Identifier '(' ')' '{' blockItem* '}';

// 'type' conflict with python keyword, so rename to varType
varType
    : 'int';

blockItem
    : declaration
    | statement;

statement
    : 'return' expression ';' # retStatement
    | expression? ';'  # exprStatement
    ;

declaration
    : varType Identifier ('=' expression)? ';';

expression
    : assignment;

assignment
    : logicalOr
    | Identifier '=' expression;

logicalOr
    : logicalAnd
    | logicalOr '||' logicalAnd;

logicalAnd
    : equality
    | logicalAnd ('&&') equality;

equality
    : relational
    | equality ('=='|'!=') relational;

relational
    : additive
    | relational ('<'|'>'|'<='|'>=') additive;

additive
    : multiplicative
    | additive ('+'|'-') multiplicative;

multiplicative
    : unary
    | multiplicative ('*'|'/'|'%') unary;

unary
    : primary
    | ('-'|'~'|'!') unary;

primary
    :  Integer # numPrimary
    | '(' expression ')' # parenthesizedPrimary
    | Identifier # identPrimary
    ;


// lexer
WhiteSpace
    : [ \t\r\n\u000C] -> skip;

Identifier
    : [a-zA-Z_] [a-zA-Z_0-9]*;

Integer
    : [0-9]+;
