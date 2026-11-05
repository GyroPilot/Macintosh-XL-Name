Macintosh XL Name 1.0  (REV F, November 5 2026)
by GyroPilot - github.com/GyroPilot

WHAT IT DOES
An Apple Lisa running MacWorks Plus uses Macintosh Plus ROM code, so System 7 calls the machine a "Macintosh Plus" (System 7.1) or just "Macintosh" (System 7.5) - on the network and in About This Macintosh. This extension changes that name to "Macintosh XL" and replaces the compact Macintosh picture with a picture of a Lisa.

TO INSTALL
Drag "Macintosh XL Name" onto the System Folder icon, let the Finder put it in the Extensions folder, and restart.

TO REMOVE
Drag it out of the Extensions folder and restart. Nothing else is changed.

WHAT IT CHANGES - AND WHAT IT DOES NOT
- Only the machine NAME and PICTURE are changed, and only in memory. The System file is never modified.
- It stays in memory (about 1.4K) and fixes the name and picture each time a program reads them, because System 6 reads them again from the System file whenever a program starts.
- The machine TYPE that installers and compatibility checks read is left alone. Software still sees a Macintosh Plus, exactly as before.
- It does nothing on a real Macintosh Plus (it only acts when the screen is not the standard 512 x 342).

REQUIREMENTS
Apple Lisa / Macintosh XL, MacWorks Plus or MacWorks Plus II, System 6.0.2 to 7.5.5. On System 6 there is no Extensions folder: put it straight into the System Folder.

THE PICTURE
The Lisa picture is drawn for the standard Lisa screen, where dots are taller than they are wide. On a Lisa with the square-dot screen kit it will look flattened.

THE NETWORK NAME
Other Macs (and network scanners such as GlobalTalk Sherpa) see this Lisa as "<your Macintosh Name>: Macintosh XL". Under System 7 that takes about 15 seconds after the desktop appears: System 7 announces the old name before extensions load, so the extension announces the new one and withdraws the old one once the desktop is up. Under System 6 it is right from the start. The network name needs a working AppleTalk connection: the BlueSCSI's Wi-Fi network (DaynaPORT) does NOT work for AppleTalk (Nov 2026: a BlueSCSI firmware bug, and Wi-Fi-to-wire bridging), so use a wired SCSI Ethernet adapter (the Asante EN/SC works) or LocalTalk. If the network name does not change, check About This Macintosh first; if it says "Macintosh XL" the extension is working. Please report it, with your System version, at github.com/GyroPilot.

REV F makes the network name change under System 7 too. REV E makes the name change under System 6 (the network name too) and makes the picture change at all: earlier versions changed a copy that System 6 threw away, and the picture never changed anywhere. REV D changes the name on System 7.5 too: it renames the entry for the model MacWorks reports, not only a "...Plus" entry (7.5 lists every 68K model as plain "Macintosh", so REV C changed nothing there). REV C fixes a startup crash (System error ID 12) on a Lisa running System 6.0.2 or 6.0.3. REV B adds the Lisa picture. REV A changed the name only.

Tested in a 68000 emulator: the name reads "Macintosh XL" under System 6.0.8, 7.1 and 7.5.5, and the Lisa picture shows under 7.1 and 7.5.5 (System 6 has no machine picture); System 6.0.2 starts up normally. On a real Lisa 2/10 (MacWorks, EtherTalk) REV E works: under System 6.0.8 the Lisa shows on the network as "Macintosh XL", and under System 7.1 About This Macintosh shows "Macintosh XL" with the Lisa picture (5 Nov 2026). REV F's System 7 network announcement works on the same Lisa under System 7.1 (Asante EN/SC).
