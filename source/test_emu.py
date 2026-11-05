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
def run(names, pin=(364,720), have_res=True, mach=4, micn=-16482, have_icon=True, icon_size=256, gestalt_ok=True, sysver=0x0701, app_first=False, stuck=False, calls=2):
    uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
    uc.ctl_set_cpu_model(UC_CPU_M68K_M68000)
    uc.mem_map(0, 0x100000)
    CODE, STACK, MP, DATA, RET = 0x20000, 0x80000, 0x30000, 0x40000, 0x7F000
    uc.mem_write(CODE, code)
    uc.mem_write(RET, b'\x4e\x71'*4)
    uc.mem_write(0x838, struct.pack('>HH', *pin))
    uc.mem_write(0x15A, struct.pack('>H', sysver))       # SysVersion
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
    SYSZ, APPZ = 0x00002000, 0xAAAA0000
    hz = {MP: APPZ if app_first else SYSZ, IMP: APPZ if app_first else SYSZ}
    FMP, FDATA, FIMP, FIDATA = 0x30020, 0x44000, 0x30030, 0x54000     # fresh copies, as after an app launch
    uc.mem_write(FDATA, data + b'\xEE'*64); uc.mem_write(FMP, struct.pack('>I', FDATA))
    uc.mem_write(FIDATA, OLDICON + b'\xEE'*32); uc.mem_write(FIMP, struct.pack('>I', FIDATA))
    hz[FMP] = hz[FIMP] = APPZ
    sizes = {MP: len(data), IMP: icon_size, FMP: len(data), FIMP: icon_size}
    st['fresh'] = {(0x53545223, -16395): FMP if have_res else 0, (0x49434E23, micn): FIMP if have_icon else 0}
    nop = set()
    st['released'] = []
    regs0 = {}
    for i,r in enumerate([UC_M68K_REG_D3,UC_M68K_REG_D4,UC_M68K_REG_D5,UC_M68K_REG_D6,UC_M68K_REG_D7,UC_M68K_REG_A2,UC_M68K_REG_A3,UC_M68K_REG_A4]):
        uc.reg_write(r, 0x11110000+i); regs0[r]=0x11110000+i
    sp = STACK - 4
    uc.mem_write(sp, struct.pack('>I', RET))
    uc.reg_write(UC_M68K_REG_A7, sp)
    OLDGR, RES = 0x7E000, 0x60000
    st['gr_calls'] = 0
    def execute(pc, stop):
      steps = 0
      while pc != stop:
          steps += 1
          assert steps < 20000, 'runaway'
          if pc == OLDGR:                     # the real GetResource, called by the patch
              a7 = uc.reg_read(UC_M68K_REG_A7)
              ret, rid, typ = struct.unpack('>IhI', uc.mem_read(a7, 10))
              st['gr_calls'] += 1
              h = st['fresh'].get((typ, rid), 0)
              uc.mem_write(a7+10, struct.pack('>I', h))
              uc.reg_write(UC_M68K_REG_A7, a7+10)
              for r in (UC_M68K_REG_A0,UC_M68K_REG_A1,UC_M68K_REG_D0,UC_M68K_REG_D1,UC_M68K_REG_D2): uc.reg_write(r, 0xDEADBEEE)
              pc = ret; uc.reg_write(UC_M68K_REG_PC, pc); continue
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
              elif op == 0xA51E:                      # NewPtr,SYS
                  st['resident'] = (RES, d0in); uc.reg_write(UC_M68K_REG_A0, RES); uc.reg_write(UC_M68K_REG_D0, 0)
              elif op == 0xA146:                      # GetTrapAddress
                  assert d0in & 0xFFFF == 0x01A0, hex(d0in); uc.reg_write(UC_M68K_REG_A0, OLDGR)
              elif op == 0xA047:                      # SetTrapAddress
                  assert d0in & 0xFFFF == 0x01A0, hex(d0in); st['patched'] = a0in
              elif op == 0xA126:                      # HandleZone
                  assert a0in in hz, hex(a0in)
                  uc.reg_write(UC_M68K_REG_A0, hz[a0in]); uc.reg_write(UC_M68K_REG_D0, 0)
              elif op == 0xA9A3:                      # ReleaseResource(h)
                  h = struct.unpack('>I', uc.mem_read(a7,4))[0]
                  assert h in hz, hex(h)
                  st['released'].append(h)
                  if not stuck: hz[h] = SYSZ          # reloaded with TheZone = SysZone
                  uc.reg_write(UC_M68K_REG_A7, a7+4)
              elif op == 0xA1AD:
                  assert sysver >= 0x0604, 'Gestalt called on System %x (bomb ID 12)' % sysver
                  sel = struct.pack('>I', d0in)
                  if not gestalt_ok: uc.reg_write(UC_M68K_REG_D0, (-5551) & 0xFFFFFFFF)
                  else:
                      assert sel in (b'mach', b'micn'), sel
                      uc.reg_write(UC_M68K_REG_A0, (mach if sel==b'mach' else micn) & 0xFFFFFFFF); uc.reg_write(UC_M68K_REG_D0, 0)
              elif op == 0xA025:
                  assert a0in in sizes, hex(a0in)
                  uc.reg_write(UC_M68K_REG_D0, sizes[a0in])
              elif op == 0xA024:
                  assert a0in in (MP, FMP), hex(a0in)
                  sizes[a0in] = d0in; uc.reg_write(UC_M68K_REG_D0, 0)
              elif op == 0xA02E:
                  s,d,n = a0in,a1in,d0in
                  assert 0 <= n < 4096
                  buf = bytes(uc.mem_read(s,n)); uc.mem_write(d,buf)
                  uc.reg_write(UC_M68K_REG_D0, 0)
              elif op == 0xA04A:
                  assert a0in in sizes; nop.add(a0in)
                  st['nopurge'] = MP in nop; st['icon_nopurge'] = IMP in nop
              else: raise Exception('unexpected trap '+hex(op))
              pc += 2; uc.reg_write(UC_M68K_REG_PC, pc); continue
          try: uc.emu_start(pc, 0xFFFFFFFF, count=1)
          except Exception as e: raise Exception("at pc %x op %04x: %s" % (pc-CODE, op, e))
          pc = uc.reg_read(UC_M68K_REG_PC)
      return pc
    execute(CODE, RET)
    assert uc.reg_read(UC_M68K_REG_A7) == STACK, 'stack unbalanced'
    for r,v in regs0.items(): assert uc.reg_read(r) == v, 'register not preserved'
    assert struct.unpack('>I', uc.mem_read(0x118,4))[0] == 0xAAAA0000, 'zone not restored'
    st['size'] = sizes[MP]
    out = bytes(uc.mem_read(DATA, st['size']))
    guard = bytes(uc.mem_read(DATA+max(st['size'],len(data)), 16))
    # --- the resident patch: a program calls GetResource after startup and gets a FRESH copy ---
    st['patch_results'] = []
    if 'patched' in st:
        res_base, res_len = st['resident']
        assert st['patched'] - res_base < res_len, 'patch outside the resident copy'
        for k in range(calls):
            for (typ, rid) in ((0x53545223, -16395), (0x49434E23, micn), (0x50494354, 128)):
                RET2 = 0x7F100; uc.mem_write(RET2, b'\x4e\x71'*4)
                sp2 = STACK - 0x200
                frame = struct.pack('>IhII', RET2, rid, typ, 0xCAFEF00D)
                uc.mem_write(sp2, frame); uc.reg_write(UC_M68K_REG_A7, sp2)
                for r,v in regs0.items(): uc.reg_write(r, v)
                execute(st['patched'], RET2)
                assert uc.reg_read(UC_M68K_REG_A7) == sp2 + 10, 'patch: stack unbalanced'
                for r,v in regs0.items(): assert uc.reg_read(r) == v, 'patch: register not preserved'
                h = struct.unpack('>I', uc.mem_read(sp2+10, 4))[0]
                st['patch_results'].append((typ, h))
        st['fresh_names'] = parse(bytes(uc.mem_read(FDATA, sizes[FMP])))[0]
        st['fresh_guard'] = bytes(uc.mem_read(FDATA+max(sizes[FMP], len(data)), 16)) == b'\xEE'*16
        st['fresh_icon'] = bytes(uc.mem_read(FIDATA, 256))
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
(names, used), st, guard, n0 = run(L, gestalt_ok=False)
check('Fallback search: shorter "Mac Plus" entry (list grows)', names == ["A","Macintosh XL","B","CC"] and st['size']==n0+4 and used==st['size'])
# 6 no Plus entry
L = ["Macintosh","Macintosh SE","Pl","us"]
(names, used), st, guard, n0 = run(L, gestalt_ok=False)
check('Fallback search, no Plus entry: untouched', names == L and st['size']==n0)
# REV D: the entry for this Mac's own model
L75 = ["Macintosh"]*11 + ["Power Macintosh"] + ["Macintosh"]*8      # System 7.5.5's list
(names, used), st, guard, n0 = run(L75)
check('REV D, 7.5.5-style list, mach 4: entry 4 renamed, rest intact', names == L75[:3]+["Macintosh XL"]+L75[4:] and used == st['size'] and guard == b'\xEE'*16)
(names, used), st, guard, n0 = run(L75, mach=1)
check('REV D, mach 1: first entry renamed', names == ["Macintosh XL"]+L75[1:])
(names, used), st, guard, n0 = run(L75, mach=20)
check('REV D, mach 20 (last entry): renamed', names == L75[:19]+["Macintosh XL"])
(names, used), st, guard, n0 = run(NAMES, mach=40)
check('REV D, mach past the list: falls back to the Plus entry', names == exp)
(names, used), st, guard, n0 = run(L75, mach=40)
check('REV D, mach past the list, no Plus entry: untouched', names == L75)
(names, used), st, guard, n0 = run(NAMES, mach=0)
check('REV D, mach 0: falls back to the Plus entry', names == exp)
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
check('REV D icon: machine type not Plus, picture still replaced; entry 6 renamed', st['icon'] == LISA and names == NAMES[:5]+["Macintosh XL"]+NAMES[6:])
(names, used), st, guard, n0 = run(NAMES, gestalt_ok=False)
check('Icon: Gestalt unavailable, picture untouched, name still changed', st['icon'] == st['old_icon'] and names == exp)
(names, used), st, guard, n0 = run(NAMES, have_icon=False)
check('Icon: no picture on file, clean exit', st['icon'] == st['old_icon'] and names == exp)
(names, used), st, guard, n0 = run(NAMES, icon_size=128)
check('Icon: picture too small, untouched', st['icon'] == st['old_icon'])
(names, used), st, guard, n0 = run(NAMES, have_res=False)
check('Icon: name list missing, picture still replaced', st['icon'] == LISA)
for v in (0x0602, 0x0603):
    (names, used), st, guard, n0 = run(NAMES, sysver=v)
    check('System %d.%d.%d: no Gestalt call, picture untouched, name still changed' % (v>>8, (v>>4)&15, v&15),
          '0xa1ad' not in st['traps'] and st['icon'] == st['old_icon'] and names == exp)
