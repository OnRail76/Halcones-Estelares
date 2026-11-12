#!/usr/bin/env python3
"""HALCONES ESTELARES 1.1 - juego mas justo, oleadas y marcador (emulador completo).
1. Caja de impacto con la silueta: un disparo que pasa por la punta del ala a la
   altura del morro ya no mata; uno en el morro o en el ala, si.
2. Ningun disparo enemigo nace a menos de 43 px del morro.
3. Al reaparecer: sin disparos enemigos en el aire y 2 s de invulnerabilidad.
4. Marcador de 16 bits: pasa de 2.550 puntos sin volver a 0; vida extra cada
   1.000 puntos (maximo 3 vidas).
5. Cartel OLEADA n antes de cada formacion, numerado 1..6, y luego la formacion.
6. Cadencia de disparo enemigo en tiempo real (ticks de 25/s)."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tests'/'emulador_completo'))
import harness
from harness import Speccy
TAP=str(R/'build'/'HALCONES_ESTELARES_V281.tap')
S=json.load(open(R/'build'/'starter.sym.json'))

def in_game():
    s=Speccy(tap=TAP,watch=False);m=s.z.m
    for f in range(300):
        s.frame({'SPACE'} if 90<=f<96 else ())
        if f>100 and m[S['card_ticks']]:break
    assert m[S['card_ticks']],'no empezo la partida'
    return s

def until_tick(s,label='combat_tick'):
    z=s.z
    for _ in range(2_000_000):
        if z.pc==S[label]:return
        z.step()
    raise AssertionError('no llego a '+label)

def call(s,label):
    """Ejecuta una rutina real con el SP del juego y vuelve."""
    z=s.z;m=z.m;ret=0x5f00;sp=z.sp
    z.sp-=2;m[z.sp]=ret&255;m[z.sp+1]=ret>>8;z.pc=S[label]
    for _ in range(500_000):
        if z.pc==ret and z.sp==sp:return
        z.step()
    raise AssertionError('no volvio '+label)

def test_caja_de_impacto():
    s=in_game();m=s.z.m;z=s.z
    pc,sp=z.pc,z.sp
    sx,sy=80,152
    cases=[(sx+0,sy-2,False,'ala izquierda a la altura del morro'),
           (sx+20,sy+2,False,'ala derecha a la altura del morro'),
           (sx+10,sy-2,True,'morro'),
           (sx+2,sy+14,True,'ala, abajo'),
           (sx+22,sy+14,False,'punta exterior del ala'),
           (sx+10,sy+30,False,'por debajo de la nave')]
    for bx,by,hit,what in cases:
        m[S['ship_x']]=sx;m[S['ship_y']]=sy;m[S['player_lives']]=3
        m[S['shield_invulnerable']]=0;m[S['grace_irqs']]=0;m[S['shield_state']]=0
        b=S['enemy_bullet_slots'];m[b:b+9]=bytes(9);m[b]=bx;m[b+1]=by-5;m[b+2]=1
        m[S['enemy_fire_cd']]=200
        call(s,'enemy_bullet_update')
        died=m[S['player_lives']]==2
        assert died==hit,(what,bx,by,died)
    z.pc,z.sp=pc,sp

def test_disparo_esquivable():
    s=in_game();m=s.z.m;z=s.z
    pc,sp=z.pc,z.sp
    for ey in (60,80,93,94,100,130):
        e=S['enemy_slots'];m[e:e+60]=bytes(60);m[e:e+6]=bytes([80,ey,1,0,80,0])
        b=S['enemy_bullet_slots'];m[b:b+9]=bytes(9)
        m[S['enemy_fire_cd']]=0;m[S['wave_stage']]=0;m[S['wave_cycle']]=0;m[S['shot_spawn_turn']]=5
        call(s,'enemy_bullet_update')
        spawned=m[b+2]==1
        assert spawned==(ey+15<=108),(ey,spawned)
        if spawned:assert m[b+1]<=108
    z.pc,z.sp=pc,sp

def test_reaparicion():
    s=in_game();m=s.z.m
    for _ in range(60):s.frame(())          # cartel fuera, formacion dentro
    m[S['grace_irqs']]=0;m[S['shield_invulnerable']]=0;m[S['shield_state']]=0
    # muerte real por un disparo en el morro
    b=S['enemy_bullet_slots'];m[b:b+3]=bytes([m[S['ship_x']]+10,m[S['ship_y']]-6,1])
    lives=m[S['player_lives']]
    for f in range(8):
        s.frame(())
        if m[S['player_lives']]<lives:break
    assert m[S['player_lives']]==lives-1,'el disparo en el morro debia matar'
    # disparos enemigos en el aire justo antes de reaparecer
    seen=False
    for f in range(140):
        if m[S['shield_invulnerable']]>52:
            for i in range(3):m[b+3*i:b+3*i+3]=bytes([60+20*i,100,1])
        s.frame(())
        if m[S['player_respawn_pending']]==0 and m[S['grace_irqs']]>0 and not seen:
            seen=True
            assert not any(m[b+3*i+2] for i in range(3)),'quedaron disparos enemigos al reaparecer'
            assert m[S['grace_irqs']]>=95
    assert seen,'no reaparecio'
    # durante la gracia los choques no quitan vida
    lives=m[S['player_lives']]
    m[b:b+3]=bytes([m[S['ship_x']]+10,m[S['ship_y']]-6,1])
    for f in range(6):s.frame(())
    assert m[S['player_lives']]==lives,'la gracia debe proteger'

def test_marcador_y_vida_extra():
    s=in_game();m=s.z.m;z=s.z
    pc,sp=z.pc,z.sp
    w=S['score_words']
    m[w]=255;m[w+1]=0;m[S['kills']]=255;m[S['life_next']]=0
    call(s,'score_add_kill')
    assert m[w]|m[w+1]<<8==256,'el marcador de 16 bits no debe volver a 0'
    d=S['score_digits'];assert list(m[d:d+4])==[0,2,5,6]
    m[w]=9999&255;m[w+1]=9999>>8
    call(s,'score_add_kill');assert m[w]|m[w+1]<<8==9999,'tope 99.990'
    m[S['player_lives']]=2;m[S['life_next']]=99
    call(s,'score_add_kill');assert m[S['player_lives']]==3 and m[S['life_next']]==0,'vida extra a los 1.000'
    m[S['life_next']]=99
    call(s,'score_add_kill');assert m[S['player_lives']]==3,'como mucho 3 vidas'
    z.pc,z.sp=pc,sp

def test_carteles():
    s=in_game();m=s.z.m
    assert m[S['card_wave']]==1 and not any(m[S['enemy_slots']+6*i+2] for i in range(10))
    s.screen(str(R/'build'/'V11_CARTEL_OLEADA_1.png'))
    for f in range(100):
        s.frame(())
        if m[S['card_ticks']]==0:break
    assert any(m[S['enemy_slots']+6*i+2] for i in range(10)),'tras el cartel entra la formacion'
    seq=[]
    for k in range(5):
        for i in range(10):m[S['enemy_slots']+6*i+2]=0
        for f in range(12):
            s.frame(())
            if m[S['card_ticks']]:break
        seq.append(m[S['card_wave']])
        for f in range(100):
            s.frame(())
            if m[S['card_ticks']]==0:break
    assert seq==[2,3,4,5,6],seq

def test_cadencia():
    s=in_game();m=s.z.m;z=s.z
    pc,sp=z.pc,z.sp
    for stage,cycle,period in ((0,0,80),(1,0,64),(2,0,32),(2,1,20),(2,4,11),(0,2,61)):
        m[S['wave_stage']]=stage;m[S['wave_cycle']]=cycle;m[S['enemy_fire_cd']]=0
        e=S['enemy_slots'];m[e:e+60]=bytes(60);m[e:e+6]=bytes([80,20,1,0,80,0])
        shots=[]
        for t in range(period*2+4):
            b=S['enemy_bullet_slots'];m[b:b+9]=bytes(9)
            call(s,'enemy_bullet_update')
            if m[b+2]:shots.append(t)
        assert shots[:3]==[0,period+1,2*(period+1)],(stage,cycle,period,shots)
    z.pc,z.sp=pc,sp

if __name__=='__main__':
    for t in (test_caja_de_impacto,test_disparo_esquivable,test_reaparicion,test_marcador_y_vida_extra,test_carteles,test_cadencia):
        t();print('PASS',t.__name__,flush=True)
    print('PASS V1.1 justicia: silueta, disparos esquivables, reaparicion limpia, marcador 16 bits + vida extra, carteles, cadencia en tiempo real')
