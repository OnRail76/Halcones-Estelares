#!/usr/bin/env python3
"""HALCONES ESTELARES 1.1 - controles, ritmo fijo y pausa (emulador Z80 completo).
1. Sin Kempston (bus flotante $FF): se empieza con SPACE y el puerto $1F no se
   vuelve a leer durante la partida.
2. Con Kempston: empezar con SU fuego = partida con joystick (izquierda, derecha,
   fuego y escudo con arriba/abajo).
3. Con Kempston conectado pero empezando con SPACE: se juega con teclado.
4. Sinclair (6/7/8/9/0) funciona siempre.
5. H pausa: el escudo activo no se gasta en pausa; otra H continua.
6. El juego avanza a 25 ticks/s fijos (2 interrupciones por tick)."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tests'/'emulador_completo'))
import harness
from harness import Speccy
TAP=str(R/'build'/'HALCONES_ESTELARES_V281.tap')
S=json.load(open(R/'build'/'starter.sym.json'))

def boot(kempston=0xff,start='SPACE'):
    s=Speccy(tap=TAP,watch=False);s.kempston=kempston;z=s.z;m=z.m
    reads=[0];op=s.port_in
    def pin(port):
        if port&0xff==0x1f:reads[0]+=1
        return op(port)
    z.port_in=pin
    for f in range(400):
        if m[S['tick_irqs']] and z.pc>=S['combat_tick']-0x2000 and S['main_loop']<=z.pc<0xc000 and f>100:break
        press=90<=f<96
        if start=='KEMPSTON':
            s.kempston=(kempston|0x10) if press else kempston
            s.frame(())
        else:
            s.frame({start} if press else ())
    # esperar a estar dentro de la partida
    for f in range(200):
        s.frame(())
        if m[S['card_ticks']]:break
    assert m[S['card_ticks']],'la partida no empezo'
    return s,reads

def ship_after(s,keys=(),kemp=None,frames=20):
    m=s.z.m;x0=m[S['ship_x']]
    for f in range(frames):
        if kemp is not None:s.kempston=kemp
        s.frame(keys)
    return m[S['ship_x']]-x0

def test_sin_kempston():
    s,reads=boot(0xff,'SPACE');m=s.z.m
    assert m[S['kempston_ok']]==0 and m[S['kempston_mode']]==0
    r0=reads[0]
    assert ship_after(s,{'O'})<0 and ship_after(s,{'P'})>0
    assert reads[0]==r0,'sin Kempston no se debe leer el puerto 1F en partida'

def test_kempston():
    s,reads=boot(0x00,'KEMPSTON');m=s.z.m
    assert m[S['kempston_ok']]==1 and m[S['kempston_mode']]==1
    assert ship_after(s,(),kemp=0x02)<0,'Kempston izquierda'
    assert ship_after(s,(),kemp=0x01)>0,'Kempston derecha'
    # fuego: aparece un disparo del jugador
    for f in range(30):s.kempston=0x10 if f%6<3 else 0;s.frame(())
    assert any(m[S['bullet_slots']+3*i+2] for i in range(9)) or m[S['kills']] ,'Kempston fuego'
    # escudo con arriba
    s.kempston=0x08
    for f in range(4):s.frame(())
    s.kempston=0
    assert m[S['shield_state']]==1,'Kempston arriba = escudo'

def test_kempston_pero_teclado():
    s,reads=boot(0x00,'SPACE');m=s.z.m
    assert m[S['kempston_ok']]==1 and m[S['kempston_mode']]==0
    r0=reads[0]
    assert ship_after(s,(),kemp=0x02)==0,'empezando con SPACE el joystick no cuenta'
    assert ship_after(s,{'O'})<0
    assert reads[0]==r0

def test_sinclair_y_pausa():
    s,reads=boot(0xff,'0');m=s.z.m
    assert ship_after(s,{'6'})<0 and ship_after(s,{'7'})>0,'Sinclair 6/7'
    for f in range(4):s.frame({'9'})
    assert m[S['shield_state']]==1,'Sinclair 9 = escudo'
    t0=m[S['shield_timer']]|m[S['shield_timer']+1]<<8
    for f in range(4):s.frame({'H'})
    for f in range(100):s.frame(())
    t1=m[S['shield_timer']]|m[S['shield_timer']+1]<<8
    assert m[S['game_paused']]==1 and s.border==1,'H pausa con borde azul'
    assert t1>=t0-6,('el escudo no debe gastarse en pausa',t0,t1)
    for f in range(4):s.frame({'H'})
    for f in range(10):s.frame(())
    assert m[S['game_paused']]==0 and s.border==0,'H continua'

def test_ritmo_fijo():
    s,reads=boot(0xff,'SPACE');m=s.z.m;z=s.z
    ticks=[];tick=S['combat_tick'];last=[None]
    for f in range(300):
        end=z.t+harness.FRAME
        s.keys=set()
        while z.t<end:
            if z.pc==tick:ticks.append(s.frames)
            z.step()
        s.frames+=1
        if z.iff1 and not z.ei_delay:
            pc0,sp0=((z.pc+1)&0xffff if z.halted else z.pc),z.sp
            if z.interrupt():
                while not(z.pc==pc0 and z.sp==sp0):z.step()
    gaps=[b-a for a,b in zip(ticks,ticks[1:])]
    assert gaps.count(2)>=len(gaps)*0.97 and min(gaps)>=2,('25 ticks/s fijos',sorted(set(gaps)))

if __name__=='__main__':
    for t in (test_sin_kempston,test_kempston,test_kempston_pero_teclado,test_sinclair_y_pausa,test_ritmo_fijo):
        t();print('PASS',t.__name__,flush=True)
    print('PASS V1.1 controles: teclado, Sinclair, Kempston automatico, pausa H, 25 ticks/s')
