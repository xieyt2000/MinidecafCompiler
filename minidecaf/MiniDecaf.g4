grammar MiniDecaf;

//parser
program
    : function* EOF;

function
    : varType Identifier '(' (varType Identifier (',' varType Identifier)*)? ')' '{' blockItem* '}' # defFunc
    | varType Identifier '(' (varType Identifier (',' varType Identifier)*)? ')' ';' # declareFunc
    ;

// 'type' conflict with python keyword, so rename to varType
varType
    : 'int';

blockItem
    : declaration
    | statement;

statement
    : 'return' expression ';' # retStatement
    | expression? ';' # exprStatement
    | 'if' '(' expression ')' statement ('else' statement)? # ifStatement
    | '{' blockItem* '}' # blockStatement
    | 'while' '(' expression ')' statement # whileStatement
    | 'for' '(' (declaration | expression? ';') expression? ';' expression? ')' statement # forStatement
    | 'do' statement 'while' '(' expression ')' ';' # doWhileStatement
    | 'break' ';' # breakStatement
    | 'continue' ';' # continueStatement
    ;

declaration
    : varType Identifier ('=' expression)? ';';

expression
    : Identifier '=' expression
    | conditional;

conditional
    : logicalOr
    | logicalOr '?' expression ':' conditional;

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
    : postfix
    | ('-'|'~'|'!') unary;

postfix
    : primary
    | Identifier '(' (expression (',' expression)*)? ')';

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

// add comment to help debugging
BlockComment: '/*' .*? '*/' -> skip;
LINECOMMENT: '//' ~[\r\n]* -> skip;
