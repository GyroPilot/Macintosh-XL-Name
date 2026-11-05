| Macintosh XL Name  -  REV E  -  Nov 5 2026  -  GyroPilot
| REV E: stays in memory. Under System 6 the name list (STR# -16395) is
| read again from the System file each time an application starts, so a
| one-time edit at startup is lost (the name never changed on 6.0.x, where
| Responder announces it after startup). REV E copies a small patch into the
| system heap and tail-patches _GetResource: whenever anyone gets STR# -16395
| or the machine picture (ICN# 'micn'), this Mac's entry is renamed and the
| picture replaced in the copy returned. Applying it twice changes nothing.
| Installed only on a Lisa screen, like everything else here. The one-time
| edits at startup stay (in a system-heap copy) for anything read before.
| REV D: renames the entry for this Mac's own model (Gestalt 'mach' index into
| STR# -16395), not only a "...Plus" entry: System 7.5.x lists every 68K model
| as plain "Macintosh", so REV C changed nothing on the XL under 7.5.5. The
| "...Plus" search stays as the fallback when Gestalt is missing (System 6.0.3
| and older) or the index is past the list. The picture is now replaced on any
| Lisa screen, whatever model MacWorks reports.
| REV C: no Gestalt call on System 6.0.3 and older, where the trap does not
| exist (System error ID 12 at startup on an XL under 6.0.2 / 6.0.3).
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
        bsr     install
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
        moveq   #0,%d6                  | d6 = this machine's index, 0 = unknown
        cmpi.w  #0x0604,0x015A.w        | SysVersion: Gestalt came with 6.0.4
        bcs.s   noidx
        move.l  #0x6D616368,%d0         | 'mach'
        .short  0xA1AD                  | _Gestalt
        tst.w   %d0
        bne.s   noidx
        move.l  %a0,%d6
noidx:
| --- h = GetResource('STR#', -16395), a copy in the system heap ---
        move.l  #0x53545223,%d0         | 'STR#'
        move.w  #-16395,%d1
        bsr     sysres
        tst.l   %d0
        beq     done
        movea.l %d0,%a2                 | a2 = handle
        tst.l   (%a2)
        beq     done
| --- rename_h: a2 = loaded STR# -16395 handle, d6 = model index (0 = unknown).
|     Also called by the resident patch. Uses d3-d7/a0-a1.
rename_h:

| --- scan the list for an entry ending in "Plus" ---
        movea.l (%a2),%a0
        move.w  (%a0)+,%d3              | number of strings
        ble     done
        moveq   #2,%d4                  | d4 = offset of current string
        tst.l   %d6
        ble.s   loop                    | model unknown: look for "...Plus"
        moveq   #0,%d0
        move.w  %d3,%d0
        cmp.l   %d0,%d6
        bgt.s   loop                    | past the list: look for "...Plus"
tloop:
        moveq   #0,%d5
        move.b  (%a0),%d5               | d5 = length of current string
        subq.l  #1,%d6
        beq.s   chkown                  | this is the machine's own entry
        lea     1(%a0,%d5.w),%a0
        add.w   %d5,%d4
        addq.w  #1,%d4
        bra.s   tloop
chkown:                                 | already "Macintosh XL"? then nothing to do
        move.l  %a0,-(%sp)
        lea     newname(%pc),%a1
        moveq   #NEWLEN,%d0             | NEWLEN+1 bytes: length and text
ckl:    cmpm.b  (%a0)+,(%a1)+
        dbne    %d0,ckl
        movea.l (%sp)+,%a0
        beq     done
        bra     found
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
        cmpi.w  #0x0604,0x015A.w        | SysVersion: Gestalt came with 6.0.4
        bcs.s   idone
        move.l  #0x6D69636E,%d0         | 'micn' = machine icon family ID
        .short  0xA1AD                  | _Gestalt
        tst.w   %d0
        bne.s   idone
        move.l  %a0,%d1                 | d1 = resource ID
        move.l  #0x49434E23,%d0         | 'ICN#'
        bsr     sysres
        tst.l   %d0
        beq.s   idone
        movea.l %d0,%a2
        tst.l   (%a2)
        beq.s   idone
put_icon:                               | a2 = loaded ICN# handle (also from the patch)
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

| =====================================================================
| sysres: d0 = handle of resource (type d0.l, ID d1.w) in the SYSTEM heap,
| or 0. GetResource with TheZone = SysZone; if the resource was already
| loaded elsewhere (the application heap, under System 6), ReleaseResource
| and load it again, so our edit survives application launches.
| Keeps d2-d7/a2-a4 and TheZone (traps may change d0-d2/a0-a1).
| =====================================================================
sysres:
        movem.l %d3-%d4/%a2,-(%sp)
        move.l  %d0,%d4
        move.w  %d1,%d3
        bsr.s   sysget
        beq.s   sysout
        movea.l %d0,%a2
        movea.l %a2,%a0
        .short  0xA126                  | _HandleZone
        cmpa.l  0x02A6.w,%a0
        beq.s   sysok                   | already in the system heap
        move.l  %a2,-(%sp)
        .short  0xA9A3                  | _ReleaseResource
        bsr.s   sysget
        beq.s   sysout
        movea.l %d0,%a2
        movea.l %a2,%a0
        .short  0xA126                  | _HandleZone
        cmpa.l  0x02A6.w,%a0
        beq.s   sysok
        moveq   #0,%d0                  | still not in the system heap: leave it
        bra.s   sysout
sysok:
        move.l  %a2,%d0
sysout:
        movem.l (%sp)+,%d3-%d4/%a2
        tst.l   %d0
        rts

sysget:                                 | d0 = GetResource(d4, d3) with TheZone = SysZone
        move.l  0x0118.w,-(%sp)         | save TheZone
        move.l  0x02A6.w,0x0118.w       | TheZone = SysZone
        subq.l  #4,%sp
        move.l  %d4,-(%sp)
        move.w  %d3,-(%sp)
        .short  0xA9A0                  | _GetResource
        move.l  (%sp)+,%d0
        move.l  (%sp)+,0x0118.w         | restore TheZone
        tst.l   %d0
        rts

| =====================================================================
| install: copy this code into the system heap and tail-patch _GetResource
| =====================================================================
install:
        moveq   #0,%d6                  | model index, 0 = unknown
        moveq   #0,%d5                  | d5 = 1 when the picture ID is known
        moveq   #0,%d4
        cmpi.w  #0x0604,0x015A.w        | Gestalt came with 6.0.4
        bcs.s   inst1
        move.l  #0x6D616368,%d0         | 'mach'
        .short  0xA1AD                  | _Gestalt
        tst.w   %d0
        bne.s   inst0
        move.l  %a0,%d6
inst0:  move.l  #0x6D69636E,%d0         | 'micn'
        .short  0xA1AD                  | _Gestalt
        tst.w   %d0
        bne.s   inst1
        move.l  %a0,%d4
        moveq   #1,%d5
inst1:  move.l  #codeend-start,%d0
        .short  0xA51E                  | _NewPtr,SYS
        tst.w   %d0
        bne.s   instx
        movea.l %a0,%a3                 | a3 = resident copy
        movea.l %a0,%a1
        lea     start(%pc),%a0
        move.l  #codeend-start,%d0
        .short  0xA02E                  | _BlockMove
        move.l  %d6,machv-start(%a3)
        move.w  %d4,micnv-start(%a3)
        move.w  %d5,micnok-start(%a3)
        move.w  #0x01A0,%d0             | _GetResource (A9A0), old-style number
        .short  0xA146                  | _GetTrapAddress
        move.l  %a0,oldgr-start(%a3)
        lea     patch-start(%a3),%a0
        move.w  #0x01A0,%d0
        .short  0xA047                  | _SetTrapAddress
instx:  rts

| =====================================================================
| patch: FUNCTION GetResource(theType: ResType; theID: INTEGER): Handle
| Calls the real one, then fixes up the copy it returns.
| Stack on entry: 0 return, 4 ID, 6 type, 10 result.
| =====================================================================
patch:
        subq.l  #4,%sp                  | result space        (ID 8, type 10)
        move.l  10(%sp),-(%sp)          | type                (ID 12, type 14)
        move.w  12(%sp),-(%sp)          | ID
        move.l  oldgr(%pc),%a0
        jsr     (%a0)                   | real GetResource
        move.l  (%sp)+,%d0
        move.l  %d0,10(%sp)             | our caller's result
        beq.s   pret
        movem.l %d3-%d7/%a2-%a4,-(%sp)  | +32
        movea.l %d0,%a2
        tst.l   (%a2)
        beq.s   pdone                   | not loaded (SetResLoad false) or purged
        cmpi.l  #0x53545223,32+6(%sp)   | 'STR#'
        bne.s   picn
        cmpi.w  #-16395,32+4(%sp)
        bne.s   pdone
        move.l  machv(%pc),%d6
        bsr     rename_h
        bra.s   pdone
picn:   cmpi.l  #0x49434E23,32+6(%sp)   | 'ICN#'
        bne.s   pdone
        move.w  micnok(%pc),%d0
        beq.s   pdone
        move.w  micnv(%pc),%d0
        cmp.w   32+4(%sp),%d0
        bne.s   pdone
        bsr     put_icon
pdone:  movem.l (%sp)+,%d3-%d7/%a2-%a4
pret:   movea.l (%sp)+,%a0
        addq.l  #6,%sp                  | pop ID and type; result stays
        jmp     (%a0)

        .even
oldgr:  .long   0
machv:  .long   0
micnv:  .short  0
micnok: .short  0

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
codeend:
