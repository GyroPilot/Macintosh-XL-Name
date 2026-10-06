/* Macintosh XL Name - TEST C - network re-announce and log.
   TEST C: finds the model name's real socket (self-send lookup), falls back to 253.
   TEST B: first network build; assumed socket 4 (wrong: models use 253).  GyroPilot, Oct 2026.
   Freestanding C for a 68000 code resource: no globals, no library calls. */
typedef unsigned char  u8;
typedef unsigned short u16;
typedef unsigned long  u32;

long pb_control(void *), pb_hcreate(void *), pb_hopen(void *), pb_write(void *), pb_close(void *);
long pb_seteof(void *), pb_hgetfinfo(void *), pb_hsetfinfo(void *), pb_flushvol(void *);
void *newptr_sys_clear(long);
long gestalt(long, long *);
void **get_resource(long, long);
void *get_g(void);
void set_g(void *);
u8 *get_oldname(void);
void install_filter(void);

#define TICKS      (*(volatile u32 *)0x16A)
#define BOOTDRIVE  (*(volatile short *)0x210)
#define W(p,o)  (*(short *)((u8 *)(p) + (o)))
#define L(p,o)  (*(long  *)((u8 *)(p) + (o)))
#define B(p,o)  (*((u8 *)(p) + (o)))
#define DELAY_TICKS (15 * 60)

typedef struct {
    u8  pb[128];
    u8  ent[104];
    u8  ret[256];
    u8  line[160];
    u8  obj[34];        /* this Mac's network name (Pascal string)   */
    u8  old[64];        /* the model name before the change          */
    u8  fname[32];
    u32 first;
    short len, done, busy, vref;
} G;

static void clear(u8 *p, short n) { while (n-- > 0) *p++ = 0; }

/* ---- building a log line ---- */
static void put(G *g, const char *s) { while (*s && g->len < 158) g->line[g->len++] = (u8)*s++; }
static void putp(G *g, const u8 *p) { short n = p[0]; while (n-- > 0 && g->len < 158) g->line[g->len++] = *++p; }
static void putn(G *g, long v)
{
    static const long pw[] = {1000000000L,100000000L,10000000L,1000000L,100000L,10000L,1000L,100L,10L,1L};
    short i, started = 0;
    if (v < 0) { if (g->len < 158) g->line[g->len++] = '-'; v = -v; }
    for (i = 0; i < 10; i++) {
        short d = 0;
        while (v >= pw[i]) { v -= pw[i]; d++; }
        if (d || started || i == 9) { if (g->len < 158) g->line[g->len++] = (u8)('0' + d); started = 1; }
    }
}
static void puth(G *g, u32 v, short digits)
{
    while (digits-- > 0) {
        short d = (short)((v >> (digits * 4)) & 15);
        if (g->len < 158) g->line[g->len++] = (u8)(d < 10 ? '0' + d : 'A' + d - 10);
    }
}

/* ---- the log file: "XL Name Log" at the top level of the startup disk ---- */
static void fpb(G *g) { clear(g->pb, 128); L(g->pb,18) = (long)g->fname; W(g->pb,22) = g->vref; L(g->pb,48) = 2; }
static void log_start(G *g)
{
    static const char nm[] = "XL Name Log";
    short i;
    for (i = 0; nm[i]; i++) g->fname[i + 1] = (u8)nm[i];
    g->fname[0] = (u8)i;
    g->vref = BOOTDRIVE;
    fpb(g); pb_hcreate(g->pb);
    fpb(g);
    if (pb_hgetfinfo(g->pb) == 0) {
        L(g->pb,32) = 0x54455854L;          /* 'TEXT' */
        L(g->pb,36) = 0x74747874L;          /* 'ttxt' */
        L(g->pb,48) = 2;
        pb_hsetfinfo(g->pb);
    }
    fpb(g); B(g->pb,27) = 3;
    if (pb_hopen(g->pb) == 0) { L(g->pb,28) = 0; pb_seteof(g->pb); pb_close(g->pb); }
}
static void endl(G *g)
{
    if (g->len < 159) g->line[g->len++] = 13;
    fpb(g); B(g->pb,27) = 3;
    if (pb_hopen(g->pb) == 0) {
        L(g->pb,32) = (long)g->line; L(g->pb,36) = g->len;
        W(g->pb,44) = 2; L(g->pb,46) = 0;   /* at end of file */
        pb_write(g->pb);
        pb_close(g->pb);
        clear(g->pb, 128); W(g->pb,22) = g->vref; pb_flushvol(g->pb);
    }
    g->len = 0;
}

/* ---- NBP ---- */
static short pack(u8 *d, const u8 *obj, const u8 *typ)
{
    short n = 0, i;
    for (i = 0; i <= obj[0]; i++) d[n++] = obj[i];
    for (i = 0; i <= typ[0]; i++) d[n++] = typ[i];
    d[n++] = 1; d[n++] = '*';
    return n;
}
static void mpp(G *g, short cs) { clear(g->pb, 128); W(g->pb,24) = -10; W(g->pb,26) = cs; }

