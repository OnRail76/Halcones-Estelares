; Extracted + isolated Grit Claymore renderer (MIT, (c) 2026 Tony C. Ware).
; 0x6000..0x7AFF shadow VRAM. 0x4000..0x5AFF visible.
screen_clear:
 ; Shadow video: complete 6912-byte Spectrum screen at 0x6000..0x7AFF.
 ; Shadow video uses 0x6000..0x7AFF; Z80 stack is in free RAM 0x7B00..0x7FFF.
 xor a
 ld hl,0x6000
 ld de,0x6001
 ld bc,6143
 ld (hl),a
 ldir
 ld a,7
 ld hl,0x7800
 ld de,0x7801
 ld bc,767
 ld (hl),a
 ldir
 call clear_dirty
 ret

; Dirty cells are composited in shadow RAM; the visible screen never sees
; an erase-and-wait gap between separate enemy updates.
clear_dirty:
 xor a
 ld (dirty_count),a
 ld hl,dirty_flags
 ld de,dirty_flags+1
 ld bc,767
 ld (hl),a
 ldir
 ret

; Deduplicated dirty queue: up to 240 tile coordinates (D=row, E=column).
; Overflow falls back to a full copy safely, without corrupting the queue.
mark_dirty:
 ; CRITICAL V07.1 FIX: A is the INK/PAPER attribute passed to the blitter.
 ; Saving AF AFTER testing full_redraw replaced every attribute with 0 or 1!
 ; Preserve AF *before* touching A, including on the early exit branch.
 push af
 ld a,(full_redraw)
 or a
 jp z,md_continue
 pop af
 ret
md_continue:
 push bc
 push de
 push hl
 ld l,d
 ld h,0
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 ld c,e
 ld b,0
 add hl,bc
 ld bc,dirty_flags
 add hl,bc
 ld a,(hl)
 or a
 jp nz,md_done
 ld (hl),1
 ld a,(dirty_count)
 cp 240
 jp nc,md_overflow
 ld c,a
 ld b,0
 ld hl,dirty_pairs
 add hl,bc
 add hl,bc
 ld (hl),d
 inc hl
 ld (hl),e
 ld a,(dirty_count)
 inc a
 ld (dirty_count),a
 jp md_done
md_overflow:
 ld a,1
 ld (full_redraw),a
md_done:
 pop hl
 pop de
 pop bc
 pop af
 ret

clear_dirty_one:
 push bc
 push de
 push hl
 ld l,d
 ld h,0
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 ld c,e
 ld b,0
 add hl,bc
 ld bc,dirty_flags
 add hl,bc
 ld (hl),0
 pop hl
 pop de
 pop bc
 ret

; Called ONCE when an arena enters or the 8px viewport strip scrolls.
; Full screen copy is necessarily costlier, but ordinary animation uses only
; dirty 8x8 cells instead of showing the blanked background to the ULA.
present_full:
 ld hl,0x6000
 ld de,0x4000
 ld bc,6144
 ldir
 ld hl,0x7800
 ld de,0x5800
 ld bc,768
 ldir
 xor a
 ld (full_redraw),a
 jp clear_dirty

; Sparse presentation, ONLY the tiles changed by actor movement or the HUD.
; Ordinary frames never scan all 768 dirty flags or copy a blanked actor.
present_dirty:
 ld a,(dirty_count)
 or a
 ret z
 ld b,a
 ld hl,dirty_pairs
pd_next:
 push bc
 ld d,(hl)
 inc hl
 ld e,(hl)
 inc hl
 push hl
 call clear_dirty_one
 call present_cell
 pop hl
 pop bc
 djnz pd_next
 xor a
 ld (dirty_count),a
 ret

; D = tile row E = column. Copy 8 actual pixel bytes AND its attribute.
present_cell:
 push de
 call playfield_addr
 ld a,h
 xor 0x20
 ld d,a
 ld e,l
 ld b,8
pc_pix:
 ld a,(hl)
 ld (de),a
 inc h
 inc d
 djnz pc_pix
 pop de
 call attribute_addr
 ld a,h
 xor 0x20
 ld d,a
 ld e,l
 ld a,(hl)
 ld (de),a
 ret


playfield_addr:
 ld a,d
 and 24
 add a,0x60
 ld h,a
 ld a,d
 and 7
 add a,a
 add a,a
 add a,a
 add a,a
 add a,a
 add a,e
 ld l,a
 ret
attribute_addr:
 ld l,d
 ld h,0
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 ld bc,0x7800
 add hl,bc
 ld c,e
 ld b,0
 add hl,bc
 ret



blit_cell:
 call mark_dirty
 push af
 push bc
 push de
 push hl
 ld (blit_src),hl
 ld (blit_attr),a
 ld a,d
 ld (blit_y),a
 ld a,e
 ld (blit_x),a
 ; bitmap start at 0x4000 | ((row AND 24)<<8), low=((row AND 7)*32)+x
 ld a,d
 and 24
 add a,0x60
 ld h,a
 ld a,d
 and 7
 add a,a
 add a,a
 add a,a
 add a,a
 add a,a
 add a,e
 ld l,a
 ld de,(blit_src)
 ld b,8
blit_pixels:
 ld a,(de)
 ld (hl),a
 inc de
 inc h
 djnz blit_pixels
 ; attribute address 0x5800+row*32+column
 ld a,(blit_y)
 ld l,a
 ld h,0
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 ld de,0x7800
 add hl,de
 ld a,(blit_x)
 ld e,a
 ld d,0
 add hl,de
 ld a,(blit_attr)
 ld (hl),a
 pop hl
 pop de
 pop bc
 pop af
 ret

; Sprite con mascara expandida (1 px negro alrededor): preserva fondo.
; (bitmap_fondo AND mascara) OR sprite. La mascara elimina el fondo bajo
; la silueta, pero el atributo sigue siendo por celda 8x8 en Spectrum.
blit_masked_cell:
 call mark_dirty
 push af
 push bc
 push de
 push hl
 push ix                    ; IX is the actor pointer in gameplay loops
 ld (blit_src),hl
 ld (blit_attr),a
 ld a,d
 ld (blit_y),a
 ld a,e
 ld (blit_x),a
 ld a,d
 and 24
 add a,0x60               ; shadow screen, never visible mid-frame
 ld h,a
 ld a,d
 and 7
 add a,a
 add a,a
 add a,a
 add a,a
 add a,a
 add a,e
 ld l,a
 ld de,(blit_src)        ; sprite byte pointer
 push hl
 ld hl,(mask_src)
 push hl
 pop ix                   ; independent mask byte pointer
 pop hl                   ; screen byte pointer
 ld b,8
bm_pixels:
 ld c,(ix+0)
 ld a,(hl)
 and c
 ld c,a
 ld a,(de)
 or c
 ld (hl),a
 inc de
 inc ix
 inc h
 djnz bm_pixels
 ; Each cell has a legal Spectrum attribute; return to static attr on erase.
 ld a,(blit_y)
 ld l,a
 ld h,0
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 ld de,0x7800
 add hl,de
 ld a,(blit_x)
 ld e,a
 ld d,0
 add hl,de
 ld a,(blit_attr)
 ld (hl),a
 pop ix
 pop hl
 pop de
 pop bc
 pop af
 ret

