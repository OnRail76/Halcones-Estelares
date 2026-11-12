#!/usr/bin/env python3
"""Regression for GAME OVER: V2.4 phase interlude must not change its 3s rule."""
from mini_z80 import VM,SYM
from boot_v15 import boot_to_game
v=boot_to_game(VM())
v.set('player_lives',0)
v.set('shield_invulnerable',0)
v.keys={'SPACE'}
v.run_to(lambda q:q.pc==SYM['gameover_wait_3_seconds'],steps=1500000)
assert v.val('gameover_timer')==150 and v.val('gameover_mode')==1
assert v.m[0x5aab]==0x40
for i in range(150):
    pc,sp=v.pc,v.sp
    v.push(pc);v.pc=0xfdfd
    v.run_to(lambda q:q.pc==pc and q.sp==sp,steps=1500)
    if i==148:assert v.val('gameover_timer')==1 and v.m[0x5aab]==0x40
assert v.val('gameover_timer')==0
v.run_to(lambda q:q.pc==SYM['gameover_wait_release'],steps=7000)
assert v.m[0x5aab]==0x44
for i in range(40):
    v.step()
    assert v.pc!=SYM['title_session_start']
v.keys=set()
v.run_to(lambda q:q.pc==SYM['gameover_wait_press'],steps=500)
v.keys={'SPACE'}
v.run_to(lambda q:q.pc==SYM['title_session_start'],steps=500)
print('PASS V2.4 GAME OVER: 150 real IM2 IRQs, SPACE held does not skip, release/press returns to title')
