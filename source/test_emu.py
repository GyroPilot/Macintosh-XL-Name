import struct, sys
from unicorn import *
from unicorn.m68k_const import *
code = open('xlname_code.bin','rb').read()
NAMES = ["Macintosh","Macintosh XL","Macintosh 512K enhanced","Macintosh Plus","Macintosh SE","Macintosh II","Macintosh IIx"]
def strlist(names):
    b = struct.pack('>H', len(names))
    for n in names: b += bytes([len(n)]) + n.encode('mac_roman')
    return b
def parse(b):
    n = struct.unpack('>H', b[:2])[0]; o=2; out=[]
    for _ in range(n):
        l=b[o]; out.append(b[o+1:o+1+l].decode('mac_roman')); o+=1+l
    return out, o
def run(names, pin=(364,720), have_res=True, mach=4, micn=-16482, have_icon=True, icon_size=256, gestalt_ok=True):
    uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
    uc.ctl_set_cpu_model(UC_CPU_M68K_M68000)
    uc.mem_map(0, 0x100000)
    CODE, STACK, MP, DATA, RET = 0x20000, 0x80000, 0x30000, 0x40000, 0x7F000
    uc.mem_write(CODE, code)
    uc.mem_write(RET, b'\x4e\x71'*4)
    uc.mem_write(0x838, struct.pack('>HH', *pin))
    uc.mem_write(0x118, struct.pack('>I', 0xAAAA0000))   # TheZone (app)
    uc.mem_write(0x2A6, struct.pack('>I', 0x00002000))   # SysZone
    data = strlist(names)
    st = {'size': len(data), 'traps': [], 'zone_at_get': None, 'nopurge': False}
    uc.mem_write(DATA, data + b'\xEE'*64)                # guard bytes after
    uc.mem_write(MP, struct.pack('>I', DATA))
    IMP, IDATA = 0x30010, 0x50000
    OLDICON = bytes(range(256))
    uc.mem_write(IDATA, OLDICON + b'\xEE'*32); uc.mem_write(IMP, struct.pack('>I', IDATA))
    st['zone_at_icon'] = None
    regs0 = {}
    for i,r in enumerate([UC_M68K_REG_D3,UC_M68K_REG_D4,UC_M68K_REG_D5,UC_M68K_REG_D6,UC_M68K_REG_D7,UC_M68K_REG_A2,UC_M68K_REG_A3,UC_M68K_REG_A4]):
        uc.reg_write(r, 0x11110000+i); regs0[r]=0x11110000+i
    sp = STACK - 4
    uc.mem_write(sp, struct.pack('>I', RET))
    uc.reg_write(UC_M68K_REG_A7, sp)
    pc = CODE; steps = 0
    while pc != RET:
        steps += 1
        assert steps < 5000, 'runaway'
        op = struct.unpack('>H', uc.mem_read(pc,2))[0]
        if op & 0xF000 == 0xA000:
            st['traps'].append(hex(op))
            a7 = uc.reg_read(UC_M68K_REG_A7)
            a0in = uc.reg_read(UC_M68K_REG_A0); a1in = uc.reg_read(UC_M68K_REG_A1); d0in = uc.reg_read(UC_M68K_REG_D0)
            for r in (UC_M68K_REG_A0,UC_M68K_REG_A1,UC_M68K_REG_D1,UC_M68K_REG_D2): uc.reg_write(r, 0xDEADBEEE)
            if op == 0xA9A0:
                rid, typ = struct.unpack('>hI', uc.mem_read(a7,6))
                zone = struct.unpack('>I', uc.mem_read(0x118,4))[0]
                if typ == 0x53545223:
                    assert rid == -16395, rid
                    st['zone_at_get'] = zone; h = MP if have_res else 0
                else:
                    assert typ == 0x49434E23 and rid == micn, (hex(typ), rid)
                    st['zone_at_icon'] = zone; h = IMP if have_icon else 0
                uc.mem_write(a7+6, struct.pack('>I', h))
                uc.reg_write(UC_M68K_REG_A7, a7+6)
            elif op == 0xA1AD:
                sel = struct.pack('>I', d0in)
                if not gestalt_ok: uc.reg_write(UC_M68K_REG_D0, (-5551) & 0xFFFFFFFF)
                else:
                    assert sel in (b'mach', b'micn'), sel
                    uc.reg_write(UC_M68K_REG_A0, (mach if sel==b'mach' else micn) & 0xFFFFFFFF); uc.reg_write(UC_M68K_REG_D0, 0)
            elif op == 0xA025:
                assert a0in in (MP, IMP)
                uc.reg_write(UC_M68K_REG_D0, st['size'] if a0in == MP else icon_size)
            elif op == 0xA024:
                assert a0in == MP
                st['size'] = d0in; uc.reg_write(UC_M68K_REG_D0, 0)
            elif op == 0xA02E:
                s,d,n = a0in,a1in,d0in
                assert 0 <= n < 4096
                buf = bytes(uc.mem_read(s,n)); uc.mem_write(d,buf)
                uc.reg_write(UC_M68K_REG_D0, 0)
            elif op == 0xA04A:
                assert a0in in (MP, IMP); st['nopurge' if a0in == MP else 'icon_nopurge'] = True
            else: raise Exception('unexpected trap '+hex(op))
            pc += 2; uc.reg_write(UC_M68K_REG_PC, pc); continue
        try: uc.emu_start(pc, 0xFFFFFFFF, count=1)
        except Exception as e: raise Exception("at pc %x op %04x: %s" % (pc-CODE, op, e))
        pc = uc.reg_read(UC_M68K_REG_PC)
    assert uc.reg_read(UC_M68K_REG_A7) == STACK, 'stack unbalanced'
    for r,v in regs0.items(): assert uc.reg_read(r) == v, 'register not preserved'
    assert struct.unpack('>I', uc.mem_read(0x118,4))[0] == 0xAAAA0000, 'zone not restored'
    out = bytes(uc.mem_read(DATA, st['size']))
    guard = bytes(uc.mem_read(DATA+max(st['size'],len(data)), 16))
    st['icon'] = bytes(uc.mem_read(IDATA,256)); st['icon_guard'] = bytes(uc.mem_read(IDATA+256,32)) == b'\xEE'*32; st['old_icon'] = OLDICON
    return parse(out), st, guard, len(data)
