# dictionary of operators to assembly string
# ignore the starting '\t' and trailing '\n'

UNOPR2ASM = {
    '-': "neg t0, t0",
    '!': "seqz t0, t0",
    '~': "not t0, t0",

}

BIOPR2ASM = {
    '+': "add t0, t0, t1",
    '-': "sub t0, t0, t1",
    '*': "mul t0, t0, t1",
    '/': "div t0, t0, t1",
    '%': "rem t0, t0, t1",
    '==': "seqz t0, t0",
    '!=': "snez t0, t0",
    '<': "slt t0, t0, t1",
    '>': "sgt t0, t0, t1",
    '<=': "sgt t0, t0, t1\n"  # not >
          "\txori t0, t0, 1",
    '>=': "slt t0, t0, t1\n"
          "\txori t0, t0, 1"
}
