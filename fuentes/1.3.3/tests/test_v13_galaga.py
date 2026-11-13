#!/usr/bin/env python3
"""HALCONES ESTELARES 1.3 - disparo limitado, 10 cuervos y fondos (emulador Z80 completo).
1. Como mucho 2 balas propias en pantalla a la vez, a 12 px por tick; al
   desaparecer una, se puede volver a disparar.
2. La primera oleada trae 10 cuervos (dos filas de 5) y el resto 6 enemigos.
3. V1.3.3: sin fondos lejanos (choque de color): el cielo inmovil (D800)
   queda vacio en las oleadas de todas las fases; el MOAI sigue con su luna
   y Jupiter.
4. Pantalla y sombra de atributos coinciden al acabar cada tick (sin celdas
   rojas olvidadas al moverse los cuervos).
5. Sonido: el efecto suena tambien a mitad de tick (interrupcion intermedia),
   no solo al final, y el juego sigue a 25 ticks/s.
6. La insignia ESF brilla (franja diagonal de color) al empezar la oleada y
   vuelve a quedar blanca; pantalla y sombra iguales.
8. V1.3.3: los efectos de golpe (disparo, estallido...) suenan como una sola
   rafaga corta (unos 5 ms) por tick, no cortados en trozos.
7. La melodia del titulo suena una vez cada vez que se llega al titulo (al
   cargar y despues de cada Game Over) y luego hay silencio."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tests'/'emulador_completo'))
import harness
from harness import Speccy
TAP=str(R/'build'/'HALCONES_ESTELARES_V281.tap')
S=json.load(open(R/'build'/'starter.sym.json'))
ROWS=[((y&0xc0)<<5)|((y&7)<<8)|((y&0x38)<<2) for y in range(192)]

def in_game():
    s=Speccy(tap=TAP,watch=False);m=s.z.m
    for f in range(400):
        s.frame({'SPACE'} if 90<=f<96 else ())
        if f>100 and m[S['card_ticks']]:break
    assert m[S['card_ticks']]
    m[S['player_take_hit']]=0xc9
    return s

def band(m):
    """Cielo inmutable en la franja de los fondos (y=88..151, columnas 2..21)."""
    return bytes(m[0xd800+ROWS[y]+c] for y in range(88,152) for c in range(2,22))

def alive(m):
    return sum(1 for i in range(10) if m[S['enemy_slots']+6*i+2])

def test_disparo():
    s=in_game();m=s.z.m
    for f in range(100):
        s.frame(())
        if m[S['card_ticks']]==0:break
    b=S['bullet_slots']
    most=0;ys=[]
    for f in range(60):
        s.frame({'SPACE'} if f%4<2 else ())
        live=[m[b+3*j+1] for j in range(2) if m[b+3*j+2]]
        most=max(most,len(live))
        if live:ys.append(min(live))
    assert most==2,('balas a la vez',most)
    steps=[a-c for a,c in zip(ys,ys[1:]) if 0<a-c<40]
    assert steps and max(steps)<=24 and 12 in steps,('velocidad',sorted(set(steps)))

def test_formacion_y_fondos():
    s=in_game();m=s.z.m
    for f in range(100):
        s.frame(())
        if m[S['card_ticks']]==0:break
    assert alive(m)==10 and m[S['enemy_count']]==10,'10 cuervos'
    assert not any(band(m)),'sin fondo en la fase 1'
    for f in range(60):s.frame(())
    s.screen(str(R/'build'/'V13_FASE1_CUERVOS.png'))
    # pasar a la segunda oleada: 6 enemigos
    for f in range(1500):
        if m[S['card_ticks']]==0 and alive(m):
            if m[S['wave_stage']]==1:break
            for i in range(10):m[S['enemy_slots']+6*i+2]=0
        s.frame(())
    assert m[S['enemy_count']]==6 and alive(m)<=6,'oleada de 6'
    # MOAI: el fondo se borra
    for i in range(10):m[S['enemy_slots']+6*i+2]=0
    m[S['wave_stage']]=2;m[S['wave_repeat']]=1;m[S['wave_done']]=1;m[S['card_ticks']]=0
    for f in range(30):
        s.frame(())
        if m[S['wave_stage']]==3 and m[S['boss_hp']]:break
    for f in range(10):s.frame(())
    assert m[S['wave_stage']]==3
    sky=bytes(m[0xd800+ROWS[y]+c] for y in range(96,152) for c in range(16,23))
    assert any(sky),'Jupiter en el cielo del MOAI'
    # derrotar al MOAI: la fase 2 trae otro fondo
    m[S['boss_hp']]=1;b=S['bullet_slots'];m[b:b+3]=bytes([96,60,1])
    for f in range(900):
        s.frame(())
        if m[S['phase_number']]==2 and m[S['wave_stage']]==0 and m[S['card_ticks']]:break
    assert m[S['phase_number']]==2
    for f in range(4):s.frame(())
    assert not any(band(m)),'sin fondo en la fase 2 (y sin restos del MOAI)'
    s.screen(str(R/'build'/'V13_FASE2_FONDO.png'))

def test_atributos_coherentes():
    s=in_game();m=s.z.m;z=s.z
    bad=[];ticks=0
    orig=z.step
    def step():
        nonlocal ticks
        orig()
        if z.pc==S['main_loop']:
            ticks+=1
            if m[S['card_ticks']]==0:
                d=[i for i in range(768) if m[0x5800+i]!=m[0xf100+i]]
                if d:bad.append((ticks,d[:4]))
    z.step=step
    for f in range(500):s.frame({'SPACE'} if f%6<3 else ())
    z.step=orig
    assert ticks>150 and not bad,('atributos sin presentar',bad[:5])

def test_sonido_mitad_de_tick():
    s=in_game();z=s.z;m=z.m
    for f in range(100):
        s.frame(())
        if m[S['card_ticks']]==0:break
    outs=[];op=s.port_out
    def po(port,v):
        if port&1==0:outs.append(z.t)
        op(port,v)
    z.port_out=po
    starts=[];t=S['combat_tick'];irq_t=[]
    for f in range(120):
        s.keys={'SPACE'} if f%8<4 else set();end=z.t+harness.FRAME
        while z.t<end:
            if z.pc==t:starts.append(z.t)
            z.step()
        s.frames+=1
        if z.iff1 and not z.ei_delay:
            pc0,sp0=((z.pc+1)&0xffff if z.halted else z.pc),z.sp
            irq_t.append(z.t)
            if z.interrupt():
                while not(z.pc==pc0 and z.sp==sp0):z.step()
    import bisect
    mid=0
    for a in irq_t:
        i=bisect.bisect_left(starts,a)
        if 0<i<len(starts) and a-starts[i-1]<harness.FRAME+5000:
            k=bisect.bisect_left(outs,a)
            if k<len(outs) and outs[k]-a<3000:mid+=1
    assert mid>=10,('sin sonido a mitad de tick',mid)
    assert len(starts)>=55,len(starts)

def test_brillo_insignia():
    s=in_game();m=s.z.m
    assert m[S['badge_pos']]==1,'brilla al empezar la oleada'
    seen=set()
    for f in range(40):
        s.frame(())
        for r in range(15,23):
            for c in range(25,31):seen.add(m[0x5800+r*32+c])
    assert {0x45,0x46,0x47}<=seen,seen
    assert m[S['badge_pos']]==0
    assert all(m[0x5800+r*32+c]==0x47 and m[0xf100+r*32+c]==0x47 for r in range(15,23) for c in range(25,31))
    s.screen(str(R/'build'/'V13_INSIGNIA.png'))

def title_music(s,start):
    """Cambios del altavoz por segundo desde que se llega al titulo."""
    z=s.z;outs=[];op=s.port_out
    def po(port,v):
        if port&1==0:outs.append(s.frames)
        op(port,v)
    z.port_out=po
    for f in range(50*25):s.frame(())
    z.port_out=op
    per=[0]*25
    for x in outs:per[(x-start)//50]+=1
    return per

def test_musica_titulo_una_vez():
    s=Speccy(tap=TAP,watch=False);m=s.z.m;z=s.z
    for f in range(400):
        s.frame(())
        if m[S['mus_ptr']]|m[S['mus_ptr']+1]:break
    per=title_music(s,s.frames)
    assert sum(per[:3])>500,('la melodia suena al llegar',per)
    assert sum(per[10:])==0,('y despues silencio',per)
    # partida y Game Over: al volver al titulo suena otra vez, una vez
    for f in range(40):s.frame({'SPACE'} if f<6 else ())
    assert m[S['card_ticks']] or m[S['enemy_count']],'empieza la partida'
    m[S['player_take_hit']]=0xc9
    m[S['player_lives']]=0;m[S['shield_invulnerable']]=60
    t0=S['tune_title'];seen=False
    for f in range(3000):
        s.frame({'SPACE'} if seen and f%40<5 else ())
        seen|=m[S['gameover_mode']]==1
        p=m[S['mus_ptr']]|m[S['mus_ptr']+1]<<8
        if seen and t0<=p<t0+8:break
    assert seen and t0<=p<t0+8,'vuelve al titulo con su melodia'
    per2=title_music(s,s.frames)
    assert sum(per2[:3])>500 and sum(per2[10:])==0,per2

def test_golpes():
    s=in_game();z=s.z;m=z.m
    for f in range(100):
        s.frame(())
        if m[S['card_ticks']]==0 and m[S['snd_left']]==0:break
    outs=[];op=s.port_out
    def po(port,v):
        if port&1==0:outs.append(z.t)
        op(port,v)
    z.port_out=po
    t0=z.t
    for f in range(8):s.frame({'SPACE'} if f<2 else ())
    z.port_out=op
    assert outs,'el disparo suena'
    cl=[[outs[0]]]
    for a,b in zip(outs,outs[1:]):
        if b-a>3000:cl.append([b])
        else:cl[-1].append(b)
    spans=[(c[-1]-c[0])/3500 for c in cl]
    assert 2<=len(cl)<=3 and max(spans)<8,('rafagas del disparo (ms)',spans)

if __name__=='__main__':
    for t in (test_disparo,test_formacion_y_fondos,test_atributos_coherentes,test_sonido_mitad_de_tick,test_brillo_insignia,test_musica_titulo_una_vez,test_golpes):
        t();print('PASS',t.__name__,flush=True)
    print('PASS V1.3: 2 balas a 12 px, 10 cuervos / 6 enemigos, cielo sin fondos, atributos coherentes, sonido a mitad de tick, brillo de la insignia, melodia del titulo una vez, golpes de sonido')
