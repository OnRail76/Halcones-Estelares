"""V2.8.9: no hostile-state updates after last loss, but original 50Hz death/gameover timers and score survive.
Z80 partial interpreter; NOT an emulator-complete validation.
"""
from mini_z80 import VM, SYM
from boot_v15 import boot_to_game


def irq(v):
    pc,sp=v.pc,v.sp
    regs=tuple(v.r);f=v.f;ix=v.ix;iy=v.iy
    v.push(pc);v.pc=0xfdfd
    v.run_to(lambda q:q.pc==pc and q.sp==sp,steps=1200)
    assert v.sp==sp and tuple(v.r)==regs and v.f==f and v.ix==ix and v.iy==iy

def tick(v):
    assert v.pc==SYM['main_loop']
    v.step()
    v.run_to(lambda q:q.pc in (SYM['main_loop'],SYM['gameover_wait_3_seconds'],SYM['panic_memory']),steps=1000000)
    assert v.pc!=SYM['panic_memory']

for kills in (0,1):
    v=boot_to_game(VM())
    v.set('kills',kills)
    v.set('player_lives',0)
    v.set('shield_invulnerable',150)
    v.set('player_respawn_pending',1)
    es=SYM['enemy_slots'];bs=SYM['enemy_bullet_slots'];ps=SYM['bullet_slots']
    before=bytes(v.m[es:es+36])+bytes(v.m[bs:bs+9])+bytes(v.m[ps:ps+27])
    for n in range(56):
        if n:irq(v);irq(v)
        tick(v)
        if v.pc==SYM['gameover_wait_3_seconds']:break
        after=bytes(v.m[es:es+36])+bytes(v.m[bs:bs+9])+bytes(v.m[ps:ps+27])
        assert after==before,('AI advanced while dead',n,kills)
        assert v.sp==0xfff0
    assert v.pc==SYM['gameover_wait_3_seconds'],('never reached gameover',kills,v.pc)
    assert v.val('gameover_timer')==150 and v.val('kills')==kills
    for _ in range(150):irq(v)
    assert v.val('gameover_timer')==0
    v.run_to(lambda q:q.pc==SYM['gameover_wait_release'],steps=10000)
    v.keys=set();v.run_to(lambda q:q.pc==SYM['gameover_wait_press'],steps=2000)
    v.keys={'SPACE'};v.run_to(lambda q:q.pc==SYM['title_session_start'],steps=1000)
    assert v.sp==0xfff0
    print('PASS kill score',kills*10,'=> GAME OVER => title, preserved hostile state, original timers and stack')
