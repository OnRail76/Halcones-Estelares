#!/usr/bin/env python3
"""V16 test: the ULA must not see the temporary white unpaint states.

Exact Z80 bytes executed by the project VM; does not model real ULA timing.
"""
from boot_v15 import boot_to_game
from mini_z80 import VM, SYM
v=boot_to_game(VM())
checks=0
for tick in range(180):
    live_before=bytes(v.m[0x5800:0x5b00])
    # Force movement plus firing and a variety of wave overlap combinations.
    v.keys=({'SPACE'} if tick%7==1 else set()) | ({'O'} if tick%48<12 else {'P'} if tick%48<24 else {'Q'} if tick%48<36 else {'A'})
    v.step()
    v.run_to(lambda q:q.pc==SYM['color_shadow_present'],steps=900000)
    # The visible display must still contain last completed frame's palette.
    assert bytes(v.m[0x5800:0x5b00])==live_before, f'visible attrs modified BEFORE final color commit at tick {tick}'
    assert v.m[0xf400]==0x3c, f'attr shadow ran past upper boundary at tick {tick}'
    # While committed palette is still old, the shadow already contains NEW colors.
    v.run_to(lambda q:q.pc==SYM['main_loop'],steps=200000)
    assert v.m[0x5800:0x5b00]==v.m[0xf100:0xf400], f'attr shadow not committed at tick {tick}'
    assert v.m[0xf400]==0x3c
    checks+=1
print(f'PASS: {checks} frames keep full previous palette while drawing, then commit full new color palette.')
print('PASS: color shadow private buffer $F100-$F3FF never overran sentinel $F400')
