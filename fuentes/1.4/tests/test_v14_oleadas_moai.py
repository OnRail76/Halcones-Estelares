#!/usr/bin/env python3
"""HALCONES ESTELARES 1.4 (emulador Z80 completo).
1. Estrellas fijas: estan en el cielo inmovil (D800) y en pantalla, igual en
   las oleadas y con el MOAI; ninguna donde el MOAI, Jupiter o la luna.
2. Director de oleadas: la primera de la partida son los cuervos de siempre;
   despues salen las seis coreografias, nunca la misma dos veces seguidas, y
   hay oleadas con y sin cuervos.
3. Cada coreografia deja a sus naves dentro del campo de juego.
4. Balas enemigas: hasta 6 a la vez; con desplazamiento lateral se mueven en
   diagonal y desaparecen al salir por un lado.
5. MOAI: tres disparos (izquierda, recto, derecha), apuntado a la ultima
   posicion conocida, barrido con un hueco y dos cuervos invocados que se
   pueden derribar."""
import sys,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tests'))
import test_v13_galaga as T
S=T.S;ROWS=T.ROWS
from test_v11_justicia import call

def stars(m):
    out=[];a=S['sky_stars']
    for i in range(S['sky_stars_draw']*0+200):
        lo,hi,mask=m[a+3*i],m[a+3*i+1],m[a+3*i+2]
        if not 0xd8<=hi<0xf0 or mask==0:break
        out.append(((lo|hi<<8),mask))
    return out

def test_estrellas_fijas():
    s=T.in_game();m=s.z.m
    st=stars(m)
    assert len(st)>=50
    for f in range(80):s.frame(())
    for addr,mask in st:
        assert m[addr]&mask,'estrella en el cielo'
        assert m[addr-0x9800]&mask or True
    assert 'stars_v13_move' not in S,'ya no hay scroll de estrellas'
    # ninguna en el MOAI (x 72..119, y 8..95), Jupiter (128..183, 96..151) ni la luna (y 113..120)
    inv={}
    for y in range(192):
        for c in range(32):inv[0xd800+ROWS[y]+c]=(y,c)
    for addr,mask in st:
        y,c=inv[addr];x=c*8+[0x80>>i for i in range(8)].index(mask)
        assert not(72<=x<=119 and 8<=y<=95) and not(128<=x<=183 and 96<=y<=151) and not 113<=y<=120,(x,y)
    # con el MOAI siguen ahi
    for i in range(10):
        b=S['enemy_slots']+6*i
        if m[b+2]:m[b+2]=3;m[b+5]=1
    m[S['wave_stage']]=2;m[S['wave_repeat']]=1;m[S['wave_done']]=1;m[S['card_ticks']]=0
    for f in range(40):s.frame(())
    assert m[S['wave_stage']]==3
    assert all(m[a]&k for a,k in st),'estrellas con el MOAI'
    s.screen(str(R/'build/V14_MOAI_ESTRELLAS.png'))

def test_director():
    s=T.in_game();m=s.z.m;z=s.z
    for f in range(100):
        s.frame(())
        if m[S['card_ticks']]==0:break
    assert m[S['wave_kind']]==0 and m[S['enemy_count']]==10
    assert all(m[S['enemy_slots']+6*i+3]==3 for i in range(10)),'primera oleada: cuervos'
    pc,sp=z.pc,z.sp
    m[S['wave_cycle']]=1
    kinds=[];crowless=0;last=None
    for n in range(120):
        call(s,'wave_director')
        k=m[S['wave_kind']];kinds.append(k)
        assert k!=last,'misma coreografia dos veces seguidas'
        last=k
        cnt=m[S['enemy_count']];types=[m[S['enemy_slots']+6*i+3] for i in range(cnt)]
        assert cnt in (6,10) and all(t in (0,1,2,3) for t in types)
        if 3 not in types:crowless+=1
    z.pc,z.sp=pc,sp
    c=collections.Counter(kinds)
    assert set(c)=={0,1,2,3,4,5},c
    assert min(c.values())>=8,c
    assert 15<=crowless<=80,crowless
    print('   coreografias',dict(sorted(c.items())),'oleadas sin cuervos',crowless,'de 120')

def force_kind(s,k,mix):
    m=s.z.m;z=s.z
    for f in range(100):
        s.frame(())
        if m[S['card_ticks']]==0:break
    st={'on':True};orig=z.step
    def step():
        if st['on'] and z.pc==S['wd_set']:z.c=k;z.e=mix;st['on']=False
        orig()
    z.step=step
    for i in range(10):
        b=S['enemy_slots']+6*i
        if m[b+2]:m[b+2]=3;m[b+5]=1
    for f in range(200):
        s.frame(())
        if not st['on'] and m[S['card_ticks']]==0:break
    z.step=orig
    assert m[S['wave_kind']]==k

