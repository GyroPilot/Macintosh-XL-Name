import struct, sys
from unicorn import *
from unicorn.m68k_const import *
code = open('xltest_code.bin','rb').read()
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
import os
B1 = open([p for p in ('icons/LisaXL_icon_B1.ICN#.bin','../icon/LisaXL_icon_B1.ICN#.bin') if os.path.exists(p)][0],'rb').read()
# a list shaped like a later System: empty placeholders, long names
L = ["Macintosh","Macintosh XL","Macintosh 512K enhanced","Macintosh Plus","Macintosh SE","","Macintosh IIx","Macintosh LC 475","Macintosh Quadra 840AV"]
def exp(i): return [("Macintosh XL" if k==i-1 else x) for k,x in enumerate(L)]
(names, used), st, guard, n0 = run(L, pin=(480,640), mach=8)
check('LC 475 entry (longer name) renamed, others intact', names == exp(8) and used == st['size'] == n0-4 and guard == b'\xEE'*16)
check('  picture replaced with B1', st['icon'] == B1 and st['icon_guard'])
(names, used), st, guard, n0 = run(L, pin=(342,512), mach=5)
check('Runs on a 512x342 screen too (SE entry renamed, same length)', names == exp(5) and st['size'] == n0)
(names, used), st, guard, n0 = run(L, mach=6)
check('Empty placeholder entry filled in (list grows)', names == exp(6) and st['size'] == n0+12 and used == st['size'])
(names, used), st, guard, n0 = run(L, mach=9)
check('Last entry renamed', names == exp(9))
(names, used), st, guard, n0 = run(L, mach=1)
check('First entry renamed', names == exp(1))
(names, used), st, guard, n0 = run(L, mach=10)
check('Machine number past the end of the list: names untouched', names == L and st['size'] == n0)
(names, used), st, guard, n0 = run(L, mach=89)
check('Machine number far past the end: names untouched', names == L)
(names, used), st, guard, n0 = run(L, gestalt_ok=False)
check('Gestalt unavailable: nothing touched', names == L and st['icon'] == st['old_icon'])
(names, used), st, guard, n0 = run(L, mach=8, have_res=False)
check('Name list missing: clean exit, picture still replaced', st['icon'] == B1)
print('ALL PASS' if ok else 'FAILURES'); sys.exit(0 if ok else 1)
