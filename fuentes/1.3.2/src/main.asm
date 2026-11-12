; ESF SHMUP COMBAT V0.5. Native ZX Spectrum 48K assembler from GRIT ENGINE.
; 192x192 pixel left playfield, authentic GRIT-designed HUD at x192..255.
; Original GRIT / master engine preserved untouched. Gameplay V0.5 in src/gameplay.asm.
; V1.2: tamanos de las tablas de enemigos y balas (antes de cualquier 'ds').
enemy_n equ 10             ; V1.2: diez huecos de enemigo (cuervos: 10; resto: 6)
enemy_bytes equ 60
bullet_n equ 2             ; V1.2: como mucho 2 balas propias a la vez (al estilo Galaga)
bullet_bytes equ 6
org 0x8000
entry:
 di
 ld sp,0xfff0               ; Reserve stack above EFFF: code begins at ORG $8000.
 xor a
 out (0xfe),a
 call v11_boot_clear        ; V1.1: variables nuevas a cero ($F001..$F0FF).
 call explosion_shift_init  ; V1.2: fases de la explosion nueva en $5B00.
 call irq_im2_install       ; Install an isolated Z80 IM2 interrupt; no ROM keyboard/FRAMES writes.
 ld a,0xa5                 ; A = sentinel for first free byte after the sky buffer ($EFFF).
 ld (0xf000),a             ; Detect compositor writes beyond $EFFF on next game tick.
 ld a,0x5a                 ; A = second independent sentinel value.
 ld (0xfdfa),a             ; Before the three-byte JP at $FDFD.
 ld (0xff01),a             ; Immediately after the final IM2 table byte ($FF00).
 ld a,0x3c                 ; A=guard for the byte immediately AFTER $F100-$F3FF attrs.
 ld (0xf400),a             ; Guard against accidental overrun of color shadow buffer.
 ei                        ; Enable IM2 after the table and trampoline are complete.
title_session_start:
 call title_screen_show       ; Copy native title graphic into real Spectrum VRAM.
 call title_screen_wait       ; Wait for fresh SPACE press; not an automatic start.
 call arcade_screen_clear
 call hud_install
 call frame_install             ; V1.7: draw the 16px left border once in live screen.
 ; Static stars disabled: starfield now scrolls inside composite RAM.
 call compositor_init
 call stars_v13_init
 call combat_init
 call combat_render

main_loop:
 ; Runtime sentinels: detect stack imbalance or writes beyond video work/IM2.
 ld hl,0                   ; HL = 0 for reading the live SP with ADD HL,SP.
 add hl,sp                 ; HL now equals the *actual* stack pointer.
 ld a,h                    ; A = high byte of SP.
 cp 0xff                   ; Expect stack to be in the upper $FFxx page.
 jp nz,panic_memory        ; Any other page means unbalanced calls or stack overwrite.
 ld a,l                    ; A = low byte of SP.
 cp 0xf0                   ; Expect exactly $FFF0 between game ticks.
 jp nz,panic_memory        ; Interruption handler must balance SP as well.
 ld a,(0xf000)             ; Guard byte above $C000-$EFFF work planes.
 cp 0xa5                   ; Has a renderer escaped into $F000?
 jp nz,panic_memory        ; Diagnostic red border on boundary damage.
 ld a,(0xf400)             ; Read first byte beyond the 768-byte color attribute shadow.
 cp 0x3c                   ; It must retain its original guard value.
 jp nz,panic_memory        ; Stop if any attribute write escaped into $F400.
 ld a,(0xfdfa)             ; Guard immediately before the IM2 trampoline.
 cp 0x5a                   ; Verify unchanged.
 jp nz,panic_memory        ; Stop without jumping into the ROM on memory corruption.
 ld a,(0xff01)             ; Guard immediately after IM2 vector page.
 cp 0x5a                   ; Verify unchanged.
 jp nz,panic_memory        ; Detect 257-byte vector initialization overflow.
 ld a,(player_lives)       ; Three lives exhausted?
 or a
 jr nz,main_gameplay_alive
 ; Let the last ship truly EXPLODE and disappear before GAME OVER.
 ld a,(shield_invulnerable)
 cp 50                      ; Above 49: 1s explosion + 1s absence.
 jp c,gameover_enter        ; No respawn on the final life.
main_gameplay_alive:
 call pause_check           ; V1.1: H = pausa.
 call tick_wait             ; V1.1: ritmo fijo de 25 ticks/s (antes 12-17 y variable).
 call combat_tick           ; One complete private-buffer composition and presentation.

 jp main_loop

; Panic loop — RED border denotes internal memory/stack guard failure,
; not ordinary attr clash. Never returns to BASIC/ROM and never writes text.
panic_memory:
 di                        ; Interrupts disabled: stop before further RAM damage.
 ld a,2                    ; Red border, beeper off.
 out (0xfe),a              ; Diagnostic visible even if playfield is corrupt.
 jp panic_memory           ; Stay here until emulator is reset manually.

