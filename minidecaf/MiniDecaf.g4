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
    : logical_or;

logical_or
    : logical_and
    | logical_or '||' logical_and;

logical_and
    : equality
    | logical_and ('&&') equality;

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
    ;


// lexer
WhiteSpace
    : [ \t\r\n\u000C] -> skip;

Identifier
    : [a-zA-Z_] [a-zA-Z_0-9]*;

Integer
    : [0-9]+;
