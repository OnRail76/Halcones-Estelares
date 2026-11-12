"""Halcon nuevo del titulo (alas por geometria + cabeza y cuerpo a mano)."""
import math
from PIL import Image,ImageDraw
from tools.v12_zx import *
import tools.v12_hawk_wings as hawk
hawk.LEAD=[(111,103),(104,98),(96,94),(86,91),(76,89),(64,88),(52,88),(40,88),(30,89),(22,90),(17,92),(14,96)]
hawk.FINGERS=[(12,108),(15,115),(20,121),(27,126),(35,130),(44,133)]
hawk.SECS=[(53,135),(62,136),(71,136),(80,135),(88,133),(96,130),(103,126),(109,121),(112,117)]
HEAD_L=[ # x112..127, y88..103 (mitad izquierda; se refleja)
"...........#####",
".........#######",
".......#########",
"......##########",
".....###########",
"....##.#########",
"....#....#######",
"...##.##...#####",
"...#.##.##..####",
"...##.##.#..####",
"....##..##.#####",
"....#####.######",
"...######.######",
"...#######.#####",
"....#######.####",
"....########.###"]
BEAK=[ # x120..135, y96..111 (tinta amarilla sobre papel cian)
"....########....",
"...##########...",
"...###.##.###...",
"...##########...",
"....########....",
"....########....",
".....######.....",
".....##..##.....",
"......####......",
"......####......",
".......##.......",
".......##.......",
"................",
"................",
"................",
"................"]
BODY_L=[ # x112..127, y104..127 (pecho con escamas)
"....############",
"...#############",
"..##############",
"..###.#####.####",
".###.#.###.#.###",
".##.###.#.###.##",
".###########.###",
".##.#####.#####.",
"..#.#.###.#.###.",
"..##.###.#.#.###",
"..##############",
"..###.#####.####",
"...#.#.###.#.###",
"...#.###.#.###.#",
"...###########.#",
"....#.#####.####",
"....#.#.###.#.##",
".....###.#.###.#",
".....##########.",
"......#########.",
"......##.####.##",
".......#.##.#.##",
".......##.###.##",
"........########"]
TAIL_L=[ # x120..127, y128..143 (cola blanca en abanico, plumas anchas)
"########",
"########",
"########",
".#######",
".###.###",
".###.###",
"####.###",
"###..###",
"###.####",
"###.####",
"##..####",
"##.#####",
"##.####.",
"#..###..",
"#..##...",
"...#...."]
LEG_L=[ # x112..119, y128..143 (pata y garras amarillas)
"....####",
"....####",
"...####.",
"...###..",
"...###..",
"...##...",
"..###...",
"..##....",
".####...",
"######..",
"##.#.##.",
"#..#..#.",
"#..#..#.",
"...#....",
"........",
"........"]
def mirror(rows):return [r+r[::-1] for r in rows]
def head_left():
    """Mitad izquierda de la cabeza (x112..127, y88..103): ceja fiera y ojo."""
    half=[6,8,10,11,12,13,13,14,14,14,14,14,13,13,12,12]
    rows=[]
    for h in half:
        rows.append(['.']*(16-h)+['#']*h)
    def blk(y,a,b):
        for i in range(a,b+1):rows[y-88][i]='.'
    blk(92,4,6);blk(93,6,9);blk(94,8,11);blk(95,10,13)     # ceja: baja hacia el pico
    blk(94,4,5);blk(95,4,8);blk(96,5,7)                     # ojo bajo la ceja
    rows[95-88][6]='#'                                       # brillo
    for y,i in ((99,2),(101,3),(103,4)):rows[y-88][i]='.'   # plumas de la mejilla
    return [''.join(r) for r in rows]
def draw(z):
    z.clear(0,84,256,144)
    w=hawk.wings()
    for y in range(88,144):
        for x in range(256):
            if w[y][x] and not 112<=x<144:z.px[y][x]=1
    # cuerpo y cabeza
    for j,r in enumerate(mirror(head_left())):
        for i,ch in enumerate(r):z.px[88+j][112+i]=1 if ch=='#' else 0
    for j,r in enumerate(mirror(BODY_L)):
        for i,ch in enumerate(r):z.px[104+j][112+i]=1 if ch=='#' else 0
    for j,r in enumerate(mirror(TAIL_L)):
        for i,ch in enumerate(r):z.px[128+j][120+i]=1 if ch=='#' else 0
    for j,r in enumerate(LEG_L):
        for i,ch in enumerate(r):
            z.px[128+j][112+i]=1 if ch=='#' else 0
            z.px[128+j][143-i]=1 if ch=='#' else 0
    # pico: celdas de papel cian y tinta amarilla (cabeza maciza alrededor)
    for j,r in enumerate(BEAK):
        for i,ch in enumerate(r):z.px[96+j][120+i]=1 if ch=='#' else 0
    # atributos
    for r in range(11,18):
        for c in range(0,32):
            z.at[r][c]=A(WHT) if r<=13 else A(YEL)       # alas: coberteras blancas, remeras doradas
    z.attr(14,11,18,16,A(CYN))                            # cabeza y cuerpo
    z.attr(15,12,17,14,A(YEL,CYN))                        # pico sobre la cara
    z.attr(15,16,17,18,A(WHT))                            # cola
    z.attr(14,16,15,18,A(YEL));z.attr(17,16,18,18,A(YEL)) # patas
    return z
