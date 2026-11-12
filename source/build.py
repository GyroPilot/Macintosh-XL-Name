#!/usr/bin/env python3
# Builds the "Macintosh XL Name" extension from xlname.bin:
#   MacintoshXLName_1_1.bin - MacBinary II file (type INIT)
import struct, time, sys
import os
TEST = os.environ.get('XL_TEST') in ('1','B')   # XL_TEST=1: test build A, XL_TEST=B: test build B
TESTB = os.environ.get('XL_TEST') == 'B'
NAME = b"Macintosh XL Name TEST C" if TESTB else b"Macintosh XL Name TEST" if TEST else b"Macintosh XL Name"
OUT = 'MacintoshXLName_TEST_C' if TESTB else 'MacintoshXLName_TEST_A' if TEST else 'MacintoshXLName_1_1'
README_MAC = 'README_MAC_TESTC.txt' if TESTB else 'README_MAC_TEST.txt' if TEST else 'README_MAC.txt'
TYPE, CREATOR = b"INIT", b"XLnm"
VERS = "1.1"
code = open('xltestb_code.bin' if TESTB else 'xltest_code.bin' if TEST else 'xlname_code.bin','rb').read()

def pstr(s): return bytes([len(s)]) + s
def vers(short, long_):
    # major(BCD) minor.bug(BCD) stage(0x80=final) non-release, region(0=US)
    return bytes([0x01,0x10,0x80,0x00]) + struct.pack('>H',0) + pstr(short) + pstr(long_)   # 1.1, final

resources = [  # (type, id, attrs, data)
    (b'INIT', 0, 0x50, code),                       # sysHeap + locked
    (b'vers', 1, 0x00, vers(VERS.encode(), (b"TEST C, not for release - renames any Mac" if TESTB else b"TEST A, not for release - renames any Mac" if TEST else b"1.1, MacWorks name, icon and startup icon by GyroPilot"))),
    (b'vers', 2, 0x00, vers(VERS.encode(), b"For Apple Lisa running MacWorks Plus")),
    (b'STR ', -16397, 0x00, pstr(b"This extension makes a Lisa running MacWorks appear as a Macintosh XL, with a Lisa picture. Put it in the Extensions folder and restart.")),
]

def resource_fork(res):
    data = b''; offs = []
    for t,i,a,d in res:
        offs.append(len(data)); data += struct.pack('>I', len(d)) + d
    types = []
    for t,i,a,d in res:
        if t not in types: types.append(t)
    tlist_len = 2 + 8*len(types)
    tlist = struct.pack('>H', len(types)-1); refs = b''
    for t in types:
        items = [(k,r) for k,r in enumerate(res) if r[0]==t]
        tlist += t + struct.pack('>HH', len(items)-1, tlist_len + len(refs))
        for k,(tt,i,a,d) in items:
            refs += struct.pack('>hh', i, -1) + bytes([a]) + offs[k].to_bytes(3,'big') + b'\0\0\0\0'
    body = tlist + refs
    maplen = 28 + len(body)
    hdr = struct.pack('>IIII', 256, 256+len(data), len(data), maplen)
    mp = hdr + b'\0'*4 + b'\0\0' + b'\0\0' + struct.pack('>HH', 28, 28+len(body)) + body
    return hdr + b'\0'*(256-16) + data + mp

def crc16(b):
    c = 0
    for x in b:
        c ^= x << 8
        for _ in range(8): c = ((c << 1) ^ 0x1021) & 0xFFFF if c & 0x8000 else (c << 1) & 0xFFFF
    return c
def macbinary(name, typ, crea, rf, df=b'', when=None):
    t = int((when or time.time()) + 2082844800) & 0xFFFFFFFF
    h = bytearray(128)
    h[1] = len(name); h[2:2+len(name)] = name
    h[65:69] = typ; h[69:73] = crea
    h[83:87] = struct.pack('>I', len(df)); h[87:91] = struct.pack('>I', len(rf))
    h[91:95] = struct.pack('>I', t); h[95:99] = struct.pack('>I', t)
    h[122] = 129; h[123] = 129
    h[124:126] = struct.pack('>H', crc16(bytes(h[:124])))
    pad = lambda b: b + b'\0'*((-len(b)) % 128)
    return bytes(h) + pad(df) + pad(rf)

rf = resource_fork(resources)
open('XLName.rsrc','wb').write(rf)
open(OUT+'.bin','wb').write(macbinary(NAME, TYPE, CREATOR, rf))
print('resource fork', len(rf), 'bytes; code', len(code), 'bytes')

# ---- 400K HFS disk image (raw .dsk and Disk Copy 4.2 .dc42) ----
import machfs
now = int(time.time() + 2082844800) & 0xFFFFFFFF
v = machfs.Volume(); v.name = 'XL Name TEST C' if TESTB else 'XL Name TEST' if TEST else 'XL Name'; v.crdate = v.mddate = now
f = machfs.File(); f.type = TYPE; f.creator = CREATOR; f.rsrc = rf; f.crdate = f.mddate = now
v[NAME.decode()] = f
t = machfs.File(); t.type = b'TEXT'; t.creator = b'ttxt'; t.crdate = t.mddate = now
t.data = open(README_MAC).read().replace('\n', '\r').encode('mac_roman')
v['Read Me'] = t
img = v.write(size=409600, align=512, desktopdb=False, bootable=False)
assert len(img) == 409600
open(OUT+'.dsk', 'wb').write(img)
def cksum(b):
    s = 0
    for i in range(0, len(b), 2):
        s = (s + ((b[i] << 8) | b[i+1])) & 0xFFFFFFFF
        s = ((s >> 1) | ((s & 1) << 31)) & 0xFFFFFFFF
    return s
tags = bytes(9600)                      # 12 tag bytes x 800 sectors, empty
vn = v.name.encode()
hdr = bytes([len(vn)]) + vn + bytes(63 - len(vn))
hdr += struct.pack('>IIIIBBH', len(img), len(tags), cksum(img), cksum(tags[12:]), 0, 0x02, 0x0100)
open(OUT+'.dc42', 'wb').write(hdr + img + tags)
v2 = machfs.Volume(); v2.read(img)
assert v2[NAME.decode()].rsrc == rf and v2[NAME.decode()].type == TYPE
print('disk image ok:', sorted(v2.keys()))
