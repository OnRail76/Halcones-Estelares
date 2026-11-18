from mini_z80 import VM, SYM
from boot_v15 import boot_to_game
v=boot_to_game(VM())
def irq():
    pc=v.pc;sp=v.sp
    v.push(pc);v.pc=0xfdfd
    v.run_to(lambda q:q.pc==pc and q.sp==sp,steps=1200)
for tick in range(700):
    for _ in range(2):irq()
    v.step()
    v.run_to(lambda q:q.pc in (SYM['main_loop'],SYM['gameover_wait_3_seconds'],SYM['panic_memory']),steps=1200000)
    if tick%30==0 or v.pc!=SYM['main_loop']:
        print('tick',tick,'pc',hex(v.pc),'lives',v.val('player_lives'),'kills',v.val('kills'),'phase',v.val('wave_stage'),'inv',v.val('shield_invulnerable'),'sp',hex(v.sp),flush=True)
    if v.pc!=SYM['main_loop']:
        print('STOP',tick,hex(v.pc),'timer',v.val('gameover_timer'),'k',v.val('kills'))
        break
else:print('NO GAME OVER after 700 ticks')
