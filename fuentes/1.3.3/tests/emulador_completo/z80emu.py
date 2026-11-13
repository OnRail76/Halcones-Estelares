#!/usr/bin/env python3
"""Emulador Z80 completo (instrucciones documentadas + IXH/IXL/IYH/IYL, SLL,
DDCB/FDCB con copia en registro) y desensamblador, decodificados con el
esquema x/y/z/p/q. Pensado para analizar binarios de ZX Spectrum 48K sin ROM:
memoria 64K, ROM opcional de solo lectura, IM0/1/2, HALT, teclado por puerto
0xFE y contador de T-states aproximado (sin contencion)."""

R8 = ['b', 'c', 'd', 'e', 'h', 'l', '(hl)', 'a']
RP = ['bc', 'de', 'hl', 'sp']
RP2 = ['bc', 'de', 'hl', 'af']
CC = ['nz', 'z', 'nc', 'c', 'po', 'pe', 'p', 'm']
ALU = ['add a,', 'adc a,', 'sub ', 'sbc a,', 'and ', 'xor ', 'or ', 'cp ']
ROT = ['rlc', 'rrc', 'rl', 'rr', 'sla', 'sra', 'sll', 'srl']

SF, ZF, YF, HF, XF, PF, NF, CF = 0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01
SZ = [0] * 256
SZP = [0] * 256
for _i in range(256):
    SZ[_i] = (_i & (SF | YF | XF)) | (ZF if _i == 0 else 0)
    SZP[_i] = SZ[_i] | (PF if bin(_i).count('1') % 2 == 0 else 0)


