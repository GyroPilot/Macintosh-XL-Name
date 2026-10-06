| Macintosh XL Name  -  REV B  -  Oct 5 2026  -  GyroPilot
| TEST B (--defsym TESTB=1, linked with glue.s and nbp.c): TEST BUILD plus a
| network re-announce of the model name and a log file on the startup disk.
| TEST BUILD (assemble with --defsym TESTBUILD=1): for trying the mechanism on
| any Mac. No Lisa check; renames the entry of whatever machine it runs on and
| always swaps the machine picture (icon B1). Not for release.
| REV B: also replaces the machine picture (About This Macintosh) with a Lisa.
| REV A: first build, name only.
| System 7 extension (INIT) for an Apple Lisa running MacWorks Plus.
| Renames the machine-name string "Macintosh Plus" to "Macintosh XL"
| in memory only (STR# -16395 in the System file is never written).
| The Gestalt machine TYPE is left alone, so installers still see a Plus.
| The machine picture (ICN# whose ID Gestalt 'micn' returns) is overwritten in
| memory the same way, only when Gestalt 'mach' says Macintosh Plus (4).
| Does nothing on a standard 512x342 Macintosh Plus screen.

        .ifdef TESTB
        .set    TESTBUILD,1
        .endif
        .text
        .globl  start
start:
        movem.l %d3-%d7/%a2-%a4,-(%sp)
        .ifdef TESTB
        lea     start(%pc),%a0          | keep this code in memory after startup
        .short  0xA128                  | _RecoverHandle
        move.l  %a0,-(%sp)
        .short  0xA992                  | _DetachResource
        .endif

| --- Lisa check: CrsrPin (cursor pinning rect) bottom/right ---
        .ifndef TESTBUILD
        cmpi.w  #342,0x0838.w
        bne.s   go
        cmpi.w  #512,0x083A.w
        beq.s   exit                    | real Plus screen: leave alone
        .endif
go:
        bsr.s   do_name
        bsr     do_icon
        .ifdef TESTB
        bsr     xl_init                 | network re-announce and log (C code)
        .endif
exit:
        movem.l (%sp)+,%d3-%d7/%a2-%a4
        rts

| =====================================================================
| Rename the "... Plus" entry of STR# -16395 to "Macintosh XL"
| =====================================================================
do_name:
        .ifdef TESTBUILD
        move.l  #0x6D616368,%d0         | 'mach'
        .short  0xA1AD                  | _Gestalt
        tst.w   %d0
        bne     done
        move.l  %a0,%d6                 | d6 = this machine's index in the list
        ble     done
        .endif
| --- h = GetResource('STR#', -16395), loaded into the system heap ---
        move.l  0x0118.w,%d7            | save TheZone
        move.l  0x02A6.w,0x0118.w       | TheZone = SysZone
        subq.l  #4,%sp
        move.l  #0x53545223,-(%sp)      | 'STR#'
        move.w  #-16395,-(%sp)
        .short  0xA9A0                  | _GetResource
        move.l  (%sp)+,%d0
        move.l  %d7,0x0118.w            | restore TheZone
        tst.l   %d0
        beq     done
        movea.l %d0,%a2                 | a2 = handle
        tst.l   (%a2)
        beq     done

| --- scan the list for an entry ending in "Plus" ---
        movea.l (%a2),%a0
        move.w  (%a0)+,%d3              | number of strings
        ble     done
        moveq   #2,%d4                  | d4 = offset of current string
        .ifdef TESTBUILD
        ext.l   %d3
        cmp.l   %d3,%d6
        bgt     done                    | no entry for this machine
tloop:
        moveq   #0,%d5
        move.b  (%a0),%d5               | d5 = length of current string
        subq.l  #1,%d6
        beq     found                   | this is the machine's own entry
        lea     1(%a0,%d5.w),%a0
        add.w   %d5,%d4
        addq.w  #1,%d4
        bra.s   tloop
        .endif
loop:
        moveq   #0,%d5
        move.b  (%a0),%d5               | d5 = its length
        cmpi.w  #4,%d5
        blt.s   next
        lea     1(%a0,%d5.w),%a1        | a1 = just past the string
        cmpi.b  #0x73,-1(%a1)           | 's'
        bne.s   next
        cmpi.b  #0x75,-2(%a1)           | 'u'
        bne.s   next
        cmpi.b  #0x6C,-3(%a1)           | 'l'
        bne.s   next
        cmpi.b  #0x50,-4(%a1)           | 'P'
        beq.s   found
next:
        lea     1(%a0,%d5.w),%a0
        add.w   %d5,%d4
        addq.w  #1,%d4
        subq.w  #1,%d3
        bne.s   loop
        bra     done

| --- replace it: d4 = offset, d5 = old length ---
found:
        .ifdef TESTB
        movem.l %d0/%a0-%a1,-(%sp)      | remember the original name (a0 -> it)
        lea     oldname(%pc),%a1
        moveq   #0,%d0
        move.b  (%a0),%d0
        cmpi.w  #62,%d0
        bhi.s   nosave
        addq.l  #1,%d0
        .short  0xA02E                  | _BlockMove
nosave:
        movem.l (%sp)+,%d0/%a0-%a1
        .endif
        moveq   #NEWLEN,%d6
        sub.l   %d5,%d6                 | d6 = change in size (may be < 0)
        movea.l %a2,%a0
        .short  0xA025                  | _GetHandleSize
        move.l  %d0,%d7                 | d7 = old handle size
        bmi     done
        tst.l   %d6
        ble.s   move_tail
        movea.l %a2,%a0                 | growing: enlarge first
        move.l  %d7,%d0
        add.l   %d6,%d0
        .short  0xA024                  | _SetHandleSize
        tst.w   %d0
        bne     done
move_tail:
        moveq   #0,%d0
        move.w  %d4,%d0
        add.l   %d5,%d0
        addq.l  #1,%d0                  | d0 = offset of the tail
        movea.l (%a2),%a0
        adda.l  %d0,%a0                 | source = old tail
        movea.l %a0,%a1
        adda.l  %d6,%a1                 | dest = new tail
        neg.l   %d0
        add.l   %d7,%d0                 | length = old size - tail offset
        ble.s   put_name
        .short  0xA02E                  | _BlockMove (overlap safe)
put_name:
        movea.l (%a2),%a1
        moveq   #0,%d0
        move.w  %d4,%d0
        adda.l  %d0,%a1
        lea     newname(%pc),%a0
        moveq   #NEWLEN+1,%d0
        .short  0xA02E                  | _BlockMove
        tst.l   %d6
        bge.s   keep
        movea.l %a2,%a0                 | shrinking: trim afterwards
        move.l  %d7,%d0
        add.l   %d6,%d0
        .short  0xA024                  | _SetHandleSize
keep:
        movea.l %a2,%a0
        .short  0xA04A                  | _HNoPurge  (keep our copy)
done:
        rts

| =====================================================================
| Overwrite the machine picture with the Lisa icon
| =====================================================================
do_icon:
        .ifndef TESTBUILD
        move.l  #0x6D616368,%d0         | 'mach'
        .short  0xA1AD                  | _Gestalt
        tst.w   %d0
        bne.s   idone
        cmpa.w  #4,%a0                  | gestaltMacPlus only
        bne.s   idone
        .endif
        move.l  #0x6D69636E,%d0         | 'micn' = machine icon family ID
        .short  0xA1AD                  | _Gestalt
        tst.w   %d0
        bne.s   idone
        move.l  %a0,%d4                 | d4 = resource ID
        move.l  0x0118.w,%d7
        move.l  0x02A6.w,0x0118.w       | TheZone = SysZone
        subq.l  #4,%sp
        move.l  #0x49434E23,-(%sp)      | 'ICN#'
        move.w  %d4,-(%sp)
        .short  0xA9A0                  | _GetResource
        move.l  (%sp)+,%d0
        move.l  %d7,0x0118.w
        tst.l   %d0
        beq.s   idone
        movea.l %d0,%a2
        tst.l   (%a2)
        beq.s   idone
        movea.l %a2,%a0
        .short  0xA025                  | _GetHandleSize
        cmpi.l  #256,%d0
        blt.s   idone
        lea     lisaicon(%pc),%a0
        movea.l (%a2),%a1
        move.l  #256,%d0
        .short  0xA02E                  | _BlockMove
        movea.l %a2,%a0
        .short  0xA04A                  | _HNoPurge
idone:
        rts

        .equ    NEWLEN,12
        .ifdef TESTB
        .globl  oldname
oldname:
        .space  64
        .endif
        .globl  newname
newname:
        .byte   NEWLEN
        .ascii  "Macintosh XL"
        .even

| Lisa icon: 32x32 icon then 32x32 mask
lisaicon:
        .ifdef TESTBUILD
        .incbin "icons/LisaXL_icon_B1.ICN#.bin"    | B1 (approved Oct 5 2026)
        .else
| A1 (approved Oct 5 2026)
        .long   0x00000000
        .long   0x00000000
        .long   0x00000000
        .long   0x00000000
        .long   0x00000000
        .long   0x3FFFFFFC
        .long   0x40000002
        .long   0x47FFC002
        .long   0x480023FA
        .long   0x50001002
        .long   0x500013FA
        .long   0x50001002
        .long   0x50001002
        .long   0x50001002
        .long   0x500013FA
        .long   0x480020E2
        .long   0x47FFC002
        .long   0x40000002
        .long   0x3FFFFFFC
        .long   0x3FFFFFCC
        .long   0x3FFFFFFC
        .long   0x00000000
        .long   0x00000000
        .long   0x1FFFFFF8
        .long   0x1AAAAAA8
        .long   0x25555554
        .long   0x3FFFFFFC
        .long   0x00000000
        .long   0x00000000
        .long   0x00000000
        .long   0x00000000
        .long   0x00000000
        .long   0x00000000
        .long   0x00000000
        .long   0x00000000
        .long   0x00000000
        .long   0x00000000
        .long   0x3FFFFFFC
        .long   0x7FFFFFFE
        .long   0x7FFFFFFE
        .long   0x7FFFFFFE
        .long   0x7FFFFFFE
        .long   0x7FFFFFFE
        .long   0x7FFFFFFE
        .long   0x7FFFFFFE
        .long   0x7FFFFFFE
        .long   0x7FFFFFFE
        .long   0x7FFFFFFE
        .long   0x7FFFFFFE
        .long   0x7FFFFFFE
        .long   0x3FFFFFFC
        .long   0x3FFFFFFC
        .long   0x3FFFFFFC
        .long   0x00000000
        .long   0x00000000
        .long   0x1FFFFFF8
        .long   0x1FFFFFF8
        .long   0x3FFFFFFC
        .long   0x3FFFFFFC
        .long   0x00000000
        .long   0x00000000
        .long   0x00000000
        .long   0x00000000
        .long   0x00000000
        .endif
