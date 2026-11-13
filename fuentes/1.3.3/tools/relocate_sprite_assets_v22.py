"""Move ONLY immutable pre-shifted sprite bytes to safe low RAM for V2.2.
Pointer tables and wave tables remain in assembled $8000 code.
This preserves all previous real Z80 render functions and sprite bitmaps.
"""
from pathlib import Path
import re, json, math
R=Path(__file__).resolve().parents[1]
src=(R/'build/combat_assets.asm').read_text()
head,tail=src.split('player_phase_ptrs:',1)
low_base=0x6000
blob=bytearray();mapping={}
for line in head.splitlines():
    t=line.split(';',1)[0].strip()
    if not t:continue
    if t.endswith(':'):
        key=t[:-1]
        assert key not in mapping,key
        mapping[key]=low_base+len(blob)
    elif t.startswith('db '):
        blob+=bytes(int(x.strip()) for x in t[3:].split(','))
    else:raise ValueError(t)
assert all(k in mapping for k in ['player_shifted','enemy_needle_shifted','enemy_blade_shifted','enemy_drone_shifted','shot_shifted','explosion_shifted'])
for key,val in mapping.items():
    tail=re.sub(r'\b'+re.escape(key)+r'\b',str(val),tail)
# independent 8×8 Crow shape (same chosen ALADO geometry; two black eyes on red body).
# The sprite width is 8 px; all eight horizontal shifts are precomputed to 2 bytes × 8 scanlines.
crowA=['10000001','11000011','11100111','11111111','01011010','00111100','01011010','10000001']
crowB=['01000010','11100111','11111111','11111111','01011010','00111100','10011001','00100100']
# Both eyes are symmetric punched holes at row 4, x2 and x5.
assert all(s[2]=='0' and s[5]=='0' for s in (crowA[4],crowB[4]))
crow_offset=len(blob)
for frame in (crowA,crowB):
    for phase in range(8):
        for row in frame:
            for byte in range(2):
                val=0
                for bit in range(8):
                    srcx=byte*8+bit-phase
                    if 0<=srcx<8 and row[srcx]=='1': val|=128>>bit
                blob.append(val)
mapping['crow_shifted']=low_base+crow_offset
# Add a real three-frame 24×24 explosion for the ESF-01 (not two dots).
# Pre-shift into 4 bytes × 24 rows × 8 phases × 3 frames.
blast=[]
for frame_id in range(3):
    fr=[]
    for yy in range(24):
        row=[]
        for xx in range(24):
            dx=xx-11.5;dy=yy-11.5
            r=math.hypot(dx,dy)
            arm=(abs(dx)<1.4 or abs(dy)<1.4 or abs(abs(dx)-abs(dy))<1.1)
            if frame_id==0:
                bit=(r<4.6) or (arm and r<10.4) or (7<r<10 and ((xx*7+yy*5)%13<2))
            elif frame_id==1:
                bit=(7.6<r<10.5 and ((xx*3+yy*7)%5!=0)) or (arm and 10<r<13.5) or (r<2.2)
            else:
                bit=(7.8<r<13 and ((xx*7+yy*11)%19<4)) or ((abs(dx)<1 and 3<abs(dy)<6))
            row.append(int(bit))
        fr.append(row)
    assert sum(map(sum,fr))>45
    blast.append(fr)
blast_offset=len(blob)
for fr in blast:
    for phase in range(8):
        for row in fr:
            for byte in range(4):
                val=0
                for bit in range(8):
                    srcx=byte*8+bit-phase
                    if 0<=srcx<24 and row[srcx]:val|=128>>bit
                blob.append(val)
mapping['ship_blast_shifted']=low_base+blast_offset
# V2.3: approved true 32x32 windshield shield, with NO horizontal stripe.
# Keep these immutable art bytes in low RAM with the other pre-shifted sprites.
from PIL import Image
shield_img=Image.open(R/'assets/ESCUDO_PARABRISAS_V23_APROBADO.png').convert('RGB')
assert shield_img.size==(32,32)
shield_bits=[[int(shield_img.getpixel((x,y))[1]>180) for x in range(32)] for y in range(32)]
assert sum(map(sum,shield_bits))>=65
shield_offset=len(blob)
for phase in range(8):
    for row in shield_bits:
        for byte in range(5):
            val=0
            for bit in range(8):
                sx=byte*8+bit-phase
                if 0<=sx<32 and row[sx]: val|=128>>bit
            blob.append(val)
mapping['shield_windshield_shifted']=low_base+shield_offset
# Relocate the 384 immutable frame bitmap bytes into unused safe CODE data RAM.
# Frame attributes stay in main code. This does not modify the displayed frame.
frame_manifest=json.loads((R/'build/frame_manifest_v17.json').read_text())
assert len(frame_manifest['bitmap'])==384
assert len(blob)==7104, f'Unexpected sprite map length {len(blob)}; recheck $7BC0 frame pointer'
frame_low_address=low_base+len(blob)
assert frame_low_address==0x7bc0
blob.extend(frame_manifest['bitmap'])
mapping['frame_bitmap_relocated']=frame_low_address
# V2.8.1: exact native attribute bytes from V2.7 original logo rows 1..7.
# $7D40..$7DFF, read-only source for the attract-mode white sweep.
logo_scr=(R/'assets/HALCONES_ESTELARES_TITLE.scr').read_bytes()
assert len(logo_scr)==6912
logo_attr_origin=low_base+len(blob)
assert logo_attr_origin==0x7d40
blob.extend(logo_scr[6144+32:6144+8*32])
mapping['title_attr_restore']=logo_attr_origin

assert low_base+len(blob)<0x8000,(hex(low_base+len(blob)),len(blob))
(R/'build/sprites_reloc_v22.bin').write_bytes(blob)
refs=['; V2.8.1 sprite pixel masks in $6000 CODE block; all pointer addresses remain absolute.','player_phase_ptrs:'+tail]
refs.append('crow_phase_ptrs:')
for phase in range(8):refs.append(f' dw {mapping["crow_shifted"]}+{phase*16}')
refs.append('crow_phase_ptrs_f1:')
for phase in range(8):refs.append(f' dw {mapping["crow_shifted"]}+{(phase+8)*16}')
for frame_id in range(3):
    refs.append(f'ship_blast_phase_ptrs_f{frame_id}:')
    for phase in range(8):
        refs.append(f' dw {mapping["ship_blast_shifted"]}+{frame_id*768+phase*96}')
refs.append('shield_phase_ptrs:')
for phase in range(8):
    refs.append(f' dw {mapping["shield_windshield_shifted"]}+{phase*160}')
(R/'build/combat_assets_v22.asm').write_text('\n'.join(refs)+'\n')
(R/'build/sprites_reloc_v22_map.json').write_text(json.dumps({'origin':low_base,'size':len(blob),'labels':mapping,'crow_frames':[crowA,crowB],'ship_blast_frames':blast},indent=2))
print(f'LOW SPRITES @ ${low_base:04X} .. ${low_base+len(blob)-1:04X}, {len(blob)} bytes; Crow {crow_offset}..{len(blob)}')
