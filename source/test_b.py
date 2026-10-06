import struct, sys
from unicorn import *
from unicorn.m68k_const import *
code = open('xltestb_code.bin','rb').read()
R = {n: getattr(sys.modules['unicorn.m68k_const'], 'UC_M68K_REG_'+n) for n in ['D0','D1','D2','D3','D4','D5','D6','D7','A0','A1','A2','A3','A4','A5','A6','A7','PC']}
NAMES = ["Macintosh","Macintosh XL","Macintosh 512K enhanced","Macintosh Plus","Macintosh SE","","Macintosh IIx","Macintosh LC 475"]
def strlist(names):
    b = struct.pack('>H', len(names))
    for n in names: b += bytes([len(n)]) + n.encode()
    return b
def pstr(mem, a): n = mem(a,1)[0]; return bytes(mem(a+1,n)).decode('mac_roman'), a+1+n
class Mac:
    def __init__(s, table, appletalk=True, blind=False, macname="Performa 475", oldfilter=False, mach=8):
        s.table = list(table); s.at = appletalk; s.blind = blind; s.macname = macname; s.mach = mach
        s.selfsend = 0; s.ss_ok = True; s.file = None; s.finfo = None; s.open = False; s.calls = []; s.heap = 0x60000; s.chain_hit = 0
        uc = s.uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN); uc.ctl_set_cpu_model(UC_CPU_M68K_M68000)
        uc.mem_map(0, 0x100000)
        s.CODE, s.STACK, s.RET, s.OLDF = 0x20000, 0x90000, 0x7F000, 0x7E000
        uc.mem_write(s.CODE, code); uc.mem_write(s.RET, b'\x4e\x71'*4); uc.mem_write(s.OLDF, b'\x4e\x75')
        uc.mem_write(0x838, struct.pack('>HH', 480, 640)); uc.mem_write(0x118, struct.pack('>I', 0xAAAA0000)); uc.mem_write(0x2A6, struct.pack('>I', 0x2000))
        uc.mem_write(0x210, struct.pack('>h', -1)); uc.mem_write(0x29A, struct.pack('>I', s.OLDF if oldfilter else 0))
        s.H = {}
        def handle(key, data, mp, da):
            uc.mem_write(da, data + b'\xEE'*32); uc.mem_write(mp, struct.pack('>I', da)); s.H[key] = mp
        handle(('STR#',-16395), strlist(NAMES), 0x30000, 0x40000); s.strsize = len(strlist(NAMES))
        handle(('ICN#',-16482), bytes(range(256)), 0x30010, 0x50000)
        if macname is not None: handle(('STR ',-16413), bytes([len(macname)])+macname.encode(), 0x30020, 0x52000)
    def rd(s,a,n): return s.uc.mem_read(a,n)
    def r(s,n): return s.uc.reg_read(R[n])
    def w(s,n,v): s.uc.reg_write(R[n], v & 0xFFFFFFFF)
    def u16(s,a): return struct.unpack('>H', s.rd(a,2))[0]
    def i16(s,a): return struct.unpack('>h', s.rd(a,2))[0]
    def u32(s,a): return struct.unpack('>I', s.rd(a,4))[0]
    def oserr(s, pb, e): s.uc.mem_write(pb+16, struct.pack('>h', e)); s.w('D0', e)
    def entity(s, a):
        o, a = pstr(s.rd, a); t, a = pstr(s.rd, a); z, a = pstr(s.rd, a); assert z == '*', z; return o, t
    def fcheck(s, pb):
        nm,_ = pstr(s.rd, s.u32(pb+18)); assert nm == 'XL Name Log' and s.i16(pb+22) == -1, (nm, s.i16(pb+22))
    def trap(s, op):
        uc = s.uc; a0, a1, d0, a7 = s.r('A0'), s.r('A1'), s.r('D0'), s.r('A7')
        for n in ('A1','D1'): s.w(n, 0xDEADBEEE)
        if op == 0xA9A0:
            rid, typ = struct.unpack('>h4s', s.rd(a7,6)); h = s.H.get((typ.decode(), rid), 0)
            uc.mem_write(a7+6, struct.pack('>I', h)); s.w('A7', a7+6); s.w('A0', 0xDEADBEEE)
        elif op == 0xA128: s.w('A0', 0x30040); assert a0 == s.CODE
        elif op == 0xA992: assert s.u32(a7) == 0x30040; s.w('A7', a7+4); s.detached = True
        elif op == 0xA1AD:
            sel = struct.pack('>I', d0); v = {b'mach': s.mach, b'micn': -16482, b'sysv': 0x0750}[sel]; s.w('A0', v); s.w('D0', 0)
        elif op == 0xA025: s.w('D0', s.strsize if a0 == 0x30000 else 256)
        elif op == 0xA024: assert a0 == 0x30000; s.strsize = d0; s.w('D0', 0)
        elif op == 0xA02E: uc.mem_write(a1, bytes(s.rd(a0, d0))); s.w('D0', 0)
        elif op == 0xA04A: pass
        elif op == 0xA71E:
            assert 0 < d0 < 4096; p = s.heap; s.heap += (d0 + 15) & ~15; uc.mem_write(p, bytes(d0)); s.w('A0', p); s.w('D0', 0)
        elif op == 0xA004:
            pb = a0; assert s.i16(pb+24) == -10; cs = s.u16(pb+26); s.calls.append(cs)
            if not s.at: s.oserr(pb, -28); return
            if cs == 256:
                if not s.ss_ok: s.oserr(pb, -17); return
                old = s.selfsend; s.selfsend = s.rd(pb+28,1)[0]; uc.mem_write(pb+29, bytes([old])); s.oserr(pb, 0)
            elif cs == 251:
                o, t = s.entity(s.u32(pb+30)); buf = s.u32(pb+34); assert s.u16(pb+38) == 256 and s.u16(pb+40) == 1
                hit = [e for e in s.table if e[0] == o and e[1] == t and s.selfsend]   # a Mac only sees its own names with self-send on
                if hit:
                    e = hit[0]; uc.mem_write(buf, struct.pack('>HBBB', 0xFF00, 0x2A, e[2], 1) + bytes([len(o)]) + o.encode() + bytes([len(t)]) + t.encode() + b'\x01*')
                uc.mem_write(pb+42, struct.pack('>H', len(hit[:1]))); s.oserr(pb, 0)
            elif cs == 253:
                nte = s.u32(pb+30); assert nte >= 0x60000 and nte % 2 == 0; o, t = s.entity(nte+9); sock = s.rd(nte+7,1)[0]
                if any(e[0]==o and e[1]==t for e in s.table): s.oserr(pb, -1027); return
                s.table.append((o, t, sock, True)); s.oserr(pb, 0)
            elif cs == 252:
                o, t = s.entity(s.u32(pb+30)); hit = [e for e in s.table if e[0]==o and e[1]==t]
                if not hit: s.oserr(pb, -1028); return
                s.table.remove(hit[0]); s.oserr(pb, 0)
            else: raise Exception('MPP csCode %d' % cs)
        elif op == 0xA208: s.fcheck(a0); assert s.u32(a0+48) == 2; e = -48 if s.file is not None else 0; s.file = s.file or b''; s.finfo = s.finfo or b'????????'; s.oserr(a0, e)
        elif op == 0xA20C: s.fcheck(a0); assert s.u32(a0+48) == 2; uc.mem_write(a0+32, s.finfo); uc.mem_write(a0+48, struct.pack('>I', 777)); s.oserr(a0, 0)
        elif op == 0xA20D: s.fcheck(a0); assert s.u32(a0+48) == 2; s.finfo = bytes(s.rd(a0+32, 8)); s.oserr(a0, 0)
        elif op == 0xA200: s.fcheck(a0); assert s.u32(a0+48) == 2 and s.rd(a0+27,1)[0] == 3 and not s.open; s.open = True; uc.mem_write(a0+24, struct.pack('>h', 99)); s.oserr(a0, 0)
        elif op == 0xA012: assert s.open and s.i16(a0+24) == 99 and s.u32(a0+28) == 0; s.file = b''; s.oserr(a0, 0)
        elif op == 0xA003:
            assert s.open and s.i16(a0+24) == 99 and s.u16(a0+44) == 2 and s.u32(a0+46) == 0
            n = s.u32(a0+36); s.file += bytes(s.rd(s.u32(a0+32), n)); uc.mem_write(a0+40, struct.pack('>I', n)); s.oserr(a0, 0)
        elif op == 0xA001: assert s.open and s.i16(a0+24) == 99; s.open = False; s.oserr(a0, 0)
        elif op == 0xA013: assert s.i16(a0+22) == -1; s.oserr(a0, 0)
        else: raise Exception('unexpected trap %04X' % op)
    def call(s, addr, regs=None):
        uc = s.uc; init = {}
        for i,n in enumerate(['D0','D1','D2','D3','D4','D5','D6','D7','A0','A1','A2','A3','A4','A5','A6']):
            init[n] = 0x11110000 + i; s.w(n, init[n])
        sp = s.STACK - 4; uc.mem_write(sp, struct.pack('>I', s.RET)); s.w('A7', sp)
        pc = addr; steps = 0
        while pc != s.RET:
            steps += 1; assert steps < 400000, 'runaway'
            if pc == s.OLDF: s.chain_hit += 1
            op = s.u16(pc)
            if op & 0xF000 == 0xA000: s.trap(op); pc += 2; continue
            try: uc.emu_start(pc, 0xFFFFFFFF, count=1)
            except Exception as e: raise Exception('at %x op %04x: %s' % (pc - s.CODE, op, e))
            pc = s.r('PC')
        assert s.r('A7') == s.STACK, 'stack unbalanced'
        return init
    def boot(s):
        init = s.call(s.CODE)
        for n in ['D3','D4','D5','D6','D7','A2','A3','A4','A5','A6']: assert s.r(n) == init[n], n+' not preserved by INIT'
        assert s.u32(0x118) == 0xAAAA0000
    def event(s, ticks):
        s.uc.mem_write(0x16A, struct.pack('>I', ticks)); f = s.u32(0x29A); assert f != 0
        init = s.call(f)
        for n in init: assert s.r(n) == init[n], n+' not preserved by event filter'
    def log(s): return (s.file or b'').decode().split('\r')
    def net(s): return sorted((o,t,k) for o,t,k,*_ in s.table)
