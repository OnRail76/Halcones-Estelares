; ESF V1.3 optimized star parallax (V1.3.3: 16 estrellas, star_n), Z80 standard assembly, ORG set by main.asm.
; Runtime cache records: physical screen address LO/HI + mask (3 bytes/star).
; Single address calculation per star/update instead of four per update.
; Bounded to x<192, y<192, separate immutable sky plane at $D800.
; All routine instructions are annotated with register and purpose.

stars_v13_init:
 call stars_v13_cache_rebuild   ; Create initial 32 pixel addresses.
 call stars_v13_masks_init     ; Calculate constant masks once (X never changes).
 call stars_v13_draw_all       ; OR initial 32 stars into $C000 working frame.
 jp stars_v13_present_initial  ; Copy all initial star bytes from RAM to screen.

stars_v13_erase_old:
 call stars_v13_select_bank    ; Work on alternating 16-star slices per update.
 ld hl,(stars_v13_active_cache) ; V1.1: solo se guarda la mitad que se mueve
 ld de,(stars_v13_active_previous) ; (la otra mitad no cambia este tick).
 ld bc,star_half_bytes
 ldir
 ; V1.1: borrado especializado de las 16 estrellas que se mueven: quita su bit
 ; de la imagen de trabajo y repone ese bit del cielo inmutable (planeta/MOAI).
 ld hl,(stars_v13_active_cache)
 ld b,star_half
stars_v11_clear_loop:
 ld e,(hl)
 inc hl
 ld a,(hl)
 add a,128
 ld d,a                       ; DE = byte en la imagen de trabajo C000..
 inc hl
 ld c,(hl)                    ; C = bit de la estrella
 inc hl
 ld a,d
 add a,24
 ld d,a                       ; DE = mismo byte en el cielo D800..
 ld a,(de)
 and c                        ; Bit del cielo bajo la estrella.
 ld (stars_v11_sky_bit),a
 ld a,d
 sub 24
 ld d,a
 ld a,c
 cpl
 ex de,hl
 and (hl)
 ex de,hl
 push hl
 ld hl,stars_v11_sky_bit
 or (hl)
 pop hl
 ld (de),a
 djnz stars_v11_clear_loop
 ret
stars_v11_sky_bit: db 0

stars_v13_move:
 ld hl,(stars_v13_active_stars) ; HL=first record of selected 16-star slice.
 ld b,star_half                ; Move only half stars this tick, alternating banks.
stars_v13_move_loop:
 push bc                        ; Save record loop count.
 inc hl                         ; HL -> mutable Y.
 ld a,(hl)                     ; Read previous Y.
 ld (star_y),a                  ; Scratch old Y.
 inc hl                         ; HL -> immutable rate 0/1/2.
 ld a,(hl)                     ; Rate group.
 or a                           ; 0=slow.
 jp z,stars_v13_rate_slow      ; 1 pixel every two game ticks (bank alternation).
 cp 1                           ; 1=middle group.
 jp z,stars_v13_rate_mid       ; 2 pixels per bank visit =1px/tick average.
 ld a,(star_y)                  ; Fast group old Y.
 add a,4                        ; 4 pixels per bank visit=2px/tick average.
 jp stars_v13_move_wrap         ; Wrap/update resulting coordinate.
stars_v13_rate_mid:
 ld a,(star_y)                  ; Medium group old Y.
 add a,2                        ; 2px every two game ticks.
 jp stars_v13_move_wrap         ; Wrap/update.
stars_v13_rate_slow:
 ld a,(star_y)                  ; Slow group old Y.
 inc a                          ; 1px every two ticks.
stars_v13_move_wrap:
 cp 192                         ; Below playfield bottom?
 jp c,stars_v13_move_store     ; In-range Y.
 sub 192                        ; Wrap back to top row.
stars_v13_move_store:
 dec hl                         ; HL points to Y field again.
 ld (hl),a                     ; Write updated Y, preserve X and rate.
 inc hl                         ; Skip to rate byte.
 inc hl                         ; Next record X.
 pop bc                         ; Recover count.
 djnz stars_v13_move_loop      ; Repeat for selected 16 stars.
 ret                            ; Other 16 remain unchanged until next tick.

