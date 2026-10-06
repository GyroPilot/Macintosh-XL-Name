| Glue between the C code (nbp.c) and the Macintosh Toolbox - TEST B
| gcc m68k calling convention: args on the stack (4(sp), 8(sp)...), result in d0
| (pointers also in a0); d2-d7/a2-a6 preserved.
        .text
        .macro  OSPB name, trap         | long name(void *pb): synchronous PB call
        .globl  \name
\name:  movea.l 4(%sp),%a0
        move.l  %d2,-(%sp)
        .short  \trap
        move.l  (%sp)+,%d2
        ext.l   %d0
        rts
        .endm
        OSPB    pb_control, 0xA004
        OSPB    pb_hcreate, 0xA208
        OSPB    pb_hopen,   0xA200
        OSPB    pb_write,   0xA003
        OSPB    pb_close,   0xA001
        OSPB    pb_seteof,  0xA012
        OSPB    pb_hgetfinfo, 0xA20C
        OSPB    pb_hsetfinfo, 0xA20D
        OSPB    pb_flushvol, 0xA013

        .globl  newptr_sys_clear        | void *newptr_sys_clear(long size)
newptr_sys_clear:
        move.l  4(%sp),%d0
        move.l  %d2,-(%sp)
        .short  0xA71E                  | _NewPtrSysClear
        move.l  (%sp)+,%d2
        move.l  %a0,%d0
        rts

        .globl  gestalt                 | long gestalt(long selector, long *response)
gestalt:
        move.l  4(%sp),%d0
        move.l  %d2,-(%sp)
        .short  0xA1AD                  | _Gestalt
        move.l  (%sp)+,%d2
        movea.l 8(%sp),%a1
        move.l  %a0,(%a1)
        ext.l   %d0
        rts

        .globl  get_resource            | void **get_resource(long type, long id)
get_resource:
        move.l  %d2,-(%sp)
        subq.l  #4,%sp
        move.l  12(%sp),-(%sp)          | type
        move.w  22(%sp),-(%sp)          | id (low word)
        .short  0xA9A0                  | _GetResource
        move.l  (%sp)+,%d0
        move.l  (%sp)+,%d2
        movea.l %d0,%a0
        rts

        .globl  get_g                   | void *get_g(void)
get_g:  move.l  gptr(%pc),%d0
        movea.l %d0,%a0
        rts
        .globl  set_g                   | void set_g(void *)
set_g:  lea     gptr(%pc),%a0
        move.l  4(%sp),(%a0)
        rts
        .globl  get_oldname             | unsigned char *get_oldname(void)
get_oldname:
        lea     oldname(%pc),%a0
        move.l  %a0,%d0
        rts

        .globl  install_filter          | void install_filter(void)
install_filter:
        lea     oldfilter(%pc),%a0
        move.l  0x029A.w,(%a0)          | JGNEFilter
        lea     gne_filter(%pc),%a0
        move.l  %a0,0x029A.w
        rts

| GetNextEvent filter: runs in application context once the Finder is up.
gne_filter:
        movem.l %d0-%d2/%a0-%a1,-(%sp)
        bsr     xl_tick
        movem.l (%sp)+,%d0-%d2/%a0-%a1
        move.l  oldfilter(%pc),-(%sp)
        beq.s   1f
        rts                             | on to the previous filter
1:      addq.l  #4,%sp
        rts

        .even
gptr:      .long 0
oldfilter: .long 0