(names, used), st, guard, n0 = run(NAMES, sysver=0x0604)
check('System 6.0.4: Gestalt used, picture replaced', '0xa1ad' in st['traps'] and st['icon'] == LISA)
# REV E: the copy GetResource returns may be in the application heap (System 6); it must be released and
# loaded again into the system heap before it is edited.
(names, used), st, guard, n0 = run(NAMES, sysver=0x0608, app_first=True)
check('REV E, 6.0.8, list and picture first loaded in the app heap: both released, reloaded, then changed',
      names == exp and st['icon'] == LISA and st['released'] == [0x30000, 0x30010] and st['nopurge'] and st.get('icon_nopurge'))
(names, used), st, guard, n0 = run(NAMES, sysver=0x0608)
check('REV E, already in the system heap: nothing released, changed', names == exp and st['icon'] == LISA and st['released'] == [])
(names, used), st, guard, n0 = run(NAMES, sysver=0x0608, app_first=True, stuck=True)
check('REV E, reload still not in the system heap: left alone (name and picture untouched)', names == NAMES and st['icon'] == st['old_icon'])
# REV E resident patch: after startup a program gets a FRESH copy (System 6 reloads it at each launch)
(names, used), st, guard, n0 = run(NAMES, sysver=0x0608)
check('REV E patch, 6.0.8: fresh name list renamed (entry 4), twice in a row, nothing past the end',
      st.get('fresh_names') == exp and st['fresh_guard'] and st['gr_calls'] == 6)