; Choose one 16-star bank per game update; all 32 still visible.
; Rates are compensated (1/2/4 pixel jumps every other update) to keep
; roughly the same average 0.5/1/2 pixels per tick.
stars_v13_select_bank:
 ld a,(frame_index)            ; Global game tick counter.
 and 1                         ; Alternate two banks.
 jp z,stars_v13_select_first  ; 0 selects first 16-star block.
 ld hl,stars+star_half_bytes               ; Second group begins 16*3 bytes later.
 ld (stars_v13_active_stars),hl ; Save data pointer.
 ld hl,stars_v13_cache+star_half_bytes      ; Second half of current cache.
 ld (stars_v13_active_cache),hl ; Save cache pointer.
 ld hl,stars_v13_previous+star_half_bytes   ; Second half of old cache.
 ld (stars_v13_active_previous),hl ; Save previous pointer.
 ret                            ; Bank selection complete.
stars_v13_select_first:
 ld hl,stars                  ; First 16 records.
 ld (stars_v13_active_stars),hl ; Save data pointer.
 ld hl,stars_v13_cache        ; First 16 cached addresses.
 ld (stars_v13_active_cache),hl ; Save current pointer.
 ld hl,stars_v13_previous     ; First 16 old addresses.
 ld (stars_v13_active_previous),hl ; Save previous pointer.
 ret                            ; Bank selection complete.

; Rebuild physical screen addresses for current (X,Y), precompute single-bit mask.
; IX=star source record, IY=cache destination. Clobbers AF/BC/DE/HL/IX/IY.
stars_v13_cache_rebuild:
 ld ix,stars                  ; IX walks 32 records (X,Y,rate).
 ld iy,stars_v13_cache        ; IY walks 32 screen_addr/bitmask records.
 ld b,star_n                  ; B=star count.
stars_v13_cache_loop:
 push bc                       ; Save star count during address lookup.
 ld a,(ix+0)                  ; Read X from star data.
 ld (star_x),a                 ; Scratch X for physical address formula.
 ld a,(ix+1)                  ; Read Y from star data.
 ld (star_y),a                 ; Scratch Y for formula.
 call stars_v13_screen_addr   ; HL=$4000-based ZX address for this pixel.
 ld (iy+0),l                  ; Save low address byte.
 ld (iy+1),h                  ; Save high address byte.
 ; X is immutable. Its mask is calculated once by stars_v13_masks_init.
 ld de,3                       ; Each data and cache record takes 3 bytes.
 add ix,de                     ; Move IX to next star.
 add iy,de                     ; Move IY to next cache record.
 pop bc                        ; Restore star counter.
 djnz stars_v13_cache_loop    ; Process all 32.
 ret                           ; Current cache addresses now valid.

stars_v13_screen_addr:
 ld a,(star_y)                 ; Pixel Y 0-191.
 ld l,a                        ; HL low=Y.
 ld h,0                        ; Extend Y to word.
 add hl,hl                     ; Offset for DW scanline table.
 ld de,scanline_table          ; Base of precomputed ZX non-linear addresses.
 add hl,de                     ; Pointer to row address.
 ld e,(hl)                    ; Low byte of physical video scanline.
 inc hl                        ; Next entry byte.
 ld d,(hl)                    ; High byte.
 ld a,(star_x)                 ; X in pixels.
 rrca                          ; Shift by one right.
 rrca                          ; Shift by two.
 rrca                          ; Shift by three.
 and 31                        ; X/8, 0-23.
 add a,e                       ; Add horizontal byte column.
 ld e,a                        ; Update low screen pointer.
 ex de,hl                      ; HL=video byte address.
 ret                           ; HL in $4000..$57FF.


; Update only 16 changed addresses. Mask data remains precomputed and unchanged.
stars_v13_cache_rebuild_half:
 ; V1.1: misma direccion que stars_v13_screen_addr, sin IX/IY ni variables.
 ld hl,(stars_v13_active_stars) ; HL = registros (x,y,ritmo) de las 16 que se mueven.
 ld de,(stars_v13_active_cache) ; DE = sus direcciones en la cache.
 ld b,star_half
stars_v11_rebuild_loop:
 ld c,(hl)                      ; C = X
 inc hl
 ld a,(hl)                      ; A = Y
 inc hl
 inc hl
 push hl
 push de
 ld l,a
 ld h,0
 add hl,hl
 ld de,scanline_table
 add hl,de
 ld a,c
 rrca
 rrca
 rrca
 and 31
 add a,(hl)
 inc hl
 ld h,(hl)
 ld l,a                         ; HL = direccion de pantalla del pixel
 pop de
 ex de,hl
 ld (hl),e
 inc hl
 ld (hl),d
 inc hl
 inc hl                         ; La mascara (X fija) no cambia.
 ex de,hl
 pop hl
 djnz stars_v11_rebuild_loop
 ret

