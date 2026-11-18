#!/usr/bin/env python3
"""Original ESF enemy designs with 2 mechanically winged frames, native 16x16.
Phoenix/Galaga-inspired movement language, NOT copied raster art.
Runs after build_ship_assets; updates manifested sprite bytes for current game.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import json
R=Path(__file__).resolve().parents[1]
P=R/'assets/sprites'
M=json.loads((P/'sprite_manifest.json').read_text())

def canvas():
    i=Image.new('1',(16,16),0)
    return i,ImageDraw.Draw(i)

def mirror(poly):return [(15-x,y) for x,y in poly]

def polygon_both(d,points):d.polygon(points,fill=1);d.polygon(mirror(points),fill=1)

def falcon(f):
    """FALCON: narrow beak and segmented wingblades; outward/downward flap."""
    im,d=canvas()
    d.polygon([(7,3),(8,3),(10,7),(10,10),(9,14),(8,15),(7,15),(6,14),(5,10),(5,7)],fill=1)
    d.rectangle((7,7,8,8),fill=0)
    if f==0:
        polygon_both(d,[(6,6),(4,5),(2,5),(0,3),(0,7),(2,9),(5,10),(6,9)])
        d.line((0,4,2,6),fill=0)
        d.line((15,4,13,6),fill=0)
    else:
        polygon_both(d,[(6,7),(4,9),(2,9),(1,12),(1,15),(3,14),(6,12),(7,10)])
        d.point((3,12),fill=0);d.point((12,12),fill=0)
    d.line((7,10,7,13),fill=0)
    return im

def raptor(f):
    """RAPTOR: swept boomerang / crescent hunter, bright angular silhouette."""
    im,d=canvas()
    d.polygon([(7,2),(8,2),(10,6),(10,10),(8,14),(7,14),(5,10),(5,6)],fill=1)
    d.polygon([(7,4),(8,4),(8,7),(7,7)],fill=0)
    if f==0:
        polygon_both(d,[(6,6),(4,4),(2,2),(0,1),(1,6),(3,8),(5,10),(6,9)])
        d.point((1,5),fill=0);d.point((14,5),fill=0)
    else:
        polygon_both(d,[(6,6),(4,7),(3,10),(1,11),(0,14),(3,13),(5,12),(7,9)])
        d.point((2,11),fill=0);d.point((13,11),fill=0)
    d.rectangle((7,12,8,13),fill=1)
    return im

def wraith(f):
    """WRAITH: armoured alien owl/manta, talons and wing joints."""
    im,d=canvas()
    d.polygon([(6,2),(9,2),(11,5),(11,10),(9,11),(9,14),(8,15),(7,15),(6,14),(6,11),(4,10),(4,5)],fill=1)
    d.point((6,6),fill=0);d.point((9,6),fill=0)
    d.rectangle((7,9,8,11),fill=0)
    if f==0:
        polygon_both(d,[(5,5),(3,5),(1,4),(0,6),(0,9),(2,9),(4,11),(6,10)])
        d.line((1,7,3,7),fill=0);d.line((12,7,14,7),fill=0)
    else:
        polygon_both(d,[(5,5),(3,8),(2,11),(1,14),(3,14),(5,13),(6,11),(6,8)])
        d.point((3,11),fill=0);d.point((12,11),fill=0)
    return im

def pack(im):
    return [sum((128>>b) for b in range(8) if im.getpixel((8*k+b,y))) for y in range(16) for k in range(2)]

for name,fn,ink in (('enemy_needle',falcon,6),('enemy_blade',raptor,2),('enemy_drone',wraith,5)):
    frames=[fn(0),fn(1)]
    for i,im in enumerate(frames):im.save(P/f'{name}_frame{i}.png')
    frames[0].save(P/f'{name}.png')
    a,b=map(pack,frames)
    M[name].update(pixel_bytes=a,mask_bytes=[255^x for x in a],frame1_pixel_bytes=b,
                   frame1_mask_bytes=[255^x for x in b],ink=[[ink,ink],[ink,ink]],
                   purpose='original ESF Phoenix-like mechanical winged enemy (2 animated native frames)')
(P/'sprite_manifest.json').write_text(json.dumps(M,indent=2))
print('3 original ESF enemy silhouettes x 2 frames, native monochrome data, attributes Yellow/Red/Cyan')

# Keep the bundled AND/OR asset bank consistent with the live XOR sprite data.
# The game uses *_shifted; *_pixels_masked remains a reusable GRIT data format.
lines=['; SOURCE: actual native ESF pixels, masks and fixed Spectrum attributes.']
for name,s in M.items():
 w,h=s['width'],s['height']
 lines.extend([f'{name}_width: db {w}',f'{name}_height: db {h}',f'{name}_pixels_masked:'])
 rowbytes=w//8
 for y in range(h):
  both=[]
  for j in range(rowbytes):
   off=y*rowbytes+j;both.extend((s['mask_bytes'][off],s['pixel_bytes'][off]))
  lines.append(' db '+','.join(map(str,both)))
 lines.append(f'{name}_attributes:')
 for row in s['ink']:
  lines.append(' db '+','.join(str(64+n) for n in row))
 if 'frame1_pixel_bytes' in s:
  lines.append(f'{name}_frame1_pixels_masked:')
  for y in range(h):
   both=[]
   for j in range(rowbytes):
    off=y*rowbytes+j
    both.extend((s['frame1_mask_bytes'][off],s['frame1_pixel_bytes'][off]))
   lines.append(' db '+','.join(map(str,both)))
(R/'build/ship_assets.asm').write_text('\n'.join(lines)+'\n')