class Z80:
    def __init__(self, rom=None):
        self.m = bytearray(65536)
        self.rom_top = 0
        if rom:
            self.m[:len(rom)] = rom
            self.rom_top = len(rom)
        self.a = self.f = self.b = self.c = self.d = self.e = self.h = self.l = 0
        self.a_ = self.f_ = self.b_ = self.c_ = self.d_ = self.e_ = self.h_ = self.l_ = 0
        self.ix = self.iy = 0xffff
        self.sp = 0xffff
        self.pc = 0
        self.i = self.r = 0
        self.iff1 = self.iff2 = 0
        self.im = 0
        self.halted = False
        self.t = 0
        self.ei_delay = False
        self.port_in = lambda port: 0xff
        self.port_out = lambda port, v: None
        self.write_hook = None

    # ---------------------------------------------------------- memoria
    def rb(self, a):
        return self.m[a & 0xffff]

    def wb(self, a, v):
        a &= 0xffff
        if a < self.rom_top:
            return
        if self.write_hook:
            self.write_hook(a, v & 0xff)
        self.m[a] = v & 0xff

    def rw(self, a):
        return self.m[a & 0xffff] | (self.m[(a + 1) & 0xffff] << 8)

    def ww(self, a, v):
        self.wb(a, v & 0xff)
        self.wb(a + 1, (v >> 8) & 0xff)

    def fetch(self):
        v = self.m[self.pc]
        self.pc = (self.pc + 1) & 0xffff
        return v

    def fetchw(self):
        v = self.rw(self.pc)
        self.pc = (self.pc + 2) & 0xffff
        return v

    def push(self, v):
        self.sp = (self.sp - 2) & 0xffff
        self.ww(self.sp, v)

    def pop(self):
        v = self.rw(self.sp)
        self.sp = (self.sp + 2) & 0xffff
        return v

    # --------------------------------------------------------- registros
    def get_rp(self, p, idx=None):
        if p == 0: return (self.b << 8) | self.c
        if p == 1: return (self.d << 8) | self.e
        if p == 2: return self._get_hl(idx)
        return self.sp

    def set_rp(self, p, v, idx=None):
        v &= 0xffff
        if p == 0: self.b, self.c = v >> 8, v & 0xff
        elif p == 1: self.d, self.e = v >> 8, v & 0xff
        elif p == 2: self._set_hl(v, idx)
        else: self.sp = v

    def get_rp2(self, p, idx=None):
        if p == 3: return (self.a << 8) | self.f
        return self.get_rp(p, idx)

    def set_rp2(self, p, v, idx=None):
        if p == 3:
            self.a, self.f = (v >> 8) & 0xff, v & 0xff
        else:
            self.set_rp(p, v, idx)

    def _get_hl(self, idx):
        if idx == 'ix': return self.ix
        if idx == 'iy': return self.iy
        return (self.h << 8) | self.l

    def _set_hl(self, v, idx):
        if idx == 'ix': self.ix = v & 0xffff
        elif idx == 'iy': self.iy = v & 0xffff
        else: self.h, self.l = (v >> 8) & 0xff, v & 0xff

    def get_r(self, n, idx=None, addr=None):
        if n == 0: return self.b
        if n == 1: return self.c
        if n == 2: return self.d
        if n == 3: return self.e
        if n == 4:
            if idx == 'ix': return self.ix >> 8
            if idx == 'iy': return self.iy >> 8
            return self.h
        if n == 5:
            if idx == 'ix': return self.ix & 0xff
            if idx == 'iy': return self.iy & 0xff
            return self.l
        if n == 6: return self.rb(addr)
        return self.a

    def set_r(self, n, v, idx=None, addr=None):
        v &= 0xff
        if n == 0: self.b = v
        elif n == 1: self.c = v
        elif n == 2: self.d = v
        elif n == 3: self.e = v
        elif n == 4:
            if idx == 'ix': self.ix = (self.ix & 0xff) | (v << 8)
            elif idx == 'iy': self.iy = (self.iy & 0xff) | (v << 8)
            else: self.h = v
        elif n == 5:
            if idx == 'ix': self.ix = (self.ix & 0xff00) | v
            elif idx == 'iy': self.iy = (self.iy & 0xff00) | v
            else: self.l = v
        elif n == 6: self.wb(addr, v)
        else: self.a = v

    # ------------------------------------------------------------- ALU
    def alu(self, op, v):
        a = self.a
        if op == 0 or op == 1:  # ADD / ADC
            c = (self.f & CF) if op == 1 else 0
            r = a + v + c
            self.f = SZ[r & 0xff] | (CF if r > 0xff else 0) | ((a ^ v ^ r) & HF) | \
                (PF if ((a ^ ~v) & (a ^ r) & 0x80) else 0)
            self.a = r & 0xff
        elif op in (2, 3, 7):  # SUB / SBC / CP
            c = (self.f & CF) if op == 3 else 0
            r = a - v - c
            f = (SZ[r & 0xff] & ~(YF | XF)) | NF | (CF if r < 0 else 0) | ((a ^ v ^ r) & HF) | \
                (PF if ((a ^ v) & (a ^ r) & 0x80) else 0)
            if op == 7:
                self.f = f | (v & (YF | XF))
            else:
                self.f = f | (r & (YF | XF))
                self.a = r & 0xff
        elif op == 4:
            self.a = a & v
            self.f = SZP[self.a] | HF
        elif op == 5:
            self.a = a ^ v
            self.f = SZP[self.a]
        elif op == 6:
            self.a = a | v
            self.f = SZP[self.a]

    def inc8(self, v):
        r = (v + 1) & 0xff
        self.f = (self.f & CF) | SZ[r] | (HF if (v & 0xf) == 0xf else 0) | (PF if v == 0x7f else 0)
        return r

    def dec8(self, v):
        r = (v - 1) & 0xff
        self.f = (self.f & CF) | SZ[r] | NF | (HF if (v & 0xf) == 0 else 0) | (PF if v == 0x80 else 0)
        return r

    def add16(self, a, b):
        r = a + b
        self.f = (self.f & (SF | ZF | PF)) | ((r >> 8) & (YF | XF)) | \
            (HF if ((a ^ b ^ r) & 0x1000) else 0) | (CF if r > 0xffff else 0)
        return r & 0xffff

    def adc16(self, a, b):
        c = self.f & CF
        r = a + b + c
        rr = r & 0xffff
        self.f = ((rr >> 8) & (SF | YF | XF)) | (ZF if rr == 0 else 0) | \
            (HF if ((a ^ b ^ r) & 0x1000) else 0) | (CF if r > 0xffff else 0) | \
            (PF if ((a ^ ~b) & (a ^ r) & 0x8000) else 0)
        return rr

    def sbc16(self, a, b):
        c = self.f & CF
        r = a - b - c
        rr = r & 0xffff
        self.f = ((rr >> 8) & (SF | YF | XF)) | (ZF if rr == 0 else 0) | NF | \
            (HF if ((a ^ b ^ r) & 0x1000) else 0) | (CF if r < 0 else 0) | \
            (PF if ((a ^ b) & (a ^ r) & 0x8000) else 0)
        return rr

    def rot(self, y, v):
        c = self.f & CF
        if y == 0: co = v >> 7; v = ((v << 1) | co) & 0xff
        elif y == 1: co = v & 1; v = (v >> 1) | (co << 7)
        elif y == 2: co = v >> 7; v = ((v << 1) | c) & 0xff
        elif y == 3: co = v & 1; v = (v >> 1) | (c << 7)
        elif y == 4: co = v >> 7; v = (v << 1) & 0xff
        elif y == 5: co = v & 1; v = (v >> 1) | (v & 0x80)
        elif y == 6: co = v >> 7; v = ((v << 1) | 1) & 0xff
        else: co = v & 1; v = v >> 1
        self.f = SZP[v] | co
        return v

    def daa(self):
        a = self.a
        cf = self.f & CF
        hf = self.f & HF
        nf = self.f & NF
        diff = 0
        if hf or (a & 0x0f) > 9: diff |= 0x06
        if cf or a > 0x99: diff |= 0x60
        newc = CF if (cf or a > 0x99) else 0
        if nf:
            newh = HF if (hf and (a & 0x0f) < 6) else 0
            a = (a - diff) & 0xff
        else:
            newh = HF if ((a & 0x0f) > 9) else 0
            a = (a + diff) & 0xff
        self.a = a
        self.f = SZP[a] | newc | newh | nf

    def cond(self, y):
        f = self.f
        return [not f & ZF, f & ZF, not f & CF, f & CF, not f & PF, f & PF, not f & SF, f & SF][y]

    # -------------------------------------------------------- interrupcion
    def interrupt(self, bus=0xff):
        if not self.iff1:
            return False
        if self.halted:
            self.halted = False
            self.pc = (self.pc + 1) & 0xffff
        self.iff1 = self.iff2 = 0
        self.push(self.pc)
        if self.im == 2:
            self.pc = self.rw((self.i << 8) | bus)
            self.t += 19
        else:
            self.pc = 0x38
            self.t += 13
        return True

    # ------------------------------------------------------------ ejecutar
    def step(self):
        if self.halted:
            self.t += 4
            return
        self.ei_delay = False
        op = self.fetch()
        self.r = (self.r & 0x80) | ((self.r + 1) & 0x7f)
        idx = None
        if op == 0xdd or op == 0xfd:
            idx = 'ix' if op == 0xdd else 'iy'
            op = self.fetch()
            self.r = (self.r & 0x80) | ((self.r + 1) & 0x7f)
            self.t += 4
            if op in (0xdd, 0xfd, 0xed):
                self.pc = (self.pc - 1) & 0xffff
                return
            if op == 0xcb:
                d = self.fetch()
                d = d - 256 if d > 127 else d
                op2 = self.fetch()
                self._ddcb(idx, (self._get_hl(idx) + d) & 0xffff, op2)
                return
        if op == 0xcb:
            self._cb(self.fetch())
            return
        if op == 0xed:
            self._ed(self.fetch())
            return
        self._main(op, idx)

    def _addr_hl(self, idx):
        if idx:
            d = self.fetch()
            d = d - 256 if d > 127 else d
            self.t += 8
            return (self._get_hl(idx) + d) & 0xffff
        return (self.h << 8) | self.l

    def _main(self, op, idx):
        x, y, z = op >> 6, (op >> 3) & 7, op & 7
        p, q = y >> 1, y & 1
        if x == 1:
            if op == 0x76:
                self.halted = True
                self.pc = (self.pc - 1) & 0xffff
                self.t += 4
                return
            if y == 6:  # LD (HL),r  -> r sin indice
                addr = self._addr_hl(idx)
                self.wb(addr, self.get_r(z))
            elif z == 6:
                addr = self._addr_hl(idx)
                self.set_r(y, self.rb(addr))
            else:
                self.set_r(y, self.get_r(z, idx), idx)
            self.t += 4
            return
        if x == 2:
            if z == 6:
                v = self.rb(self._addr_hl(idx)); self.t += 7
            else:
                v = self.get_r(z, idx); self.t += 4
            self.alu(y, v)
            return
        if x == 0:
            if z == 0:
                if y == 0: self.t += 4
                elif y == 1:
                    self.a, self.a_ = self.a_, self.a
                    self.f, self.f_ = self.f_, self.f
                    self.t += 4
                elif y == 2:
                    d = self.fetch(); d = d - 256 if d > 127 else d
                    self.b = (self.b - 1) & 0xff
                    if self.b:
                        self.pc = (self.pc + d) & 0xffff; self.t += 13
                    else:
                        self.t += 8
                else:
                    d = self.fetch(); d = d - 256 if d > 127 else d
                    if y == 3 or self.cond(y - 4):
                        self.pc = (self.pc + d) & 0xffff; self.t += 12
                    else:
                        self.t += 7
            elif z == 1:
                if q == 0:
                    self.set_rp(p, self.fetchw(), idx); self.t += 10
                else:
                    self.set_rp(2, self.add16(self.get_rp(2, idx), self.get_rp(p, idx)), idx); self.t += 11
            elif z == 2:
                if q == 0:
                    if p == 0: self.wb((self.b << 8) | self.c, self.a); self.t += 7
                    elif p == 1: self.wb((self.d << 8) | self.e, self.a); self.t += 7
                    elif p == 2: self.ww(self.fetchw(), self.get_rp(2, idx)); self.t += 16
                    else: self.wb(self.fetchw(), self.a); self.t += 13
                else:
                    if p == 0: self.a = self.rb((self.b << 8) | self.c); self.t += 7
                    elif p == 1: self.a = self.rb((self.d << 8) | self.e); self.t += 7
                    elif p == 2: self.set_rp(2, self.rw(self.fetchw()), idx); self.t += 16
                    else: self.a = self.rb(self.fetchw()); self.t += 13
            elif z == 3:
                v = self.get_rp(p, idx)
                self.set_rp(p, v + (1 if q == 0 else -1), idx); self.t += 6
            elif z == 4 or z == 5:
                if y == 6:
                    addr = self._addr_hl(idx)
                    v = self.rb(addr)
                    self.wb(addr, self.inc8(v) if z == 4 else self.dec8(v)); self.t += 11
                else:
                    v = self.get_r(y, idx)
                    self.set_r(y, self.inc8(v) if z == 4 else self.dec8(v), idx); self.t += 4
            elif z == 6:
                if y == 6:
                    addr = self._addr_hl(idx)
                    self.wb(addr, self.fetch()); self.t += 10
                else:
                    self.set_r(y, self.fetch(), idx); self.t += 7
            else:
                a, f = self.a, self.f
                if y == 0:
                    c = a >> 7; self.a = ((a << 1) | c) & 0xff
                    self.f = (f & (SF | ZF | PF)) | (self.a & (YF | XF)) | c
                elif y == 1:
                    c = a & 1; self.a = (a >> 1) | (c << 7)
                    self.f = (f & (SF | ZF | PF)) | (self.a & (YF | XF)) | c
                elif y == 2:
                    c = a >> 7; self.a = ((a << 1) | (f & CF)) & 0xff
                    self.f = (f & (SF | ZF | PF)) | (self.a & (YF | XF)) | c
                elif y == 3:
                    c = a & 1; self.a = (a >> 1) | ((f & CF) << 7)
                    self.f = (f & (SF | ZF | PF)) | (self.a & (YF | XF)) | c
                elif y == 4:
                    self.daa()
                elif y == 5:
                    self.a = a ^ 0xff
                    self.f = (f & (SF | ZF | PF | CF)) | HF | NF | (self.a & (YF | XF))
                elif y == 6:
                    self.f = (f & (SF | ZF | PF)) | CF | (a & (YF | XF))
                else:
                    self.f = ((f & (SF | ZF | PF | CF)) | (HF if f & CF else 0) | (a & (YF | XF))) ^ CF
                self.t += 4
            return
        # x == 3
        if z == 0:
            if self.cond(y):
                self.pc = self.pop(); self.t += 11
            else:
                self.t += 5
        elif z == 1:
            if q == 0:
                self.set_rp2(p, self.pop(), idx); self.t += 10
            else:
                if p == 0: self.pc = self.pop(); self.t += 10
                elif p == 1:
                    for r in ('b', 'c', 'd', 'e', 'h', 'l'):
                        v = getattr(self, r); setattr(self, r, getattr(self, r + '_')); setattr(self, r + '_', v)
                    self.t += 4
                elif p == 2: self.pc = self._get_hl(idx); self.t += 4
                else: self.sp = self._get_hl(idx); self.t += 6
        elif z == 2:
            nn = self.fetchw()
            if self.cond(y): self.pc = nn
            self.t += 10
        elif z == 3:
            if y == 0: self.pc = self.fetchw(); self.t += 10
            elif y == 2: self.port_out((self.a << 8) | self.fetch(), self.a); self.t += 11
            elif y == 3: self.a = self.port_in((self.a << 8) | self.fetch()) & 0xff; self.t += 11
            elif y == 4:
                v = self.rw(self.sp); self.ww(self.sp, self._get_hl(idx)); self._set_hl(v, idx); self.t += 19
            elif y == 5:
                de = (self.d << 8) | self.e
                self.d, self.e, self.h, self.l = self.h, self.l, self.d, self.e
                self.t += 4
            elif y == 6: self.iff1 = self.iff2 = 0; self.t += 4
            elif y == 7: self.iff1 = self.iff2 = 1; self.ei_delay = True; self.t += 4
        elif z == 4:
            nn = self.fetchw()
            if self.cond(y):
                self.push(self.pc); self.pc = nn; self.t += 17
            else:
                self.t += 10
        elif z == 5:
            if q == 0:
                self.push(self.get_rp2(p, idx)); self.t += 11
            elif p == 0:
                nn = self.fetchw(); self.push(self.pc); self.pc = nn; self.t += 17
        elif z == 6:
            self.alu(y, self.fetch()); self.t += 7
        else:
            self.push(self.pc); self.pc = y * 8; self.t += 11

    def _cb(self, op):
        x, y, z = op >> 6, (op >> 3) & 7, op & 7
        hl = (self.h << 8) | self.l
        v = self.get_r(z, None, hl)
        self.t += 15 if z == 6 else 8
        if x == 0:
            self.set_r(z, self.rot(y, v), None, hl)
        elif x == 1:
            r = v & (1 << y)
            self.f = (self.f & CF) | HF | (ZF | PF if not r else 0) | (SF if (y == 7 and r) else 0) | (v & (YF | XF))
            self.t -= 3 if z == 6 else 0
        elif x == 2:
            self.set_r(z, v & ~(1 << y), None, hl)
        else:
            self.set_r(z, v | (1 << y), None, hl)

    def _ddcb(self, idx, addr, op):
        x, y, z = op >> 6, (op >> 3) & 7, op & 7
        v = self.rb(addr)
        self.t += 23
        if x == 1:
            r = v & (1 << y)
            self.f = (self.f & CF) | HF | (ZF | PF if not r else 0) | (SF if (y == 7 and r) else 0) | ((addr >> 8) & (YF | XF))
            self.t -= 3
            return
        if x == 0: v = self.rot(y, v)
        elif x == 2: v &= ~(1 << y)
        else: v |= 1 << y
        self.wb(addr, v)
        if z != 6:
            self.set_r(z, v)

    def _ed(self, op):
        x, y, z = op >> 6, (op >> 3) & 7, op & 7
        p, q = y >> 1, y & 1
        self.r = (self.r & 0x80) | ((self.r + 1) & 0x7f)
        if x == 1:
            if z == 0:
                v = self.port_in((self.b << 8) | self.c) & 0xff
                if y != 6: self.set_r(y, v)
                self.f = (self.f & CF) | SZP[v]; self.t += 12
            elif z == 1:
                self.port_out((self.b << 8) | self.c, 0 if y == 6 else self.get_r(y)); self.t += 12
            elif z == 2:
                hl = (self.h << 8) | self.l
                v = self.sbc16(hl, self.get_rp(p)) if q == 0 else self.adc16(hl, self.get_rp(p))
                self.h, self.l = v >> 8, v & 0xff; self.t += 15
            elif z == 3:
                nn = self.fetchw()
                if q == 0: self.ww(nn, self.get_rp(p))
                else: self.set_rp(p, self.rw(nn))
                self.t += 20
            elif z == 4:
                a = self.a; self.a = 0; self.alu(2, a); self.t += 8
            elif z == 5:
                self.pc = self.pop(); self.iff1 = self.iff2; self.t += 14
            elif z == 6:
                self.im = [0, 0, 1, 2, 0, 0, 1, 2][y]; self.t += 8
            else:
                if y == 0: self.i = self.a
                elif y == 1: self.r = self.a
                elif y == 2:
                    self.a = self.i; self.f = (self.f & CF) | SZ[self.a] | (PF if self.iff2 else 0)
                elif y == 3:
                    self.a = self.r; self.f = (self.f & CF) | SZ[self.a] | (PF if self.iff2 else 0)
                elif y == 4:  # RRD
                    hl = (self.h << 8) | self.l; v = self.rb(hl)
                    self.wb(hl, ((self.a << 4) | (v >> 4)) & 0xff)
                    self.a = (self.a & 0xf0) | (v & 0x0f)
                    self.f = (self.f & CF) | SZP[self.a]
                elif y == 5:  # RLD
                    hl = (self.h << 8) | self.l; v = self.rb(hl)
                    self.wb(hl, ((v << 4) | (self.a & 0x0f)) & 0xff)
                    self.a = (self.a & 0xf0) | (v >> 4)
                    self.f = (self.f & CF) | SZP[self.a]
                self.t += 9
            return
        if x == 2 and z <= 3 and y >= 4:
            self._block(y, z)
            return
        self.t += 8  # NOP de ED

    def _block(self, y, z):
        bc = (self.b << 8) | self.c
        de = (self.d << 8) | self.e
        hl = (self.h << 8) | self.l
        inc = 1 if y in (4, 6) else -1
        rep = y >= 6
        if z == 0:  # LDI/LDD/LDIR/LDDR
            v = self.rb(hl); self.wb(de, v)
            hl += inc; de += inc; bc = (bc - 1) & 0xffff
            n = (v + self.a) & 0xff
            self.f = (self.f & (SF | ZF | CF)) | (PF if bc else 0) | (n & XF) | ((n << 4) & YF)
        elif z == 1:  # CPI/CPD/CPIR/CPDR
            v = self.rb(hl); r = (self.a - v) & 0xff
            hl += inc; bc = (bc - 1) & 0xffff
            h = HF if ((self.a ^ v ^ r) & 0x10) else 0
            n = (r - (1 if h else 0)) & 0xff
            self.f = (self.f & CF) | (SZ[r] & ~(YF | XF)) | h | NF | (PF if bc else 0) | (n & XF) | ((n << 4) & YF)
            if rep and r == 0:
                rep = False
        elif z == 2:  # INI...
            v = self.port_in((self.b << 8) | self.c) & 0xff; self.wb(hl, v)
            hl += inc; self.b = (self.b - 1) & 0xff; bc = (self.b << 8) | self.c
            self.f = SZ[self.b] | NF
        else:  # OUTI...
            v = self.rb(hl); self.b = (self.b - 1) & 0xff
            self.port_out((self.b << 8) | self.c, v)
            hl += inc; bc = (self.b << 8) | self.c
            self.f = SZ[self.b] | NF
        self.h, self.l = (hl >> 8) & 0xff, hl & 0xff
        if z in (0, 1):
            self.b, self.c = bc >> 8, bc & 0xff
            self.d, self.e = (de >> 8) & 0xff, de & 0xff
            more = bc != 0
        else:
            more = self.b != 0
        if rep and more:
            self.pc = (self.pc - 2) & 0xffff; self.t += 21
        else:
            self.t += 16