; Fetch native HUD bitmap into shadow (8 bytes / Spectrum scanline).
hud_install:
 ld hl,hud_lz               ; V1.2: HUD comprimido; se descomprime en la imagen
 ld de,0xc000               ; de trabajo (aun libre) y se copia como siempre.
 call lz_unpack
 ld hl,0xc000
 ld (hud_source),hl
 xor a
hud_bitmap_row:
 ld (hud_y),a
 ld l,a
 ld h,0
 add hl,hl
 ld de,scanline_table
 add hl,de
 ld e,(hl)
 inc hl
 ld d,(hl)
 ex de,hl
 ld bc,24
 add hl,bc
 ex de,hl
 ld hl,(hud_source)
 ld bc,8
 ldir
 ld (hud_source),hl
 ld a,(hud_y)
 inc a
 cp 192
 jp nz,hud_bitmap_row
 ; Attributes laid out row-major 8 columns; screen total width 32.
 ld hl,0xc000+1536
 ld de,0x5818
 ld b,24
hud_attr_row:
 push bc
 ld bc,8
 ldir
 push hl
 ex de,hl
 ld bc,24
 add hl,bc
 ex de,hl
 pop hl
 pop bc
 djnz hud_attr_row
 ret

; V1.7 ORIGINAL HALCONES DECORATIVE FRAME (x0..15).
; Input: none. Output: left 16 pixel columns + their 48 attributes on-screen.
; Clobbers: AF,BC,DE,HL. All reads from compiled immutable Z80 tables.
; Crucially called BEFORE compositor_init, so C000 and D800 snapshot the rail.
frame_install:
 ld hl,frame_bitmap_low        ; V1.2 (antes $7BC0) immutable 384-byte left frame from low RAM sprite CODE block.
 ld (frame_source),hl          ; Save source pointer for each of 192 non-linear scanlines.
 xor a                         ; A = pixel row 0.
frame_bitmap_row:
 ld (frame_y),a               ; Save row index (other registers are consumed by LDIR).
 ld l,a                       ; HL low = row index.
 ld h,0                       ; HL = row index as unsigned 16-bit word.
 add hl,hl                    ; HL = row*2 (word entries).
 ld de,scanline_table         ; DE = compiled Spectrum non-linear scanline table.
 add hl,de                    ; HL = entry address for current row.
 ld e,(hl)                    ; E = low byte of VRAM destination.
 inc hl                       ; HL points to high byte of that destination.
 ld d,(hl)                    ; DE = visible VRAM scanline at x=0.
 ld hl,(frame_source)         ; HL = 2 source bytes for this row.
 ld bc,2                      ; BC = exactly two character columns (16px).
 ldir                         ; Copy both bytes into physical bitmap and advance HL/DE.
 ld (frame_source),hl         ; Save source cursor for next scanline.
 ld a,(frame_y)               ; Read row index.
 inc a                        ; Advance one vertical scanline.
 cp 192                       ; Check 192 Spectrum scanlines.
 jp nz,frame_bitmap_row      ; Repeat until both rail bytes per row are installed.
 ld hl,frame_attr_data        ; HL = 48 native 8x8 color attrs, two per block row.
 ld de,0x5800                 ; DE = top-left attribute cell, first two columns.
 ld b,24                      ; B = 24 character rows.
frame_attr_row:
 push bc                      ; LDIR destroys BC: preserve row counter.
 ld bc,2                      ; Copy two color cells of the rail.
 ldir                         ; HL/DE advance by two native attribute bytes.
 ex de,hl                     ; HL = current VRAM position (two columns in).
 ld bc,30                     ; Skip remaining 30 columns before next row.
 add hl,bc                    ; HL now points at next 32-byte attribute row.
 ex de,hl                     ; DE = next row's first attribute cell.
 pop bc                       ; Restore 24-row counter.
 djnz frame_attr_row         ; Repeat exactly 24 times.
 ret                          ; Return with visible rail installed.

frame_source: dw 0             ; Scratch source pointer for frame rows.
frame_y: db 0                 ; Scratch Y index for non-linear VRAM lookup.

; Stars data: x pixel (0..191), y pixel (0..191), speed group 0,1,2.
; A single vertical parallax rate is applied per star independently.
; Legacy direct-to-VRAM star updater removed in V2.0.
; stars_v13_* are the only active star routines.

stars:
 db 21,6,0, 29,42,1, 25,19,2, 36,113,0
 db 47,67,1, 53,150,2, 64,33,0, 72,92,1
 db 80,12,2, 91,41,0, 108,120,1, 116,25,2
 db 123,72,0, 137,173,1, 142,58,2, 153,7,0
 db 163,125,1, 174,87,2, 185,18,0, 28,178,1
 db 44,3,2, 60,183,0, 76,142,1, 95,95,2
 db 113,179,0, 132,132,1, 150,161,2, 169,50,0
 db 182,166,1, 33,84,2, 106,6,0, 30,163,1

hud_source: dw 0
hud_y: db 0
star_x: db 0
star_y: db 0
frame_index: db 0
