"""Launch the real title flow in the headless Z80 VM (no fabricated state)."""
from mini_z80 import SYM

def boot_to_game(v,keep_card=False):
    v.run_to(lambda q:q.pc==SYM['title_wait_release'],steps=1_000_000)
    v.run_to(lambda q:q.pc==SYM['title_wait_press'],steps=10_000)
    v.keys={'SPACE'}
    v.run_to(lambda q:q.pc==SYM['title_wait_start_release'],steps=10_000)
    v.keys=set()
    v.run_to(lambda q:q.pc==SYM['main_loop'],steps=900_000)
    assert v.sp==0xfff0 and v.im==2 and v.ir==0xfe
    if 'card_ticks' in SYM and not keep_card:
        # V1.1: la partida empieza con el cartel OLEADA 1 y la formacion entra al
        # acabarlo. Estas pruebas son de versiones sin cartel: se salta.
        v.set('card_ticks',0);v.set('wave_done',0)
        a=SYM['wave_initial'];v.m[SYM['enemy_slots']:SYM['enemy_slots']+60]=v.m[a:a+60]; v.m[SYM['enemy_count']]=10
        # V1.3: en el juego la formacion entra a mitad de tick y su primera
        # huella siempre se presenta. Aqui se copia antes del tick: se desplaza
        # 8 px la x guardada (el tick la recalcula desde la base) para que la
        # foto anterior no coincida y la primera huella se presente igual.
        e=SYM['enemy_slots']
        for i in range(10):
            x=v.m[e+6*i];v.m[e+6*i]=x+8 if x<160 else x-8
        for i in range(8):v.m[0xf269+i]=0x47
    return v