# ---------------------------------------------------------------- desensamblador
def disasm(mem, pc):
    """Devuelve (texto, longitud) de la instruccion en pc."""
    start = pc
    def b():
        nonlocal pc
        v = mem[pc & 0xffff]; pc += 1; return v
    def w():
        lo = b(); hi = b(); return lo | (hi << 8)
    def sd(v): return v - 256 if v > 127 else v
    op = b(); idx = None
    if op in (0xdd, 0xfd):
        idx = 'ix' if op == 0xdd else 'iy'; op = b()
        if op == 0xcb:
            d = sd(b()); o2 = b(); x, y, z = o2 >> 6, (o2 >> 3) & 7, o2 & 7
            m = f'({idx}{d:+d})'
            if x == 0: t = f'{ROT[y]} {m}'
            elif x == 1: t = f'bit {y},{m}'
            elif x == 2: t = f'res {y},{m}'
            else: t = f'set {y},{m}'
            if x != 1 and z != 6: t += f',{R8[z]}'
            return t, pc - start
    if op == 0xcb:
        o2 = b(); x, y, z = o2 >> 6, (o2 >> 3) & 7, o2 & 7
        t = [f'{ROT[y]} {R8[z]}', f'bit {y},{R8[z]}', f'res {y},{R8[z]}', f'set {y},{R8[z]}'][x]
        return t, pc - start
    if op == 0xed:
        o2 = b(); x, y, z = o2 >> 6, (o2 >> 3) & 7, o2 & 7; p, q = y >> 1, y & 1
        if x == 1:
            if z == 0: t = f'in {R8[y] if y != 6 else "f"},(c)'
            elif z == 1: t = f'out (c),{R8[y] if y != 6 else "0"}'
            elif z == 2: t = f'{"sbc" if q == 0 else "adc"} hl,{RP[p]}'
            elif z == 3:
                nn = w(); t = f'ld (${nn:04x}),{RP[p]}' if q == 0 else f'ld {RP[p]},(${nn:04x})'
            elif z == 4: t = 'neg'
            elif z == 5: t = 'retn' if y != 1 else 'reti'
            elif z == 6: t = f'im {[0,0,1,2,0,0,1,2][y]}'
            else: t = ['ld i,a', 'ld r,a', 'ld a,i', 'ld a,r', 'rrd', 'rld', 'nop', 'nop'][y]
        elif x == 2 and z <= 3 and y >= 4:
            t = [['ldi', 'cpi', 'ini', 'outi'], ['ldd', 'cpd', 'ind', 'outd'], ['ldir', 'cpir', 'inir', 'otir'], ['lddr', 'cpdr', 'indr', 'otdr']][y - 4][z]
        else:
            t = f'db $ed,${o2:02x}'
        return t, pc - start
    x, y, z = op >> 6, (op >> 3) & 7, op & 7; p, q = y >> 1, y & 1
    hl = idx or 'hl'
    def r8(n):
        if n == 6:
            if idx: return f'({idx}{sd(b()):+d})'
            return '(hl)'
        if idx and n == 4: return idx + 'h'
        if idx and n == 5: return idx + 'l'
        return R8[n]
    rp = lambda n: hl if n == 2 else RP[n]
    rp2 = lambda n: hl if n == 2 else RP2[n]
    if x == 1:
        if op == 0x76: return 'halt', pc - start
        if y == 6: return f'ld {r8(6)},{R8[z]}', pc - start
        if z == 6: return f'ld {R8[y]},{r8(6)}', pc - start
        return f'ld {r8(y)},{r8(z)}', pc - start
    if x == 2: return f'{ALU[y]}{r8(z)}', pc - start
    if x == 0:
        if z == 0:
            if y == 0: t = 'nop'
            elif y == 1: t = "ex af,af'"
            else:
                d = sd(b()); tgt = (pc + d) & 0xffff
                t = ['', '', f'djnz ${tgt:04x}', f'jr ${tgt:04x}'][y] if y < 4 else f'jr {CC[y-4]},${tgt:04x}'
        elif z == 1: t = f'ld {rp(p)},${w():04x}' if q == 0 else f'add {hl},{rp(p)}'
        elif z == 2:
            if p < 2:
                t = ['ld (bc),a', 'ld (de),a'][p] if q == 0 else ['ld a,(bc)', 'ld a,(de)'][p]
            else:
                nn = w()
                if q == 0: t = f'ld (${nn:04x}),{hl}' if p == 2 else f'ld (${nn:04x}),a'
                else: t = f'ld {hl},(${nn:04x})' if p == 2 else f'ld a,(${nn:04x})'
        elif z == 3: t = f'{"inc" if q == 0 else "dec"} {rp(p)}'
        elif z == 4: t = f'inc {r8(y)}'
        elif z == 5: t = f'dec {r8(y)}'
        elif z == 6:
            dst = r8(y); t = f'ld {dst},${b():02x}'
        else: t = ['rlca', 'rrca', 'rla', 'rra', 'daa', 'cpl', 'scf', 'ccf'][y]
        return t, pc - start
    if z == 0: t = f'ret {CC[y]}'
    elif z == 1:
        if q == 0: t = f'pop {rp2(p)}'
        else: t = ['ret', 'exx', f'jp ({hl})', f'ld sp,{hl}'][p]
    elif z == 2: t = f'jp {CC[y]},${w():04x}'
    elif z == 3:
        if y == 0: t = f'jp ${w():04x}'
        elif y == 2: t = f'out (${b():02x}),a'
        elif y == 3: t = f'in a,(${b():02x})'
        else: t = ['', '', '', '', f'ex (sp),{hl}', 'ex de,hl', 'di', 'ei'][y]
    elif z == 4: t = f'call {CC[y]},${w():04x}'
    elif z == 5:
        if q == 0: t = f'push {rp2(p)}'
        else: t = f'call ${w():04x}'
    elif z == 6: t = f'{ALU[y]}${b():02x}'
    else: t = f'rst ${y*8:02x}'
    return t, pc - start