ok = True
def check(label, cond, m=None):
    global ok; print(('PASS ' if cond else 'FAIL ')+label); ok &= bool(cond)
    if not cond and m: print('\n'.join('     | '+l for l in m.log())); print('     net:', m.net())
SYS = [("Performa 475","Workstation",4,False), ("Performa 475","Macintosh LC 475",253,False)]
FIXED = [("Performa 475","Macintosh XL",253), ("Performa 475","Workstation",4)]
def run_events(m):
    m.event(5000); m.event(5100); m.event(5000+899); mid = len(m.log()); m.event(5000+900); m.event(9000); return mid

m = Mac(SYS); m.boot(); L1 = m.log()
check('A. Name announced before extensions: found on its real socket and replaced there', m.net() == FIXED and '  see own names (self-send): OK' in L1 and '  Workstation name on network: YES, socket 4' in L1 and '  old model name on network: YES, socket 253' in L1 and '  announce Macintosh XL on socket 253: OK' in L1 and '  withdraw old name: OK' in L1 and '  Macintosh XL on network now: YES, socket 253' in L1, m)
check('   log header', L1[:4] == ['Macintosh XL Name - TEST C log','System 0750  machine type 8','Model name was: Macintosh LC 475','Network name of this Mac: Performa 475'], m)
check('   self-send switched back off; log is TeachText; code resident; filter installed', m.selfsend == 0 and m.finfo == b'TEXTttxt' and m.detached and m.u32(0x29A) != 0)
mid = run_events(m); L2 = m.log()
check('   later pass waits 15 s, runs once, changes nothing more', mid == len(L1) and L2[-2] == 'End of log.' and m.net() == FIXED and L2.count('15 seconds after the desktop appeared:') == 1 and '  withdraw old name (probe): error -1028' in L2 and m.selfsend == 0, m)
print('\n'.join('     | '+l for l in L2))

