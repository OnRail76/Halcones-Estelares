"""Halcon nuevo del titulo (coordenadas globales del Spectrum)."""
import math
from PIL import Image,ImageDraw
LEAD=[(111,104),(104,99),(96,95),(88,91),(80,88),(72,86),(64,86),(54,87),(44,89),(34,91),(25,94),(18,98),(15,103)]
# puntas de las primarias (dedos) y de las secundarias (festón)
FINGERS=[(14,116),(18,123),(24,129),(31,133),(39,136),(48,138)]
SECS=[(57,138),(66,138),(75,137),(84,135),(92,132),(100,128),(107,123),(111,119)]
def outline():
    pts=list(LEAD)
    tips=FINGERS+SECS
    # entre punta y punta, una muesca hacia dentro (separa las plumas)
    prev=LEAD[-1]
    for i,t in enumerate(tips):
        if i>0:
            a=tips[i-1];mx,my=(a[0]+t[0])/2,(a[1]+t[1])/2
            # hacia el centro del ala
            cx,cy=70,104;dx,dy=cx-mx,cy-my;l=math.hypot(dx,dy)
            depth=7 if i<len(FINGERS) else 3
            pts.append((mx+dx/l*depth,my+dy/l*depth))
        pts.append(t)
    return pts
def draw_left(d):
    d.polygon(outline(),fill=1)
    tips=FINGERS+SECS
    # lineas de separacion entre plumas: desde la muesca hacia el foco
    for i in range(1,len(tips)):
        a,t=tips[i-1],tips[i];mx,my=(a[0]+t[0])/2,(a[1]+t[1])/2
        fx,fy=(66,100) if i<len(FINGERS)+1 else (86,104)
        frac=0.62 if i<len(FINGERS)+1 else 0.45
        d.line([(mx,my),(mx+(fx-mx)*frac,my+(fy-my)*frac)],fill=0)
    # canones (raquis) punteados en las primarias
    for t in FINGERS[:-1]:
        fx,fy=66,100
        for k in range(3,13,2):
            q=k/30;d.point((t[0]+(fx-t[0])*q+1,t[1]+(fy-t[1])*q),fill=0)
    # coberteras: dos filas de escamas
    for row,(base,r,n) in enumerate((((108,110),(4,3),10),((104,103),(4,3),9),((100,96),(4,3),8))):
        for k in range(n):
            t=k/(n-1)
            x=base[0]-t*(78,70,60)[row]
            y=base[1]-6*math.sin(t*math.pi*0.9)+t*(0,1,2)[row]
            d.arc((x-r[0],y-r[1],x+r[0],y+r[1]),10,170,fill=0)
def wings():
    im=Image.new('1',(256,192),0);d=ImageDraw.Draw(im);draw_left(d)
    px=im.load();out=[[0]*256 for _ in range(192)]
    for y in range(192):
        for x in range(128):
            if px[x,y]:out[y][x]=1;out[y][255-x]=1
    return out
if __name__=='__main__':
    b=wings();im=Image.new('RGB',(256,64))
    for y in range(64):
        for x in range(256):
            if b[84+y][x]:im.putpixel((x,y),(255,255,255))
    im.resize((256*5,64*5),0).save('/tmp/wings.png')
