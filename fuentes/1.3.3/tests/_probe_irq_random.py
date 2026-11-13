from mini_z80 import VM,SYM
from boot_v15 import boot_to_game
import random
orstep=VM.step

def run_trial(seed, interval):
    v=boot_to_game(VM())
    v.set('kills',0);v.set('player_lives',0);v.set('shield_invulnerable',0)
    v.keys=set()
    original_starter=bytes(v.m[0x8000:0x8000+15683])
    original_extra=bytes(v.m[0xf401:0xf401+2539])
    rng=random.Random(seed)
    nextirq=v.steps+rng.randint(1,interval)
    in_irq=False
    ie=True
    count=0
    def step():
        nonlocal nextirq,in_irq,ie,count
        current_pc=v.pc
        op=v.m[current_pc]
        orstep(v)
        if op==0xf3:ie=False
        if op==0xfb:ie=True
        if not in_irq and ie and v.steps>=nextirq:
            savepc=v.pc;savesp=v.sp
            save_regs=tuple(v.r);save_f=v.f;save_ix=v.ix;save_iy=v.iy
            in_irq=True
            v.push(savepc)
            v.pc=0xfdfd
            v.run_to(lambda m:m.pc==savepc and m.sp==savesp,steps=1500)
            in_irq=False
            assert tuple(v.r)==save_regs and v.f==save_f and v.ix==save_ix and v.iy==save_iy,(seed,hex(savepc),'irq register corruption')
            nextirq=v.steps+rng.randint(interval//2,interval*2)
            count+=1
    v.step=step
    v.run_to(lambda m:m.pc==SYM['gameover_wait_3_seconds'] or m.pc==SYM['panic_memory'],steps=500000)
    assert v.pc==SYM['gameover_wait_3_seconds'],(seed,hex(v.pc))
    assert v.sp==0xfff0,(seed,'SP',hex(v.sp))
    assert v.val('gameover_timer') in (149,150),(seed,'timer',v.val('gameover_timer'))

    changes=[(hex(i+0x8000),original_starter[i],v.m[i+0x8000]) for i in range(len(original_starter)) if original_starter[i]!=v.m[i+0x8000]]
    if seed==0:print('CODE MUTATIONS',len(changes),changes[:80])
    assert v.m[0xf401:0xf401+len(original_extra)]==original_extra,(seed,'extra overwritten')
    assert v.m[0xf000]==0xa5 and v.m[0xf400]==0x3c,(seed,'guard')
    return seed,count,v.steps
for i in range(80):
    row=run_trial(i,150+(i%4)*100)
    if i%20==0:print('Trial',row,flush=True)
print('PASS gameover zero score with async 50Hz mid-routine IRQ, 80 seeds')