m = Mac(SYS); m.selfsend = 0xFF; m.boot()
check('A2. Self-send already on before we start: left on afterwards', m.selfsend == 0xFF and m.net() == FIXED, m)

m = Mac([("Performa 475","Workstation",4,False), ("Performa 475","Macintosh LC 475",250,False)]); m.boot()
check('A3. Model name on some other socket (250): replaced on that socket', ("Performa 475","Macintosh XL",250) in m.net(), m)

m = Mac([SYS[0]]); m.boot(); a = m.net(); m.table.append(SYS[1]); run_events(m)
check('B. Name announced after extensions load: fixed by the later pass', a == [("Performa 475","Workstation",4)] and m.net() == FIXED, m)

m = Mac([SYS[0]]); m.boot(); m.table.append(("Performa 475","Macintosh XL",253,False)); run_events(m); L = m.log()
check('C. System itself announces Macintosh XL later: left alone, reported', m.net() == FIXED and L[-3] == '  Macintosh XL on network now: YES, socket 253', m)

m = Mac(SYS, appletalk=False); m.boot(); run_events(m)
check('D. AppleTalk off: nothing touched, error -28 logged', '  AppleTalk is not active: error -28' in m.log() and len(m.net()) == 2 and m.calls.count(253) == 0, m)

m = Mac(SYS); m.ss_ok = False; m.boot(); L = m.log()
check('E. Self-send not available: probe path, announces on 253', m.net() == FIXED and '  see own names (self-send): error -17' in L and '  announce Macintosh XL on socket 253 (assumed): OK' in L, m)

m = Mac(SYS, macname=None); m.boot(); run_events(m)
check('F. No network name set: skipped cleanly', m.calls == [] and '  skipped (no network name or model name)' in m.log(), m)

m = Mac(SYS, mach=99); m.boot()
check('G. Machine not in the name list: no network change', m.calls == [] and 'Model name was: (not found in the name list)' in m.log(), m)

m = Mac(SYS, oldfilter=True); m.boot(); run_events(m)
check('H. An earlier event filter is still called every time', m.chain_hit == 5 and m.net() == FIXED, m)

m = Mac(SYS); m.file = b'old junk'; m.finfo = b'TEXTttxt'; m.boot()
check('I. Existing log file is replaced, not appended to', m.log()[0] == 'Macintosh XL Name - TEST C log', m)
print('ALL PASS' if ok else 'FAILURES'); sys.exit(0 if ok else 1)
