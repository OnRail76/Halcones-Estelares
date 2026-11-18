#!/usr/bin/env python3
"""Arnes para HALCONES ESTELARES: carga el TAP, simula 50 Hz, teclado y vigila
la maquina (registros a traves de la interrupcion, pila, tabla IM2, testigos)."""
from PIL import Image
from z80emu import Z80, disasm
from loadtap import load

FRAME = 69888
KEYS = {  # tecla -> (fila de media linea, bit)
    'SPACE': (0x7f, 0), 'O': (0xdf, 1), 'P': (0xdf, 0), 'A': (0xfd, 0), 'Q': (0xfb, 0),
    'ENTER': (0xbf, 0), 'H': (0xbf, 4), '0': (0xef, 0),
    '6': (0xef, 4), '7': (0xef, 3), '8': (0xef, 2), '9': (0xef, 1),
}
REGS = ['b', 'c', 'd', 'e', 'ix', 'iy', 'a_', 'f_', 'b_', 'c_', 'd_', 'e_', 'h_', 'l_']


class Speccy:
    def __init__(self, patch=None, watch=True, tap=None):
        self.z = z = Z80()
        load(z, tap)
        if patch:
            patch(z)
        z.pc = 0x8000
        z.sp = 0x7ffe
        self.keys = set()
        self.kempston = 0xff
        z.port_in = self.port_in
        z.port_out = self.port_out
        self.border = 0
        self.frames = 0
        self.events = []
        self.int_snap = []
        self.watch = watch
        self.beeper = 0
        if watch:
            z.write_hook = self.on_write
        self.handler = z.rw(0xfdfe) if z.m[0xfdfd] == 0xc3 else None

    def port_in(self, port):
        if port & 0xff == 0x1f:
            return self.kempston
        if port & 1 == 0:
            v = 0xff
            hi = port >> 8
            for k in self.keys:
                row, bit = KEYS[k]
                if (~hi & ~row) & 0xff:
                    v &= ~(1 << bit)
            return v
        return 0xff

    def port_out(self, port, v):
        if port & 1 == 0:
            self.border = v & 7
            self.beeper += 1

    def on_write(self, a, v):
        z = self.z
        if 0xfe00 <= a <= 0xff00 and v != 0xfd and z.m[0xfdfd] == 0xc3:
            self.events.append((self.frames, 'TABLA IM2', hex(a), hex(v), hex(z.pc), hex(z.sp)))
        elif a in (0xf000, 0xf400, 0xfdfa, 0xff01, 0xfdfd, 0xfdfe, 0xfdff) and z.m[a] != v and self.frames > 2:
            self.events.append((self.frames, 'TESTIGO/VECTOR', hex(a), hex(z.m[a]), '->', hex(v), 'pc', hex(z.pc), 'sp', hex(z.sp)))

    def frame(self, keys=()):
        z = self.z
        self.keys = set(keys)
        end = z.t + FRAME
        while z.t < end:
            z.step()
            if z.pc == 0x807d and not any(e[1] == 'BLOQUEO' for e in self.events):
                self.events.append((self.frames, 'BLOQUEO', 'guardia del bucle principal (borde rojo)'))
        self.frames += 1
        if z.iff1 and not z.ei_delay:
            pc0, sp0 = (z.pc + 1) & 0xffff if z.halted else z.pc, z.sp
            snap = {r: getattr(z, r) for r in REGS}
            if not (0xff02 <= sp0 <= 0xfff0) and self.watch:
                self.events.append((self.frames, 'INT CON PILA FUERA', hex(sp0), 'pc', hex(pc0)))
            if z.interrupt():
                # ejecutar el manejador hasta que vuelva al punto interrumpido
                guard = 0
                while not (z.pc == pc0 and z.sp == sp0) and guard < 400000:
                    z.step(); guard += 1
                if self.watch:
                    diff = [r for r in REGS if getattr(z, r) != snap[r]]
                    if diff:
                        self.events.append((self.frames, 'INT CAMBIA REGISTROS', diff, 'pc', hex(pc0)))

    def run(self, n, keys=()):
        for _ in range(n):
            self.frame(keys)

    def screen(self, path, scale=3):
        m = self.z.m
        P = [(0, 0, 0), (0, 0, 205), (205, 0, 0), (205, 0, 205), (0, 205, 0), (0, 205, 205), (205, 205, 0), (205, 205, 205)]
        B = [(0, 0, 0), (0, 0, 255), (255, 0, 0), (255, 0, 255), (0, 255, 0), (0, 255, 255), (255, 255, 0), (255, 255, 255)]
        im = Image.new('RGB', (256, 192))
        px = im.load()
        for y in range(192):
            for xb in range(32):
                byte = m[0x4000 | ((y & 0xc0) << 5) | ((y & 7) << 8) | ((y & 0x38) << 2) | xb]
                at = m[0x5800 + (y >> 3) * 32 + xb]
                pal = B if at & 64 else P
                ink, paper = pal[at & 7], pal[(at >> 3) & 7]
                for bit in range(8):
                    px[xb * 8 + bit, y] = ink if byte & (128 >> bit) else paper
        im.resize((256 * scale, 192 * scale), Image.NEAREST).save(path)
