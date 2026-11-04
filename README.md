# Macintosh XL Name 1.0 (REV C, Nov 4 2026)

A System 7 extension for an Apple Lisa running MacWorks Plus / MacWorks Plus II.
MacWorks runs Macintosh Plus ROM code, so System 7 calls the machine a
"Macintosh Plus". This extension changes that name to **Macintosh XL** and
replaces the compact-Mac picture in About This Macintosh with a Lisa.

- **REV C** (Nov 4 2026): no Gestalt call before System 6.0.4. REV B stopped an XL
  at startup with System error ID 12 under 6.0.2 and 6.0.3, where the Gestalt trap
  does not exist. REV C reads the System version (low-memory `SysVersion`, $15A) first.
- **REV B** (Oct 5 2026): adds the Lisa picture (icon A1, in `icon/`).
- **REV A** (Oct 5 2026): first build, name only.

## Status

**Not yet proven on hardware.** The code passes its tests in a 68000 emulator
(see below). It has not yet run on a real Lisa, on a LisaFPGA, or under any
real copy of System 7.

## Files

| File | What it is |
|---|---|
| `MacintoshXLName_1_0_REVC.dc42` | 400K floppy image (Disk Copy 4.2) holding the extension and a Read Me. Use this on the Lisa. |
| `MacintoshXLName_1_0_REVC.dsk` | The same disk as a raw 400K image (Mini vMac and similar). |
| `MacintoshXLName_1_0_REVC.bin` | The extension alone, as a MacBinary II file. |
| `source/` | `xlname.s` (68000 assembly), `build.py`, `test_emu.py`, `README_MAC.txt`. |
| `icon/` | The approved Lisa icon A1: PNG, mask, pixel grid, icon data, drawing scripts. |

## Install / remove

Drag **Macintosh XL Name** onto the System Folder icon (the Finder files it in
Extensions) and restart. To remove it, drag it out of Extensions and restart.

## What it changes

- At startup it finds the machine-name list in memory (`STR#` -16395, the list
  Apple documents for turning the machine type into a name) and rewrites the
  entry ending in "Plus" to "Macintosh XL".
- It asks the system which picture belongs to this machine (Gestalt selector
  `micn`, documented by Apple as the machine's icon family ID) and overwrites
  that picture (`ICN#`, icon and mask) in memory with the Lisa icon. It does this
  only when the machine type reads as Macintosh Plus.
- Both changes are in memory only. The System file is never written.
- The Gestalt machine **type** is not touched, so installers and compatibility
  checks still see a Macintosh Plus.
- It does nothing when the screen is the standard 512 x 342 of a real
  Macintosh Plus (it reads the cursor-limit rectangle `CrsrPin`).

## What to check on the Lisa

1. Apple menu > About This Macintosh should say "Macintosh XL" and show the
   Lisa picture.
2. The name shown on the network should change from Mac Plus to Macintosh XL.

If the name changes but the picture does not, either the About box does not
take its picture from the `micn` icon, or MacWorks reports a machine type other
than Macintosh Plus.

If 1 works and 2 does not, System 7 registered the network name before the
extension loaded; that needs a second revision (re-registering the name).
If neither changes, the Lisa check or the name list is not what was assumed.

## Assumptions not yet confirmed

- That the "Mac Plus" seen on the network comes from this name list.
- That About This Macintosh draws the `micn` picture, and that the Gestalt
  machine type under MacWorks is Macintosh Plus (4).
- The small 16 x 16 version of the machine picture is not replaced.
- That System 7 registers the network name after extensions load.
- That MacWorks keeps `CrsrPin` at the Lisa screen size (720 x 364 or 608 x 431).
- That a 400K HFS floppy image suits the machine (the image could not be
  opened by hfsutils, which refuses volumes under 800K; the same file on an
  800K test volume read back identically).

## Emulator test (test_emu.py)

The assembled code is run instruction by instruction in a 68000 emulator with
the six Toolbox calls it makes stubbed out. Cases: Lisa 720 x 364, Lisa
608 x 431, real Plus screen, Plus entry last in the list, a shorter "Mac Plus"
entry, no Plus entry, list missing, empty list; and for the picture: replaced on a
Lisa, untouched on a real Plus screen, untouched when the machine type is not
Plus, Gestalt unavailable, picture missing, picture too small; System 6.0.2 and 6.0.3 (no Gestalt call), 6.0.4 (Gestalt used). All pass; registers, stack and
the memory zone are restored and nothing is written past the list.

## Build

    m68k-linux-gnu-as -m68000 -o xlname.o xlname.s
    m68k-linux-gnu-ld -nostdlib -Ttext=0 -e start -o xlname.elf xlname.o
    m68k-linux-gnu-objcopy -O binary -j .text xlname.elf xlname_code.bin

(On moof, Retro68's m68k-apple-macos-as/ld/objcopy. The link step matters there:
without it the `lea newname(%pc)` displacement is left as 0.)
    python3 test_emu.py
    python3 build.py        (needs: pip install machfs)
