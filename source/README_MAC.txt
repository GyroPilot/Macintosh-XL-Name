Macintosh XL Name 1.0  (REV B, October 5 2026)
by GyroPilot - github.com/GyroPilot

WHAT IT DOES
An Apple Lisa running MacWorks Plus uses Macintosh Plus ROM code, so System 7 calls the machine a "Macintosh Plus" - on the network and in About This Macintosh. This extension changes that name to "Macintosh XL" and replaces the compact Macintosh picture in About This Macintosh with a picture of a Lisa.

TO INSTALL
Drag "Macintosh XL Name" onto the System Folder icon, let the Finder put it in the Extensions folder, and restart.

TO REMOVE
Drag it out of the Extensions folder and restart. Nothing else is changed.

WHAT IT CHANGES - AND WHAT IT DOES NOT
- Only the machine NAME and PICTURE are changed, and only in memory. The System file is never modified.
- The machine TYPE that installers and compatibility checks read is left alone. Software still sees a Macintosh Plus, exactly as before.
- It does nothing on a real Macintosh Plus (it only acts when the screen is not the standard 512 x 342).

REQUIREMENTS
Apple Lisa / Macintosh XL, MacWorks Plus or MacWorks Plus II, System 7.

THE PICTURE
The Lisa picture is drawn for the standard Lisa screen, where dots are taller than they are wide. On a Lisa with the square-dot screen kit it will look flattened.

IF THE NETWORK NAME DOES NOT CHANGE
Check About This Macintosh first. If it says "Macintosh XL" the extension is working, and the network name was registered before the extension loaded. Please report this, with your System version, at github.com/GyroPilot.

REV B adds the Lisa picture. REV A changed the name only.

This is the first release. It has been tested in a 68000 emulator, and is waiting for confirmation on real Lisa hardware.