ok = True
def check(label, cond):
    global ok; print(('PASS ' if cond else 'FAIL ')+label); ok &= bool(cond)
# 1 Lisa screen, standard list
(names, used), st, guard, n0 = run(NAMES)
exp = [("Macintosh XL" if x=="Macintosh Plus" else x) for x in NAMES]
check('Lisa 720x364: Plus entry renamed, others intact', names == exp)
check('  list still parses to its full new size', used == st['size'] == n0-2)
check('  loaded in system heap, kept non-purgeable', st['zone_at_get']==0x2000 and st['nopurge'])
check('  nothing written past the list', guard == b'\xEE'*16)
# 2 Lisa square-pixel screen
(names, used), st, guard, n0 = run(NAMES, pin=(431,608))
check('Lisa 608x431: renamed', names == exp)
# 3 real Plus
(names, used), st, guard, n0 = run(NAMES, pin=(342,512))
check('Real Plus 512x342: untouched, no Toolbox calls', names == NAMES and st['traps']==[])
# 4 Plus entry last in list (empty tail)
L = NAMES[:4]
(names, used), st, guard, n0 = run(L)
check('Plus entry last in list', names == L[:3]+["Macintosh XL"] and guard == b'\xEE'*16)
# 5 short variant name (list must grow)
L = ["A","Mac Plus","B","CC"]
(names, used), st, guard, n0 = run(L)
check('Shorter "Mac Plus" entry (list grows)', names == ["A","Macintosh XL","B","CC"] and st['size']==n0+4 and used==st['size'])
# 6 no Plus entry
L = ["Macintosh","Macintosh SE","Pl","us"]
(names, used), st, guard, n0 = run(L)
check('No Plus entry: untouched', names == L and st['size']==n0)
# 7 resource missing
(names, used), st, guard, n0 = run(NAMES, have_res=False)
check('Resource missing: clean exit', names == NAMES)
# 8 empty list
(names, used), st, guard, n0 = run([])
check('Empty list: clean exit', names == [])
import os
LISA = open([p for p in ('icons/LisaXL_icon_A1.ICN#.bin','../icon/LisaXL_icon_A1.ICN#.bin') if os.path.exists(p)][0],'rb').read()
(names, used), st, guard, n0 = run(NAMES)
check('Icon: Plus picture replaced by Lisa A1 (icon + mask, 256 bytes)', st['icon'] == LISA and st['icon_guard'] and st.get('icon_nopurge') and st['zone_at_icon'] == 0x2000 and names == exp)
(names, used), st, guard, n0 = run(NAMES, pin=(342,512))
check('Icon: real Plus screen, picture untouched', st['icon'] == st['old_icon'])
(names, used), st, guard, n0 = run(NAMES, mach=6)
check('Icon: machine type not Plus, picture untouched', st['icon'] == st['old_icon'] and st['zone_at_icon'] is None)
(names, used), st, guard, n0 = run(NAMES, gestalt_ok=False)
check('Icon: Gestalt unavailable, picture untouched, name still changed', st['icon'] == st['old_icon'] and names == exp)
(names, used), st, guard, n0 = run(NAMES, have_icon=False)
check('Icon: no picture on file, clean exit', st['icon'] == st['old_icon'] and names == exp)
(names, used), st, guard, n0 = run(NAMES, icon_size=128)
check('Icon: picture too small, untouched', st['icon'] == st['old_icon'])
(names, used), st, guard, n0 = run(NAMES, have_res=False)
check('Icon: name list missing, picture still replaced', st['icon'] == LISA)
print('ALL PASS' if ok else 'FAILURES'); sys.exit(0 if ok else 1)
