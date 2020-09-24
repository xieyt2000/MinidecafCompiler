ANTLR_JAR ?= /usr/local/lib/antlr-4.8-complete.jar
i ?= i.c
o ?= o.s
CC = riscv64-unknown-elf-gcc  -march=rv32im -mabi=ilp32
SPIKE = spike --isa=RV32G /usr/local/bin/pk

RUNMD = python3 -m minidecaf $(EXTRA_ARGS)

CLASSPATH = $(ANTLR_JAR):generated

all: run

run: asm
	$(CC) $(o)
	$(SPIKE) a.out ; echo $$?

just_run:
	$(CC) $(o)
	$(SPIKE) a.out ; echo $$?

asm: grammar-py
	$(RUNMD) $(i) $(o)

grammar-py:
	cd minidecaf && java -jar $(ANTLR_JAR) -Dlanguage=Python3 -visitor -o generated MiniDecaf.g4

clean:
	rm -rf generated minidecaf/generated
	rm -rf minidecaf/**__pycache__