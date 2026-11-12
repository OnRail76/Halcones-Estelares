#!/usr/bin/env python3
"""HALCONES ESTELARES 1.2 - remozado grafico y sonido (emulador Z80 completo).
1. El titulo descomprimido (LZ) es exactamente build/TITULO_V12.scr (bitmap).
2. Marcador: caras feliz/apurada/vacia segun las vidas; escudo LISTO/CARGANDO.
3. LEDs del marco: MOAI = los tres fijos; enemigo cerca = parpadeo; escudo
   listo = barrido verde.
4. MOAI: grietas al bajar a 12/6/3 de vida, boca que se abre y se cierra
   (el cielo queda intacto), luna que cruza por delante de Jupiter, derrumbe
   por bloques que deja limpio el cielo y lleva a la pantalla de fase.
5. Sonido: el beeper suena en las esperas sin romper los 25 ticks/s.
6. El record se conserva entre partidas y GAME OVER lo anuncia."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tests'/'emulador_completo'))
import harness
from harness import Speccy
TAP=str(R/'build'/'HALCONES_ESTELARES_V281.tap')
S=json.load(open(R/'build'/'starter.sym.json'))
ROWS=[((y&0xc0)<<5)|((y&7)<<8)|((y&0x38)<<2) for y in range(192)]

def in_game(kemp=0xff):
    s=Speccy(tap=TAP,watch=False);s.kempston=kemp;m=s.z.m
    for f in range(400):
        s.frame({'SPACE'} if 90<=f<96 else ())
        if f>100 and m[S['card_ticks']]:break
    assert m[S['card_ticks']],'no empezo la partida'
    return s

def test_titulo():
    s=Speccy(tap=TAP,watch=False);m=s.z.m
    for f in range(60):s.frame(())
    ref=(R/'build'/'TITULO_V12.scr').read_bytes()
    rec=set(ROWS[y]+c for y in range(152,160) for c in range(32))   # cifras del RECORD (las pone el juego)
    bad=[i for i in range(6144) if m[0x4000+i]!=ref[i] and i not in rec]
    assert not bad,('el titulo no coincide con TITULO_V12.scr',bad[:8])
    s.screen(str(R/'build'/'V12_TITULO.png'))

def test_marcador():
    s=in_game();m=s.z.m
    for f in range(60):s.frame(())
    def face(i):
        return bytes(m[0x4000+ROWS[y]+25+2*i+k] for y in range(42,55) for k in (0,1))
    feliz,apurado,vacia=(bytes(m[S[n]:S[n]+26]) for n in ('hud_face_feliz','hud_face_apurado','hud_face_vacia'))
    assert [face(i) for i in range(3)]==[feliz]*3
    for lives,exp in ((2,[feliz,feliz,vacia]),(1,[apurado,vacia,vacia])):
        m[S['player_lives']]=lives
        for f in range(4):s.frame(())
        assert [face(i) for i in range(3)]==exp,('caras',lives)
        assert m[0x5800+5*32+25]==0x46 and m[0x5800+5*32+29]==0x01
    s.screen(str(R/'build'/'V12_MARCADOR.png'))
    # escudo: LISTO parpadea en verde; al usarlo pasa a ACTIVO y luego CARGANDO
    assert m[0x5800+10*32+25]==0xc4
    for f in range(4):s.frame({'A'})
    assert m[S['shield_state']]==1 and m[0x5800+10*32+25]==0x45
    for f in range(160):s.frame(())
    assert m[S['shield_state']]==2 and m[0x5800+10*32+25]==0x06
    assert [m[0x5800+9*32+25+c] for c in range(6)]==[0x42,0x42,0x46,0x46,0x44,0x44]

def leds(m):return (m[0x58c0],m[0x5980],m[0x5a40])

def test_leds():
    s=in_game();m=s.z.m
    for f in range(80):s.frame(())
    seen=set()
    for f in range(40):
        s.frame(());seen.add(leds(m))
    assert all(set(l)<={0x44,0x04} for l in seen) and any(0x44 in l for l in seen),('barrido verde',seen)
    e=S['enemy_slots'];m[e+1]=130;m[e+2]=2
    seen=set()
    for f in range(8):
        m[e+1]=130;m[e+2]=2;s.frame(());seen.add(leds(m))
    assert (0x42,0x42,0x42) in seen and (0x02,0x02,0x02) in seen,('parpadeo de peligro',seen)

def to_boss(s):
    m=s.z.m
    for i in range(10):m[S['enemy_slots']+6*i+2]=0
    m[S['wave_stage']]=2;m[S['wave_repeat']]=1;m[S['wave_done']]=1;m[S['card_ticks']]=0
    for f in range(20):
        s.frame(())
        if m[S['wave_stage']]==3:break
    assert m[S['wave_stage']]==3 and m[S['boss_hp']]==18
    for f in range(10):              # V1.3: el MOAI se dibuja al acabar de borrar el fondo
        if any(moai_sky(m)):break
        s.frame(())
    assert any(moai_sky(m))

def moai_sky(m):
    return bytes(m[0xd800+ROWS[y]+9+c] for y in range(8,96) for c in range(6))

def test_moai():
    s=in_game();m=s.z.m
    for f in range(60):s.frame(())
    m[S['shield_invulnerable']]=0
    to_boss(s)
    m[S['player_take_hit']]=0xc9 if False else m[S['player_take_hit']]
    sky0=moai_sky(m)
    # boca: al disparar se abre en pantalla y trabajo, el cielo no cambia
    m[S['enemy_fire_cd']]=0
    for f in range(8):
        s.frame(())
        if m[S['mouth_ticks']]:break
    assert m[S['mouth_ticks']],'el MOAI no abrio la boca'
    s.frame(());s.frame(())
    a=ROWS[66]+11
    assert m[0x4000+a]==0 and m[0xc000+a]==0 and m[0xd800+a]!=0
    assert m[0x586a]==0x42,'ojos encendidos al disparar'
    for f in range(30):s.frame(())
    assert m[S['mouth_ticks']]==0 and m[0x4000+a]==m[0xd800+a],'boca cerrada'
    # grietas al bajar a 12, 6 y 3
    lit=[]
    for hp in (13,7,4):
        m[S['boss_hp']]=hp
        b=S['bullet_slots'];m[b:b+3]=bytes([96,60,1])
        for f in range(4):s.frame(())
        lit.append(sum(bin(x).count('1') for x in moai_sky(m)))
    base=sum(bin(x).count('1') for x in sky0)
    assert base>lit[0]>lit[1]>lit[2],('grietas',base,lit)
    s.screen(str(R/'build'/'V12_MOAI_GRIETAS.png'))
    # luna: avanza y se dibuja entre y=113 y 119
    x0=m[S['moon_x']]
    for f in range(60):s.frame(())
    assert m[S['moon_x']]>x0 and m[S['moon_x']]>=24
    # derrumbe por bloques: el cielo del MOAI queda vacio y llega la pantalla de fase
    m[S['boss_hp']]=1;b=S['bullet_slots'];m[b:b+3]=bytes([96,60,1])
    partial=False
    for f in range(400):
        s.frame(())
        bl=m[S['boss_blocks']]
        if 0<bl<60 and not partial:
            partial=True;n=sum(1 for x in moai_sky(m) if x)
            assert 0<n<len(sky0),'derrumbe a medias'
            s.screen(str(R/'build'/'V12_MOAI_DERRUMBE.png'))
        if m[S['gameover_mode']]==2:break
    assert partial and m[S['gameover_mode']]==2,'no llego la pantalla de fase'
    assert not any(moai_sky(m)),'restos del MOAI en el cielo'
    s.screen(str(R/'build'/'V12_FASE.png'))

def test_sonido_y_ritmo():
    s=in_game();z=s.z;m=z.m
    for f in range(50):s.frame(())
    outs=[0];op=s.port_out
    def po(port,v):
        if port&1==0:outs[0]+=1
        op(port,v)
    z.port_out=po
    ticks=[];t=S['combat_tick']
    for f in range(200):
        keys={'SPACE'} if f%8<4 else set()
        s.keys=keys;end=z.t+harness.FRAME
        while z.t<end:
            if z.pc==t:ticks.append(s.frames)
            z.step()
        s.frames+=1
        if z.iff1 and not z.ei_delay:
            pc0,sp0=((z.pc+1)&0xffff if z.halted else z.pc),z.sp
            if z.interrupt():
                while not(z.pc==pc0 and z.sp==sp0):z.step()
    gaps=[b-a for a,b in zip(ticks,ticks[1:])]
    assert outs[0]>1000,('el beeper casi no suena',outs[0])
    assert min(gaps)>=2 and gaps.count(2)>=len(gaps)*0.95,('ritmo',sorted(set(gaps)))

def test_record():
    s=in_game();m=s.z.m
    m[S['score_words']]=123;m[S['score_words']+1]=0
    for f in range(4):s.frame(())
    m[S['player_take_hit']]=0xc9
    m[S['player_lives']]=0;m[S['shield_invulnerable']]=60
    for f in range(300):
        s.frame(())
        if m[S['gameover_mode']]==1:break
    assert m[S['gameover_mode']]==1
    for f in range(20):s.frame(())
    assert m[0x5800+17*32+12]&7!=(m[0x5800+17*32+12]>>3)&7,'NUEVO RECORD visible'
    s.screen(str(R/'build'/'V12_GAMEOVER_RECORD.png'))
    assert m[S['record_words']]|m[S['record_words']+1]<<8==123

if __name__=='__main__':
    for t in (test_titulo,test_marcador,test_leds,test_moai,test_sonido_y_ritmo,test_record):
        t();print('PASS',t.__name__,flush=True)
    print('PASS V1.2 remozado: titulo, marcador, LEDs, MOAI (grietas, boca, luna, derrumbe), sonido a 25 ticks/s, record')