check('REV E patch: fresh machine picture replaced; other resources passed through untouched',
      st['fresh_icon'] == LISA and [h for t,h in st['patch_results'] if t == 0x50494354] == [0, 0])
check('REV E patch: the caller gets the real handle back', [h for t,h in st['patch_results'] if t == 0x53545223] == [0x30020, 0x30020])
(names, used), st, guard, n0 = run(NAMES, sysver=0x0602)
check('REV E patch, 6.0.2 (no Gestalt): fresh list renamed by the Plus search, picture untouched',
      st.get('fresh_names') == exp and st['fresh_icon'] == st['old_icon'] and '0xa1ad' not in st['traps'])
(names, used), st, guard, n0 = run(L75, mach=4)
check('REV E patch, 7.5.5-style list: entry 4 renamed in the fresh copy', st.get('fresh_names') == L75[:3]+["Macintosh XL"]+L75[4:])
(names, used), st, guard, n0 = run(NAMES, pin=(342,512))
check('REV E: real Plus screen: no patch installed', 'patched' not in st and 'resident' not in st)
(names, used), st, guard, n0 = run(NAMES, have_res=False, have_icon=False)
check('REV E patch: resources missing: patch passes the nil handle back', [h for t,h in st['patch_results']] == [0]*6)
(names, used), st, guard, n0 = run(NAMES, gestalt_ok=False)
check('REV E patch: Gestalt fails: fresh name still renamed (Plus search), picture untouched',
      st.get('fresh_names') == exp and st['fresh_icon'] == st['old_icon'])
print('ALL PASS' if ok else 'FAILURES'); sys.exit(0 if ok else 1)
