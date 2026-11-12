; GRIT ENGINE / ARCADE XOR SPRITE MODULE v0.2 (opt-in). ZX Spectrum 48K.
; Based on shifted sprite concepts described by David M. Webb, chapter 12.
; This implementation is independently authored and tested, not a transcription.
; No ROM dependencies, fixed screen. Do not include with shadow framebuffer engine.
; INPUTS spr_data -> table of 8 DW addresses of pre-shifted 1bpp frames
;        spr_x, spr_y -> pixel coords, spr_cols=2/3/4, spr_height=height
; Each phase occupies cols*height bytes. Each sprite is applied by XOR.
; Call twice to erase if all overlapping objects have been erased in reverse order.
; Caller must ensure 0<=spr_y<=192-spr_height and horizontal bytes stay x<192.
; Requires scanline_table: DW address for 192 scanlines, built in asset generator.

sprite_render:
 ld a,(spr_x)
 and 7
 add a,a
 ld e,a
 ld d,0
 ld hl,(spr_data)
 add hl,de
 ld e,(hl)
 inc hl
 ld d,(hl)
 ex de,hl
 ld (spr_ptr),hl
 ld a,(spr_x)
 rrca
 rrca
 rrca
 and 31
 ld (spr_col_byte),a
 ld a,(spr_y)
 ld l,a
 ld h,0
 add hl,hl
 ld de,scanline_table
 add hl,de
 ld (spr_scan_table_ptr),hl
 ld a,(spr_height)
 ld (spr_rows_left),a
 ld a,(spr_cols)
 cp 4
 jp z,sprite_row4
 cp 3
 jp z,sprite_row3
 jp sprite_row2

; The row prologue is intentionally repeated for each fixed-width specialization.
; Removes the runtime inner byte loop and its DJNZ for *every sprite row*.
sprite_row2:
 ld hl,(spr_scan_table_ptr)
 ld e,(hl)
 inc hl
 ld d,(hl)
 inc hl
 ld (spr_scan_table_ptr),hl
 ld a,(spr_col_byte)
 add a,e
 ld e,a
 ld hl,(spr_ptr)
 ld a,(de)
 xor (hl)
 ld (de),a
 inc hl
 inc de
 ld a,(de)
 xor (hl)
 ld (de),a
 inc hl
 inc de
 ld (spr_ptr),hl
 ld a,(spr_rows_left)
 dec a
 ld (spr_rows_left),a
 jp nz,sprite_row2
 ret

sprite_row3:
 ld hl,(spr_scan_table_ptr)
 ld e,(hl)
 inc hl
 ld d,(hl)
 inc hl
 ld (spr_scan_table_ptr),hl
 ld a,(spr_col_byte)
 add a,e
 ld e,a
 ld hl,(spr_ptr)
 ld a,(de)
 xor (hl)
 ld (de),a
 inc hl
 inc de
 ld a,(de)
 xor (hl)
 ld (de),a
 inc hl
 inc de
 ld a,(de)
 xor (hl)
 ld (de),a
 inc hl
 inc de
 ld (spr_ptr),hl
 ld a,(spr_rows_left)
 dec a
 ld (spr_rows_left),a
 jp nz,sprite_row3
 ret

sprite_row4:
 ld hl,(spr_scan_table_ptr)
 ld e,(hl)
 inc hl
 ld d,(hl)
 inc hl
 ld (spr_scan_table_ptr),hl
 ld a,(spr_col_byte)
 add a,e
 ld e,a
 ld hl,(spr_ptr)
 ld a,(de)
 xor (hl)
 ld (de),a
 inc hl
 inc de
 ld a,(de)
 xor (hl)
 ld (de),a
 inc hl
 inc de
 ld a,(de)
 xor (hl)
 ld (de),a
 inc hl
 inc de
 ld a,(de)
 xor (hl)
 ld (de),a
 inc hl
 inc de
 ld (spr_ptr),hl
 ld a,(spr_rows_left)
 dec a
 ld (spr_rows_left),a
 jp nz,sprite_row4
 ret

spr_data: dw 0
spr_x: db 0
spr_y: db 0
spr_cols: db 0
spr_height: db 0
