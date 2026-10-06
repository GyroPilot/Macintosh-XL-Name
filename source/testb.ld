OUTPUT_FORMAT("binary")
SECTIONS {
  . = 0;
  .text : { xltestb.o(.text) *(.text*) *(.rodata*) *(.data*) *(.bss*) *(COMMON) }
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
