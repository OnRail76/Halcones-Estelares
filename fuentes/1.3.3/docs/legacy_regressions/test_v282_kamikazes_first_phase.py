#!/usr/bin/env python3
"""V2.8.2: run genuine assembled Z80 routines in the repo's headless interpreter.
This is a targeted deterministic regression, not full-speed/audio Fuse validation.
"""
from pathlib import Path
import hashlib
from mini_z80 import VM, SYM

R = Path(__file__).resolve().parents[1]
assert (R / 'assets/HALCONES_ESTELARES_TITLE.scr').read_bytes() == (Path('/mnt/data/HALCONES_V281_CORREGIDO') / 'assets/HALCONES_ESTELARES_TITLE.scr').read_bytes()


def invoke(v, label, maxsteps=50_000):
    return_address = 0x6fb7
    saved_sp = v.sp
    v.push(return_address)
    v.pc = SYM[label]
    v.run_to(lambda w: w.pc == return_address and w.sp == saved_sp, steps=maxsteps)
    assert v.sp == saved_sp, (label, 'stack imbalance')


def setup(cycle, stage=2, frame=8, repeat=0):
    v = VM()
    v.sp=0xfff0
    v.set('wave_stage', stage)
    v.set('wave_repeat', repeat)
    v.set('wave_cycle',cycle)
    v.set('frame_index',frame)
    v.set('ship_x',140)
    slots = SYM['enemy_slots']
    for j in range(6):
        v.m[slots+6*j:slots+6*j+6]=bytes([35+j*18,30,1,0,35+j*18,0])
    bullet = SYM['enemy_bullet_slots']
    v.m[bullet:bullet+9]=bytes(9)
    return v


def shots(v):
    a=SYM['enemy_bullet_slots']
    return sum(v.m[a+3*j+2]!=0 for j in range(3))

# Phase 01, wave 3 / its repeat: only every 16 updates. All later MOAI loops
# keep the original 8-update schedule. Other waves are unaffected.
for repeat in (0,1):
    for frame, expected in ((8,0),(16,1),(24,0),(32,1)):
        v=setup(0,frame=frame,repeat=repeat)
        invoke(v,'enemy_bullet_update')
        assert shots(v)==expected,('first-phase shots',repeat,frame,shots(v),expected)
for cycle in (1,2,6):
    for frame in (8,16,24,32):
        v=setup(cycle,frame=frame)
        invoke(v,'enemy_bullet_update')
        assert shots(v)==1,('later-cycle shots',cycle,frame)
for stage,frame,expected in ((0,32,0),(0,64,1),(1,16,0),(1,32,1)):
    v=setup(0,stage=stage,frame=frame)
    invoke(v,'enemy_bullet_update')
    assert shots(v)==expected,('other-wave shots',stage,frame)
print('PASS actual Z80: phase 01 kamikaze every 16 updates; later kamikaze every 8; crow/hunters unchanged')

# Verify the FIRST phase delays pursuit until Y>=96, while original pursuit
# from Y>=80 returns for all subsequent cycles. Falling speed unchanged.
def one_attacker(cycle, start_y):
    v=setup(cycle,frame=5)
    a=SYM['enemy_slots']
    v.m[a:a+36]=bytes(36)
    v.m[a:a+6]=bytes([70,start_y,1,2,70,0])
    v.set('ship_x',140)
    invoke(v,'wave_update_live')
    return v.m[a],v.m[a+1],v

# New velocity is 3px on cycle 0 and 4px on cycle 1, both exactly as in V2.8.1.
for cycle,y0,expect_steer in ((0,90,False),(0,92,False),(0,93,True),
                                (1,74,False),(1,75,False),(1,76,True),(1,90,True)):
    x,y,v=one_attacker(cycle,y0)
    assert y==y0+3+cycle,('speed changed',cycle,y0,y)
    if expect_steer:
        assert x==71,('did not home at correct Y',cycle,y0,x,y)
    else:
        # For the V2.8.1 sine motion at frame 5, lookup index 10, zero offset.
        expected_x=(70+v.m[SYM['wave_sinus']+10])&255
        assert x==expected_x,('premature homing / changed sine',cycle,y0,x,y,expected_x)
print('PASS actual Z80: first-phase steering Y>=96; later phase Y>=80; dive speeds and sine path intact')

# Zero changes whatsoever to current title, beeper module, and binaries/assets.
BASE=Path('/mnt/data/HALCONES_V281_CORREGIDO')
for folder in ('assets','tools'):
    for p in (R/folder).rglob('*'):
        if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts:
            original=BASE/p.relative_to(R)
            assert original.is_file(),f'Original asset/tool missing: {p}'
            if p.relative_to(R).as_posix() not in ('assets/HUD_NATIVO_NUEVO.png','tools/generate_assets.py'):
                assert p.read_bytes()==original.read_bytes(),f'Unexpected asset/tool change: {p}'
for name in ('src/sound_v19.asm','src/title_screen.asm','src/main.asm','src/phase_interlude_v24.asm'):
    assert (R/name).read_bytes()==(BASE/name).read_bytes(),f'Unrequested change: {name}'
print('PASS all non-smiley assets, title, beeper, IM2, phase and unrelated generators unchanged; smiley exception verified in V284 test')

# Compilation region safety.
blob=(R/'build/starter.bin').read_bytes()
assert 0x8000+len(blob)<0xc000
print('PASS Z80 assembled length=',len(blob),'free before C000=',0x4000-len(blob),'SHA256=',hashlib.sha256(blob).hexdigest())