static long nbp_lookup(G *g, const u8 *typ, short *count, short *sock)
{
    long e;
    pack(g->ent, g->obj, typ);
    mpp(g, 251);
    B(g->pb,28) = 3; B(g->pb,29) = 2;
    L(g->pb,30) = (long)g->ent; L(g->pb,34) = (long)g->ret; W(g->pb,38) = 256; W(g->pb,40) = 1;
    clear(g->ret, 8);
    e = pb_control(g->pb);
    *count = e ? 0 : W(g->pb,42);
    *sock = g->ret[3];
    return e;
}
static long nbp_register(G *g, const u8 *typ, short sock)
{
    u8 *nte = (u8 *)newptr_sys_clear(128);   /* must stay allocated while registered */
    if (!nte) return -108;
    nte[7] = (u8)sock;
    pack(nte + 9, g->obj, typ);
    mpp(g, 253);
    B(g->pb,28) = 2; B(g->pb,29) = 2;
    L(g->pb,30) = (long)nte; B(g->pb,34) = 0;
    return pb_control(g->pb);
}
static long nbp_remove(G *g, const u8 *typ)
{
    pack(g->ent, g->obj, typ);
    mpp(g, 252);
    L(g->pb,30) = (long)g->ent;
    return pb_control(g->pb);
}
static void result(G *g, const char *what, long e)
{
    put(g, what);
    if (e == 0) put(g, "OK"); else { put(g, "error "); putn(g, e); }
    endl(g);
}

/* Self-send: while on, an NBP lookup also reports this Mac's own names. */
static long self_send(G *g, short on, short *old)
{
    long e;
    mpp(g, 256);
    B(g->pb,28) = (u8)on;
    e = pb_control(g->pb);
    if (old) *old = B(g->pb,29);
    return e;
}
static void found(G *g, const char *what, long e, short count, short sock)
{
    put(g, what);
    if (e) { put(g, "lookup error "); putn(g, e); }
    else if (count > 0) { put(g, "YES, socket "); putn(g, sock); }
    else put(g, "not found");
    endl(g);
}

static void nbp_pass(G *g, const char *when)
{
    static const u8 xl[] = "\014Macintosh XL";
    static const u8 ws[] = "\013Workstation";
    short count = 0, sock = 0, oldflag = 0;
    long e, se;
    put(g, when); endl(g);
    if (g->obj[0] == 0 || g->old[0] == 0) { put(g, "  skipped (no network name or model name)"); endl(g); return; }

    se = self_send(g, 0xFF, &oldflag);
    if (se == -28 || se == -21) { result(g, "  AppleTalk is not active: ", se); return; }
    result(g, "  see own names (self-send): ", se);

    e = nbp_lookup(g, ws, &count, &sock);
    found(g, "  Workstation name on network: ", e, count, sock);
    e = nbp_lookup(g, g->old, &count, &sock);
    found(g, "  old model name on network: ", e, count, sock);

    if (e == 0 && count > 0) {
        e = nbp_register(g, xl, sock);
        put(g, "  announce Macintosh XL on socket "); putn(g, sock); result(g, ": ", e);
        if (e == 0) result(g, "  withdraw old name: ", nbp_remove(g, g->old));
    } else if (e == 0) {
        /* not seen: probe by withdrawing; real Macs keep the model name on 253 */
        e = nbp_remove(g, g->old);
        result(g, "  withdraw old name (probe): ", e);
        if (e == 0) result(g, "  announce Macintosh XL on socket 253 (assumed): ", nbp_register(g, xl, 253));
    }
    e = nbp_lookup(g, xl, &count, &sock);
    found(g, "  Macintosh XL on network now: ", e, count, sock);
    if (se == 0) self_send(g, oldflag, 0);
}

/* ---- called from the extension at startup ---- */
void xl_init(void)
{
    G *g = (G *)newptr_sys_clear(sizeof(G));
    long v;
    void **h;
    u8 *o;
    short i;
    if (!g) return;
    o = get_oldname();
    for (i = 0; i <= o[0] && i < 63; i++) g->old[i] = o[i];
    log_start(g);
    put(g, "Macintosh XL Name - TEST C log"); endl(g);
    put(g, "System "); if (gestalt(0x73797376L, &v) == 0) puth(g, (u32)v, 4); else put(g, "?");
    put(g, "  machine type "); if (gestalt(0x6D616368L, &v) == 0) putn(g, v); else put(g, "?");
    endl(g);
    put(g, "Model name was: "); if (g->old[0]) putp(g, g->old); else put(g, "(not found in the name list)"); endl(g);
    h = get_resource(0x53545220L, -16413);                  /* 'STR ' Macintosh Name */
    if (h && *h) { u8 *p = (u8 *)*h; if (p[0] <= 32) for (i = 0; i <= p[0]; i++) g->obj[i] = p[i]; }
    put(g, "Network name of this Mac: "); if (g->obj[0]) putp(g, g->obj); else put(g, "(none)"); endl(g);
    nbp_pass(g, "At startup, when the extension loaded:");
    set_g(g);
    install_filter();
}

/* ---- called on every event once applications are running ---- */
void xl_tick(void)
{
    G *g = (G *)get_g();
    if (!g || g->done || g->busy) return;
    if (g->first == 0) { g->first = TICKS; if (g->first == 0) g->first = 1; return; }
    if (TICKS - g->first < DELAY_TICKS) return;
    g->busy = 1;
    nbp_pass(g, "15 seconds after the desktop appeared:");
    put(g, "End of log."); endl(g);
    g->done = 1; g->busy = 0;
}
