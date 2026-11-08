# Macintosh XL Name 1.0 (REV F, 5 Nov 2026)

An extension for an Apple Lisa (Macintosh XL) running MacWorks Plus or MacWorks Plus II.
MacWorks runs Macintosh Plus ROM code, so the System calls the machine a
"Macintosh Plus" (System 7.1) or just "Macintosh" (System 7.5), on the network and in
About This Macintosh. This extension changes the name to **Macintosh XL** and replaces
the compact-Mac picture with a Lisa.

Works under System 6.0.2 to 7.5.5. Tested on a real Lisa 2/10: under System 6.0.8 it
shows on the network as "Macintosh XL"; under System 7.1 About This Macintosh shows
"Macintosh XL" with the Lisa picture, and the network name changes too (Asante EN/SC).

## Download

The release disk is on the [Releases page](../../releases): `MacintoshXLName_1_0_REVF.dc42`
(400K Disk Copy 4.2, for the Lisa), `.dsk` (raw image) and `.bin` (MacBinary II).

## Install / remove

Drag **Macintosh XL Name** onto the System Folder icon (the Finder files it in
Extensions) and restart. On System 6 put it straight into the System Folder.
To remove it, drag it out and restart.

## What it changes

- Only the machine **name** and **picture**, and only in memory. The System file is never written.
- It stays resident (about 1.4K) and tail-patches GetResource, so the name and picture
  are right each time a program reads them (System 6 rereads them from the System file
  whenever a program starts).
- It renames this Mac's own model entry in the machine-name list (`STR#` -16395,
  through Gestalt `mach`), so the name changes under System 7.5 as well as 7.1.
- The Gestalt machine **type** is not touched, so installers and compatibility checks
  still see a Macintosh Plus.
- It does nothing on a real Macintosh Plus (it acts only when the screen is not 512 x 342).

## The network name

Other Macs see the Lisa as "<Macintosh Name>: Macintosh XL". Under System 7 that takes
about 15 seconds after the desktop appears: System 7 announces the old name before
extensions load, so the extension announces the new one and withdraws the old one once
the desktop is up. Under System 6 it is right from the start. It needs a working
AppleTalk connection: the BlueSCSI's Wi-Fi network (DaynaPORT) does not carry AppleTalk
(Nov 2026), so use a wired SCSI Ethernet adapter (the Asante EN/SC works) or LocalTalk.

The Lisa picture is drawn for the standard Lisa screen (tall dots); on a Lisa with the
square-dot screen kit it looks flattened.

## History

- **REV F**: the network name changes under System 7 too.
- **REV E**: stays resident; the name changes under System 6 (and the network name with it), and the picture changes at all.
- **REV D**: renames this Mac's own model entry, so the name changes under System 7.5.
- **REV C**: no Gestalt call before System 6.0.4 (REV B stopped with System error ID 12 under 6.0.2 and 6.0.3).
- **REV B**: adds the Lisa picture (icon A1, in `icon/`).
- **REV A**: name only.

## Files

| File | What it is |
|---|---|
| `MacintoshXLName_1_0_REVF.dc42` / `.dsk` / `.bin` | The release (earlier revisions beside it). |
| `source/` | `xlname.s` (68000 assembly), `glue.s`, `nbp.c`, `build.py`, `test_emu.py`, `README_MAC.txt` (the Read Me on the disk). |
| `test/` | Test builds A to C. |
| `icon/` | The Lisa icon: PNG, mask, pixel grid, icon data, drawing scripts. |

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
