ENTRY(sg_run_diagnostic)
SECTIONS { . = 0x09F20100; .text : { *(.text.sg_run_diagnostic) *(.text*) *(.rodata*) } .ARM.exidx : { *(.ARM.exidx*) } }