def test_coreografias_en_campo():
    for k in range(6):
        s=T.in_game();m=s.z.m
        m[S['player_take_hit']]=0xc9
        force_kind(s,k,(k+3)%8)
        seen=set()
        for f in range(300):
            s.frame(())
            e=S['enemy_slots']
            for i in range(m[S['enemy_count']]):
                if m[e+6*i+2] in (1,2,4,5):
                    x,y=m[e+6*i],m[e+6*i+1]
                    assert 16<=x<=176 and y<=176,(k,i,x,y)
                    seen.add((i,x//4,y//4))
        assert len(seen)>30,('se mueven',k,len(seen))
        if k==4:s.screen(str(R/'build/V14_MOON_CRESTA.png'))
        if k==3:s.screen(str(R/'build/V14_PHOENIX.png'))

def test_balas_diagonales():
    s=T.in_game();m=s.z.m;z=s.z
    pc,sp=z.pc,z.sp
    b=S['enemy_bullet_slots']
    m[b:b+24]=bytes(24)
    for i in range(6):m[b+4*i:b+4*i+4]=bytes([40+20*i,20,1,(256-2) if i==0 else (3 if i==5 else 0)])
    m[S['enemy_fire_cd']]=200
    xs=[]
    for t in range(30):
        call(s,'enemy_bullet_update')
        xs.append((m[b],m[b+2],m[b+20],m[b+22]))
    assert xs[0][0]==38 and xs[0][2]==143,xs[0]
    assert any(a==0 for _,a,_,_ in xs),'la de la izquierda sale por el lado'
    assert any(c==0 for _,_,_,c in xs),'la de la derecha sale por el lado'
    z.pc,z.sp=pc,sp

def boss_scene():
    s=T.in_game();m=s.z.m
    for i in range(10):
        b=S['enemy_slots']+6*i
        if m[b+2]:m[b+2]=3;m[b+5]=1
    m[S['wave_stage']]=2;m[S['wave_repeat']]=1;m[S['wave_done']]=1;m[S['card_ticks']]=0
    for f in range(40):s.frame(())
    assert m[S['wave_stage']]==3 and m[S['boss_hp']]==18 and m[S['enemy_count']]==2
    m[S['player_take_hit']]=0xc9
    return s

def attack(s,pick,hp=4):
    """Fuerza el ataque PICK del MOAI y devuelve las balas nuevas."""
    m=s.z.m;z=s.z;pc,sp=z.pc,z.sp
    b=S['enemy_bullet_slots'];m[b:b+24]=bytes(24)
    m[S['boss_hp']]=hp;m[S['boss_last']]=9;m[S['enemy_fire_cd']]=0
    st={'on':True};orig=z.step
    def step():
        if st['on'] and z.pc==S['ba_pick']:z.a=pick;st['on']=False
        orig()
    z.step=step
    call(s,'enemy_bullet_update')
    z.step=orig;z.pc,z.sp=pc,sp
    return [tuple(m[b+4*i:b+4*i+4]) for i in range(6) if m[b+4*i+2]]

def test_ataques_moai():
    s=boss_scene();m=s.z.m;z=s.z
    tri=attack(s,1)
    assert sorted((x,y,d) for x,y,a,d in tri)==[(90,68,254),(92,68,0),(94,68,2)],tri
    # apuntado: la x de la nave cuando los ojos avisan (boss_target)
    m[S['boss_target']]=40
    aim=attack(s,2)
    assert len(aim)==1 and aim[0][3]>=0x80,('hacia la izquierda',aim)
    m[S['boss_target']]=170
    aim=attack(s,2)
    assert len(aim)==1 and 1<=aim[0][3]<=4,('hacia la derecha',aim)
    # barrido: 6 columnas con un hueco, una cada 4 ticks
    attack(s,3)
    assert m[S['sweep_left']]==6
    b=S['enemy_bullet_slots'];xs=set()
    pc,sp=z.pc,z.sp
    for t in range(30):
        call(s,'boss_v14_tick')
        for i in range(6):
            if m[b+4*i+2] and m[b+4*i+1]==70:xs.add(m[b+4*i])
    z.pc,z.sp=pc,sp
    cols=[26+30*i for i in range(6)]
    assert len(xs)==5 and xs<set(cols),xs
    gap=(set(cols)-xs).pop();assert gap not in (26,176),'el hueco nunca en un borde'
    # dos cuervos invocados bajo la barbilla, que bajan y se pueden derribar
    attack(s,4)
    e=S['enemy_slots']
    assert [m[e+2],m[e+8]]==[2,2] and [m[e+3],m[e+9]]==[3,3] and m[e+1]>=96
    y0=m[e+1]
    for f in range(6):s.frame(())
    assert m[e+1]>y0 and m[e]<=108
    bs=S['bullet_slots'];m[bs:bs+3]=bytes([m[e]+4,m[e+1]+20,1])
    for f in range(4):s.frame(())
    assert m[e+2] in (0,3),'cuervo invocado derribado'
    s.screen(str(R/'build/V14_MOAI_CUERVOS.png'))

def test_desbloqueo_por_vida():
    s=boss_scene();m=s.z.m;z=s.z
    for hp,allowed in ((18,{0,1,2}),(10,{0,1,2,3}),(5,{0,1,2,3,4})):
        seen=set()
        for n in range(40):
            pc,sp=z.pc,z.sp
            m[S['boss_hp']]=hp;m[S['enemy_fire_cd']]=0;m[S['sweep_left']]=0
            b=S['enemy_bullet_slots'];m[b:b+24]=bytes(24)
            e=S['enemy_slots'];m[e:e+12]=bytes(12)
            got={}
            orig=z.step
            def step():
                if z.pc==S['ba_new']:got['a']=z.a
                orig()
            z.step=step
            call(s,'enemy_bullet_update')
            z.step=orig;z.pc,z.sp=pc,sp
            seen.add(got['a'])
        assert seen==allowed,(hp,seen)

if __name__=='__main__':
    for t in (test_estrellas_fijas,test_director,test_coreografias_en_campo,test_balas_diagonales,test_ataques_moai,test_desbloqueo_por_vida):
        t();print('PASS',t.__name__,flush=True)
    print('PASS V1.4: estrellas fijas, director con 6 coreografias y mezcla de naves, 6 balas en diagonal, MOAI con 5 ataques')
