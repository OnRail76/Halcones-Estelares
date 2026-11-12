from mini_z80 import VM, SYM
from boot_v15 import boot_to_game
v=boot_to_game(VM())
print('INIT', v.steps,hex(v.pc),hex(v.sp),'kills',v.val('kills'),'lives',v.val('player_lives'))
def irq():
    pc=v.pc;sp=v.sp;regs=tuple(v.r);f=v.f
    v.push(pc);v.pc=0xfdfd
    v.run_to(lambda q:q.pc==pc and q.sp==sp,steps=1200)
    assert tuple(v.r)==regs and v.f==f,(v.r,regs)
def tick():
    assert v.pc==SYM['main_loop'],hex(v.pc)
    v.step()
    v.run_to(lambda q:q.pc==SYM['main_loop'] or q.pc==SYM['gameover_wait_3_seconds'] or q.pc==SYM['panic_memory'],steps=1000000)
    assert v.pc!=SYM['panic_memory'],('panic',v.steps)
    return v.pc
for n in (2,1,0):
    bullets=SYM['enemy_bullet_slots']
    v.m[bullets:bullets+9]=bytes(9)
    v.m[bullets:bullets+3]=bytes((v.val('ship_x')+8,149,1))
    assert tick()==SYM['main_loop']
    print('LOSS',n,'actual lives',v.val('player_lives'),'inv',v.val('shield_invulnerable'),'kills',v.val('kills'),'steps',v.steps)
    assert v.val('player_lives')==n
    for _ in range(101 if n==0 else 150):irq()
    print('IRQ',n,'inv',v.val('shield_invulnerable'),'steps',v.steps)
    if n==0:
        assert tick()==SYM['gameover_wait_3_seconds']
    else:
        assert tick()==SYM['main_loop']
        assert v.val('kills')==0
print('GAME OVER reached',v.steps,hex(v.pc),'SP',hex(v.sp),'score',v.val('kills'))
assert v.sp==0xfff0
assert v.val('gameover_mode')==1 and v.val('gameover_timer')==150
for i in range(150):irq()
assert v.val('gameover_timer')==0
v.run_to(lambda q:q.pc==SYM['gameover_wait_release'],steps=10000)
v.keys=set();v.run_to(lambda q:q.pc==SYM['gameover_wait_press'],steps=2000)
v.keys={'SPACE'};v.run_to(lambda q:q.pc==SYM['title_session_start'],steps=2000)
print('RETURN TITLE',hex(v.pc),hex(v.sp),'steps',v.steps)
