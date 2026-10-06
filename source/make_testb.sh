#!/bin/sh
# Builds TEST B: xlname.s (TESTB) + glue.s + nbp.c -> xltestb_code.bin
set -e
CF="-m68000 -Os -mpcrel -ffreestanding -fno-builtin -fno-tree-loop-distribute-patterns -fno-delete-null-pointer-checks -fomit-frame-pointer -fno-asynchronous-unwind-tables -Wall -Wno-array-bounds"
m68k-linux-gnu-as -m68000 --defsym TESTB=1 -o xltestb.o xlname.s
m68k-linux-gnu-as -m68000 -o glue.o glue.s
m68k-linux-gnu-gcc $CF -c nbp.c -o nbp.o
# position independence: only PC-relative relocations are allowed
if m68k-linux-gnu-objdump -r xltestb.o glue.o nbp.o | grep R_68K | grep -v R_68K_PC; then echo "absolute relocation found"; exit 1; fi
m68k-linux-gnu-ld -T testb.ld -o xltestb_code.bin xltestb.o glue.o nbp.o
sed 's/OUTPUT_FORMAT("binary")//' testb.ld > /tmp/testb_elf.ld
m68k-linux-gnu-ld -T /tmp/testb_elf.ld -o /tmp/testb.elf xltestb.o glue.o nbp.o
if m68k-linux-gnu-nm /tmp/testb.elf | grep -iE ' [tT] ' | awk '{print $1}' | grep -E '[13579bdf]$'; then echo "odd code address"; exit 1; fi
if m68k-linux-gnu-objdump -d /tmp/testb.elf | grep -qiE 'divs|divu|muls\.l|mulu\.l|bfext|extb'; then echo "non-68000 instruction"; exit 1; fi
ls -l xltestb_code.bin