; Initialize fixed X-dependent masks (one-time cost, never in hot loop).
; Clobbers AF/BC/DE/HL/IX/IY.
stars_v13_masks_init:
 ld ix,stars                   ; IX iterates immutable star X/Y/rate records.
 ld iy,stars_v13_cache         ; IY iterates 3-byte cache records.
 ld b,star_n                   ; star masks.
stars_v13_mask_init_loop:
 push bc                        ; Preserve loop counter.
 ld a,(ix+0)                   ; Star X coordinate.
 and 7                          ; Choose bit within pixel byte.
 ld e,a                         ; Mask table index low.
 ld d,0                         ; Zero high.
 ld hl,bitmask_table            ; Eight mask bytes 0x80..0x01.
 add hl,de                      ; Table entry for X&7.
 ld a,(hl)                     ; Read one bit.
 ld (iy+2),a                   ; Save as permanent star mask.
 ld de,3                        ; Records 3 bytes.
 add ix,de                      ; Next star.
 add iy,de                      ; Next cache record.
 pop bc                         ; Restore counter.
 djnz stars_v13_mask_init_loop ; Repeat 32.
 ret                            ; All masks precomputed.

; V1.1: stars_v13_apply_cache/apply_selected (modo OR/AND por variable) se
; sustituyeron por los bucles especializados de borrado y dibujo.

stars_v13_draw_all:
 ; V1.1: bucle OR especializado (sin modo ni PUSH/POP por estrella).
 ld hl,stars_v13_cache
 ld b,star_n
stars_v11_draw_loop:
 ld e,(hl)
 inc hl
 ld a,(hl)
 add a,128
 ld d,a                        ; DE = byte en la imagen de trabajo
 inc hl
 ld a,(de)
 or (hl)                       ; Mascara de la estrella
 ld (de),a
 inc hl
 djnz stars_v11_draw_loop
 ret

; Present old and new star bytes only AFTER final sprite composition.
; Each writes a full finalized byte, never XORs or clears VRAM directly.
stars_v13_present_all:
 call stars_v13_present_old    ; Clear old star positions in visible screen.
 jp stars_v13_present_new      ; Display current stars from work buffer.
stars_v13_present_old:
 ld hl,(stars_v13_active_previous) ; Previous 16 moved-star addresses.
 ld b,star_half                  ; Only this bank moved this tick.
 jp stars_v13_sync_loop          ; Sync completed bytes.
stars_v13_present_new:
 ld hl,(stars_v13_active_cache) ; Current 16 moved-star addresses.
 ld b,star_half                  ; Other half unchanged; actor rects repaint as needed.
 jp stars_v13_sync_loop          ; Sync completed bytes.
stars_v13_present_initial:
 ld hl,stars_v13_cache          ; All 32 current positions after initialization.
 ld b,star_n                     ; Initial display requires all stars.
 jp stars_v13_sync_loop          ; Sync first still frame.
stars_v13_sync_loop:
 push bc                       ; Preserve outer counter, LDI changes BC.
 ld e,(hl)                    ; E=screen address low.
 inc hl                        ; Advance to high.
 ld d,(hl)                    ; D=screen address high.
 inc hl                        ; Advance to mask.
 inc hl                        ; Skip mask (not needed for full byte transfer).
 push hl                       ; Preserve next cache record location.
 ld h,d                        ; HL high=screen address high.
 ld l,e                        ; HL low=screen address low.
 ld a,h                        ; Work address differs by $8000.
 add a,128                     ; Map $40xx..$57xx to $C0xx..$D7xx.
 ld h,a                        ; HL is source work pixel address.
 ldi                           ; Copy one FULL FINAL byte to physical screen.
 pop hl                        ; Restore cache pointer.
 pop bc                        ; Restore outer star count.
 djnz stars_v13_sync_loop     ; Continue through all points.
 ret                           ; No writes outside 192px playfield.

stars_v13_active_stars: dw 0    ; Pointer to selected 16 star records.
stars_v13_active_cache: dw 0    ; Pointer to selected 16 cached addresses.
stars_v13_active_previous: dw 0 ; Pointer to previous selected cached addresses.
stars_v13_cache: ds star_bytes      ; 32 records of current video address and bitmask.
stars_v13_previous: ds star_bytes   ; 32 records of old video address and bitmask.
