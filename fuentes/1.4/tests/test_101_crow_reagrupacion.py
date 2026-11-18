#!/usr/bin/env python3
"""FINAL 1.0.1 - fallo del CROW con 0 puntos (reset / bloqueo en Fuse, Speccy,
Spectaculator). Usa un emulador Z80 COMPLETO (tests/emulador_completo), no el
mini_z80 parcial, y barre la velocidad de CPU respecto al fotograma para cubrir
la contencion de memoria del Spectrum real.

Causa: crow_scout_return restaba 3 a la Y sin comprobar acarreo; con Y<3 la Y
daba la vuelta a 253..255, el compositor indexaba scanline_table mas alla de
sus 192 lineas y el LDI escribia sobre el codigo (call $8635 -> call $1035).
Se comprueba: (1) partida a 0 puntos sin tocar nada termina en GAME OVER a
todas las velocidades, CON y SIN el guardia de la V2.8.9; (2) ningun sprite
llega al compositor con Y>=192."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tests'/'emulador_completo'))
import harness
from harness import Speccy
TAP=str(R/'build'/'HALCONES_ESTELARES_V281.tap')
S=json.load(open(R/'build'/'starter.sym.json'))
def guard_addr(m,target):
    for a in range(0x8000,0xa000):
        if m[a]==0xca and m[a+1]|(m[a+2]<<8)==target:return a
    raise AssertionError('guardia V2.8.9 no encontrado')
def run(fl,guard,maxf=1500):
    harness.FRAME=fl
    def patch(z):
        if not guard:
            a=guard_addr(z.m,S['combat_last_death_freeze']);z.m[a:a+3]=b'\x00\x00\x00'
    s=Speccy(patch=patch,tap=TAP);z=s.z;bad=[0];oh=z.write_hook
    def wh(a,v):
        if a==S['spr_y'] and v>=192:bad[0]+=1
        oh(a,v)
    z.write_hook=wh;started=None
    try:
        for f in range(maxf):
            pc=z.pc
            # V1.2: el titulo toca musica mientras espera: se pulsa SPACE un momento
            # y la partida se da por empezada al aparecer el cartel OLEADA 1.
            s.frame({'SPACE'} if (60<=s.frames<66 and started is None) else ())
            if started is None and z.m[S['card_ticks']]:started=s.frames
            assert z.pc>=0x4000,('RESET: pc en ROM',hex(z.pc),fl,guard)
            assert not any(e[1]=='BLOQUEO' for e in s.events),('BLOQUEO',fl,guard)
            # V1.2: las esperas del GAME OVER tocan musica (ya no son HALT); se
            # detecta la pantalla por su temporizador de 3 s ya armado.
            if started and z.m[S['gameover_mode']]==1:
                assert bad[0]==0,('sprite con Y>=192',bad[0],fl,guard)
                return s.frames
        raise AssertionError(('sin GAME OVER',fl,guard))
    finally:
        harness.FRAME=69888
if __name__=='__main__':
    for fl in (69888,60000,50000):
        for guard in (True,False):
            run(fl,guard)
    print('PASS FINAL 1.0.1: 0 puntos sin tocar nada -> GAME OVER a 3 velocidades, con y sin guardia V2.8.9; ningun sprite con Y>=192')
