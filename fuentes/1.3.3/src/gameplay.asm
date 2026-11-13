; EUROPEAN STAR FORCE / COMBATE V0.5
; Native Z80 gameplay on genuine shadow Spectrum framebuffer. No mockups.
; 25 logical ticks per second. Gameplay uses 8 shifted 1-bit masks per sprite.
; SPACE dispara SOLO en transicion de tecla suelta a pulsada; sin auto-repeticion.
; Q/A/O/P move at 3 px/tick. Key-edge latch stores prior state.

combat_init:
 ld a,80
 ld (ship_x),a
 ld a,152
 ld (ship_y),a
 xor a
 ld (fire_held),a   ; A=0: SPACE starts released (one-shot edge detector)
 ld (frame_index),a ; New game: Crow wait cadence must start from zero.
 ld (rush_rest_ticks),a      ; No kamikaze regroup timer on first game.
 ld (rush_pause_active),a    ; No suspended wave on first game.
 ld (led_anim_phase),a      ; Three red frame LEDs start at upper position.
 ld (led_anim_clock),a      ; Reset LED scan cadence.
 ld (player_respawn_pending),a ; No pending respawn on new game.
 ld (kills),a
 ld (tick_irqs),a            ; V1.1: el primer tick empieza con el reloj a cero.
 ld a,10
 ld (enemy_count),a          ; V1.2: la partida empieza con diez cuervos
 xor a
 ld hl,(record_words)        ; V1.2: record al empezar (para NUEVO RECORD)
 ld (record_start),hl
 ld (score_words),a          ; V1.1: marcador de 16 bits a cero.
 ld (score_words+1),a
 ld (life_next),a
 ld (grace_irqs),a
 ld (boss_eye),a
 ld (card_ticks),a
 ld a,32                     ; Primer disparo enemigo tras 1,3 s.
 ld (enemy_fire_cd),a
 xor a
 ld (wave_done),a
 ld (wave_stage),a           ; Start with slower formation on game boot.
 ld (wave_repeat),a          ; Every wave family appears TWICE per boss circuit.
 ld (hunter_pair_active),a
 ld (hunter_pair_turn),a
 ld (hunter_sway_bias),a
 ld (hunter_attack_cooldown),a
 ld (wave_cycle),a           ; Number of completed MOAI circuits, capped at four.
 ld a,1
 ld (phase_number),a
 ld hl,enemy_slots           ; V1.1: la primera oleada entra tras su cartel.
 ld de,enemy_slots+1
 ld bc,enemy_bytes-1
 ld (hl),0
 ldir
 ld a,1
 ld (wave_done),a
 ld hl,bullet_slots
 ld de,bullet_slots+1
 ld bc,bullet_bytes-1
 xor a
 ld (hl),a
 ldir
 call shield_init          ; V1.8: arm real-time shield, lives and enemy projectiles.
 call color_shadow_init      ; Snapshot current VRAM color attrs into private 768-byte RAM plane.
 call led_frame_apply        ; Only the upper warning lamp begins BRIGHT; other two start dim.
 call boss_scene_sync        ; Cielo inmovil -> imagen de trabajo y pantalla.
 call wave_card_start        ; V1.1: cartel OLEADA 1 (tras copiar los atributos).
 jp hud_draw_all             ; V1.2: marcador completo con los valores de la partida nueva.

combat_tick:
 ; Keep OLD positions and animation phase: no long whole-wave erase interval.
 ; Each object is XOR-erased and replaced immediately in render_deltas.
 ld hl,enemy_slots
 ld de,old_enemy_slots
 ld bc,enemy_bytes
 ldir
 ld hl,bullet_slots
 ld de,old_bullet_slots
 ld bc,bullet_bytes
 ldir
 ld hl,enemy_bullet_slots
 ld de,old_enemy_bullets
 ld bc,9
 ldir
 ld a,(anim_phase)
 ld (old_anim_phase),a
 ld a,(ship_x)
 ld (ship_old_x),a
 ld a,(ship_y)
 ld (ship_old_y),a
 ; shield_previous_state tracks LAST PRESENTED frame, not current IM2 state.
 ; The interrupt may expire the shield before this update starts.
 call input_poll             ; V1.1: una sola lectura de mandos por tick.
 call player_respawn_tick
 call player_keys
 ; Snapshot shield visibility for this entire bitmap+attribute frame.
 ; IM2 may expire the live timer DURING the renderer; never mix the states.
 ld a,(shield_state)
 ld (shield_frame_state),a
 ld a,(ship_x)
 ld (ship_new_x),a
 ld a,(ship_y)
 ld (ship_new_y),a
 ld a,(frame_index)
 inc a
 ld (frame_index),a
 and 4
 jp z,animation_wings_up
 ld a,1
animation_wings_up:
 ld (anim_phase),a
 ; V2.8.9: once the LAST life is exhausted, do not run enemy AI,
 ; projectile movement or collision logic during the two-second death finale.
 ; Continue composing the last known enemy positions and the original three
 ; ESF explosion frames; the 50Hz IM2 death counter remains unchanged.
 ld a,(player_lives)
 or a
 jp z,combat_last_death_freeze
 call wave_update
 call bullet_update
 call enemy_bullet_update      ; Enemy fire moves toward the player; independent of FIRE.
 call shield_collisions        ; Active shield destroys nearby birds and their bullets.
 call ship_hit_collisions      ; Unprotected impacts cost one life.
 call player_fire
combat_last_death_freeze:
 call wave_unpaint_old       ; Restore old enemy colors ONLY in $F100 attribute shadow.
 call player_unpaint_old     ; Restore old cockpit/engines ONLY in the attribute shadow.
 call wave_paint_new         ; Build full new enemy palette before changing visible ULA attributes.
 call player_paint_new       ; Ship palette has final priority in the shadow attribute map.
 call enemy_bullet_colors   ; V1.2: rombos enemigos en magenta (solo sobre celdas blancas).
 call composite_update      ; Compose/present all sprite pixels without whitening on-screen color.
 call card_draw             ; V1.1: texto del cartel OLEADA encima de todo.
 call color_shadow_present  ; Copy fully composed 8x8 attributes in one final pass to VRAM.
 call card_attr_present     ; V1.1: color del cartel OLEADA (8 celdas).
 ld a,(shield_frame_state)
 ld (shield_previous_state),a ; The exact shield visible in last COMPOSED frame.
 call compositor_scrub      ; Progressive repair of stray pixel bytes only.
 ld a,(wave_stage)         ; Boss eye updates must NOT run on normal formations.
 cp 3
 call z,boss_eye_tick        ; Eye cells: red / black with perceptible pauses.
 call led_frame_tick         ; Change only the three fixed rail attribute cells.
 call shield_bar_present      ; Redraw only 32 pixels x 8 scanlines on meter changes.
 call lives_hud_present      ; Change life icons only after a confirmed hit.
 ld a,(shield_ready_pending) ; Consume a deferred 50Hz shield-ready chime.
 or a
 ret z
 xor a
 ld (shield_ready_pending),a
 call badge_shine           ; V1.3: la insignia brilla
 call sfx_shield_ready
 ret

; V1.6: PRIVATE COLOR PLANE, deliberately independent of sprite bitmap planes.
; The previous renderer reset OLD sprite attributes directly in visible VRAM,
; then spent over 100,000 T-states composing a new bitmap. During that work,
; the ULA showed WHITE enemies for entire refreshes. No longer do that.
; VRAM attrs $5800..$5AFF, private attrs $F100..$F3FF (768 bytes).
; $F100..$F3FF is disjoint from $FDFD/$FE00 IM2 and $FFF0 stack.
; Input: none. Outputs: HL,DE advance; BC zero; flags clobbered.
color_shadow_init:
 ld hl,0x5800             ; HL = beginning of the live ULA attribute table.
 ld de,0xf100             ; DE = 768-byte private color buffer (safe upper RAM).
 ld bc,768                ; BC = all 32x24 attribute bytes, including the fixed HUD.
 ldir                     ; Copy attributes ONCE before gameplay (Z80 block instruction).
 ret                      ; Colors may now be composed off-screen.

; V1.6 fast color commit: final palette is built in RAM, NEVER whiten VRAM.
; Copy only OLD+NEW 8x8 color footprints for enemies and the ESF fighter.
; This preserves colored sprites during long pixel-composition operations and
; costs much less than copying all 576 playfield attribute cells every frame.
; $F100..$F3FF = private attributes; $5800..$5AFF = native screen attributes.
; Clobbers AF BC DE HL IX, preserves IY, restores caller stack on every path.
color_shadow_present:
 ; V1.1: la huella antigua de un enemigo solo se copia si no coincide con la
 ; nueva (misma celda 8x8): la nueva ya cubre esas 9 celdas.
 ; V1.2: un enemigo que no ha cambiado (misma x, y y estado) no se vuelve a
 ; copiar: sus celdas ya estan en pantalla. Si otro enemigo toca esas celdas,
 ; la caja de ese otro las cubre.
 ld ix,old_enemy_slots      ; IX points to last frame's enemy status records.
 ld iy,enemy_slots
 ld a,(enemy_count)       ; V1.2: 10 con los cuervos, 6 en el resto
 ld b,a
color_old_pair_loop:
 push bc
 call enemy_unchanged
 jr z,color_old_pair_next
 ; V1.3: la huella antigua se copia siempre. El atajo "misma celda" de la 1.1
 ; comparaba x,y en bruto, pero la caja del cuervo empieza en x+4,y+4 y podia
 ; cambiar de celda sin que x,y cambiaran: quedaban celdas rojas en pantalla.
 call color_present_enemy
 push ix
 push iy
 pop ix
 call color_present_enemy
 pop ix
color_old_pair_next:
 ld de,6
 add ix,de
 add iy,de
 pop bc
 djnz color_old_pair_loop
 ld a,(ship_old_x)         ; A = previous ESF x position in pixels.
 ld b,a                    ; B = x input for ship color-rectangle.
 ld a,(ship_old_y)         ; A = previous ESF y position in pixels.
 ld c,a                    ; C = y input for ship color-rectangle.
 call color_present_ship    ; Update the previous ESF occupied attribute cells.
 ld a,(ship_x)             ; A = new ESF x coordinate.
 ld b,a                    ; B = x input to color presenter.
 ld a,(ship_y)             ; A = new ESF y coordinate.
 ld c,a                    ; C = y input to color presenter.
 call color_present_ship    ; Update current ESF original attribute cells.
 ld a,(shield_previous_state)
 cp 1
 call z,color_present_shield_old
 ld a,(shield_frame_state)
 cp 1
 call z,color_present_shield_new
 ; V1.2: celdas de los rombos enemigos (antiguas y nuevas), 2x2.
 ld ix,old_enemy_bullets
 call color_present_bullets
 ld ix,enemy_bullet_slots
color_present_bullets:
 ld b,3
color_bullet_loop:
 push bc
 ld a,(ix+2)
 or a
 jr z,color_bullet_next
 ld a,2
 ld (color_rect_w),a
 ld (color_rect_h),a
 ld b,(ix+0)
 ld c,(ix+1)
 call color_present_box
color_bullet_next:
 ld de,3
 add ix,de
 pop bc
 djnz color_bullet_loop
 ret

; 5x5 ULA attribute cells for shield, clipped to x<192. Changed only on active ticks.
color_present_shield_old:
 ld a,(ship_old_x)
 sub 4
 ld b,a
 ld a,(ship_old_y)
 sub 6
 ld c,a
 jp color_present_shield
color_present_shield_new:
 ld a,(ship_x)
 sub 4
 ld b,a
 ld a,(ship_y)
 sub 6
 ld c,a
color_present_shield:
 ld a,5
 ld (color_rect_w),a
 ld (color_rect_h),a
 jp color_present_box

; Input IX points at six 6-byte enemy records; preserves no scratch regs.
color_present_six:
 ld a,(enemy_count)       ; V1.2: 10 con los cuervos, 6 en el resto
 ld b,a
color_present_six_loop:
 push bc                   ; Save slot counter across painter, which clobbers BC.
 call color_present_enemy  ; Copy only this enemy's live 8x8 color footprint.
 ld de,6                   ; DE = length of one enemy record.
 add ix,de                 ; IX advances to the next old/new enemy slot.
 pop bc                    ; Restore slot counter after painter.
 djnz color_present_six_loop ; Repeat for all six enemies.
 ret                       ; Caller can now process ship or next list.

; Input IX = enemy record [X,Y,alive,type,...]. No writes for dead enemies.
color_present_enemy:
 ld a,(ix+2)              ; A=alive flag for this snapshot.
 or a                      ; Set Z if enemy is inactive.
 ret z                     ; Dead object has no attribute footprint in this snapshot.
 call enemy_box_ix          ; V1.2: B,C = esquina; D = 3 celdas (2 para un cuervo)
 ld a,d
 ld (color_rect_w),a       ; Desired rectangle width measured in 8px cells.
 ld (color_rect_h),a       ; Desired rectangle height is also three cells.
 jp color_present_box      ; Copy final palette over its old/new footprint.

; Input BC = ship x/y pixels. Vary footprint 3 or 4 cells for pixel alignment.
color_present_ship:
 ld a,4                    ; V1.2: siempre 4 filas (la llama baja a la fila siguiente).
 ld (color_rect_h),a
 ld a,b                    ; A=left edge x pixel.
 and 7                     ; Test if sprite left edge is byte-aligned.
 ld a,3                    ; 24px wide occupies 3 cells when aligned.
 jr z,color_ship_width_ok  ; Aligned sprites do not need a fourth column.
 inc a                     ; Misaligned sprite can occupy 4 attribute columns.
color_ship_width_ok:
 ld (color_rect_w),a       ; Save selected width for the ship.
 jp color_present_box      ; Present precisely that rectangle.

; Input B=pixel x, C=pixel y, color_rect_w/h=desired sizes (2..4).
; Output: final ATTR values copied from private RAM to VRAM over the rectangle;
; clipped before right-hand HUD (columns >=24) and below screen row 23.
color_present_box:
 ld a,b                    ; A=x pixel coordinate.
 cp 192                    ; Is left edge already in HUD/outside playfield?
 ret nc                    ; Do not write HUD attributes from game objects.
 rrca                      ; Rotate x, preparing x/8.
 rrca                      ; Rotate x/4.
 rrca                      ; Rotate x/2.
 and 31                    ; A=x /8 in the 32-column attribute map.
 ld (color_col),a          ; Save column index 0..23 for address calculation.
 ld e,a                    ; E=column of initial 8x8 cell.
 ld a,24                   ; Maximum number of playfield columns.
 sub e                     ; A = remaining playable columns from x onward.
 ld b,a                    ; B = horizontal clip width.
 ld a,(color_rect_w)       ; A = desired rectangle width.
 cp b                      ; If requested width exceeds the remaining cells...
 jr c,color_box_width_ok   ; ...otherwise keep the requested size.
 ld a,b                    ; Truncate rectangle before the HUD begins.
color_box_width_ok:
 ld (color_rect_w),a       ; Safe width clipped to columns 0..23.
 ld a,c                    ; A=y pixel coordinate.
 cp 192                    ; Is it below visible screen bitmap?
 ret nc                    ; Do not write outside 24 attribute rows.
 rrca                      ; Compute y/8 with three rotations.
 rrca                      ; Second rotate.
 rrca                      ; Third rotate.
 and 31                    ; 0..23 for valid sprite position.
 ld (color_row),a          ; Save row index for address calculation.
 ld e,a                    ; E=attribute row.
 ld a,24                   ; Number of playable screen rows.
 sub e                     ; A = remaining screen rows.
 ld b,a                    ; B = vertical clipped height.
 ld a,(color_rect_h)       ; A = requested height.
 cp b                      ; Clamp the requested height if needed.
 jr c,color_box_height_ok  ; Requested value is less than remaining rows.
 ld a,b                    ; Truncate before going beyond last attribute row.
color_box_height_ok:
 ld (color_rect_h),a       ; Safe row count, always >=1 here.
 ld a,(color_row)          ; A=row index.
 ld l,a                    ; HL=row.
 ld h,0                    ; High byte cleared for zero-extended row.
 add hl,hl                 ; Multiply row by two.
 add hl,hl                 ; Multiply row by four.
 add hl,hl                 ; Multiply row by eight.
 add hl,hl                 ; Multiply row by sixteen.
 add hl,hl                 ; Multiply row by thirty-two.
 ld a,(color_col)          ; A=column index.
 ld e,a                    ; DE=column.
 ld d,0                    ; Clear high part of DE.
 add hl,de                 ; HL=attribute offset row*32+column.
 push hl                   ; Preserve offset for independent live address.
 ld de,0xf100              ; DE=private base address.
 add hl,de                 ; HL=source cell in private color RAM.
 ex de,hl                  ; DE=private source cell, HL=base $F100.
 pop hl                    ; HL=original offset.
 ld bc,0x5800              ; BC=native ULA attribute base.
 add hl,bc                 ; HL=destination cell in real video RAM.
 ex de,hl                  ; HL=private source, DE=native VRAM destination.
 ld a,(color_rect_w)       ; A=safe width, 1 to 5 cells.
 cp 5
 jp z,color_box_row5
 cp 4                      ; Select unrolled fast 4-byte copy.
 jp z,color_box_row4       ; Copy 4 bytes across each row.
 cp 3                      ; Select 3-byte copy for 16px enemy.
 jp z,color_box_row3       ; Most enemies take this path.
 cp 2                      ; Select 2-byte clip for rightmost x boundary.
 jp z,color_box_row2       ; Copy two bytes per row.
 jp color_box_row1         ; Only one column remains before HUD.

; LDI copies HL -> DE and increments pointers in 16 Z80 T-states.
color_box_row5:
 ldi
 ldi
 ldi
 ldi
 ldi
 ld bc,27
 call color_box_next_row
 jp nz,color_box_row5
 ret
color_box_row4:
 ldi                       ; First source attribute -> native screen attribute.
 ldi                       ; Second cell in same row.
 ldi                       ; Third cell in same row.
 ldi                       ; Fourth cell in same row.
 ld bc,28                  ; 32-column row stride less four copied bytes.
 call color_box_next_row   ; Advance and see whether another row remains.
 jp nz,color_box_row4      ; Repeat unless vertical count reached zero.
 ret                       ; Finished four-column rectangle.
color_box_row3:
 ldi                       ; Copy color cell 0.
 ldi                       ; Copy color cell 1.
 ldi                       ; Copy color cell 2.
 ld bc,29                  ; Step to next row after three copied bytes.
 call color_box_next_row   ; Advance and reduce number of remaining rows.
 jp nz,color_box_row3      ; Repeat for remaining 8px rows.
 ret                       ; Finished three-column rectangle.
color_box_row2:
 ldi                       ; Copy first attribute.
 ldi                       ; Copy second attribute.
 ld bc,30                  ; 32 minus two columns.
 call color_box_next_row   ; Advance and count row.
 jp nz,color_box_row2      ; Repeat until complete.
 ret                       ; Finished two-column rectangle.
color_box_row1:
 ldi                       ; One attribute in the last playfield column.
 ld bc,31                  ; Skip to next line's same column.
 call color_box_next_row   ; Advance and count row.
 jp nz,color_box_row1      ; Continue if more rows remain.
 ret                       ; Finished one-column rectangle.

; Input HL=private source next cell, DE=screen dest next cell, BC=stride.
; Clobbers AF. Leaves Z flag set when no more rows remain.
color_box_next_row:
 add hl,bc                 ; HL=source next 32-column attr row.
 ex de,hl                  ; Place live destination in HL for matching stride.
 add hl,bc                 ; HL=destination next 32-column attr row.
 ex de,hl                  ; Restore source HL, destination DE.
 ld a,(color_rect_h)       ; A=remaining row count including current.
 dec a                     ; One row has been copied.
 ld (color_rect_h),a       ; Store remaining row count for next call.
 ret                       ; Z set when count reaches zero.

color_rect_w: db 3         ; Selected, clipped rectangle width in 8px cells.
color_rect_h: db 3         ; Selected, clipped rectangle height in 8px rows.
color_col: db 0            ; Current 8x8 attribute column.
color_row: db 0            ; Current 8x8 attribute row.

; Colored enemies are drawn into the native Spectrum attribute file. Each
; type is ONE ink color (yellow/magenta/cyan) across its covered 8x8 cells.
; The old attributes are restored and the new footprints are painted only once.
wave_unpaint_old:
 ld ix,old_enemy_slots
 ld a,(enemy_count)       ; V1.2: 10 con los cuervos, 6 en el resto
 ld b,a
wave_unpaint_loop:
 push bc
 ld a,0x47
 ld (enemy_paint_color),a
 call paint_enemy_attr_ix
 ld de,6
 add ix,de
 pop bc
 djnz wave_unpaint_loop
 ret
wave_paint_new:
 ld ix,enemy_slots
 ld a,(enemy_count)       ; V1.2: 10 con los cuervos, 6 en el resto
 ld b,a
wave_paint_loop:
 push bc
 ld a,(ix+3)
 ld e,a
 ld d,0
 ld hl,enemy_palettes
 add hl,de
 ld a,(hl)
 ld (enemy_paint_color),a
 call paint_enemy_attr_ix
 ld de,6
 add ix,de
 pop bc
 djnz wave_paint_loop
 ret

paint_enemy_attr_ix:
 ld a,(ix+2)
 or a
 ret z
 call enemy_box_ix          ; V1.2: 3x3 celdas, o 2x2 para un cuervo
 push de
 ld a,c
 and 248
 ld l,a
 ld h,0
 add hl,hl
 add hl,hl
 ld a,b
 rrca
 rrca
 rrca
 and 31
 ld e,a
 ld d,0
 add hl,de
 ld de,0xf100
 add hl,de
 pop bc
 ld c,b
 ld a,(enemy_paint_color)
paint_enemy_rows:
 push bc
 push hl
paint_enemy_cols:
 ld (hl),a
 inc hl
 djnz paint_enemy_cols
 pop hl
 ld de,32
 add hl,de
 pop bc
 dec c
 jr nz,paint_enemy_rows
 ret

; ---------------- ORIGINAL VARIANT D COLOUR, SCREEN-ATTRIBUTE SAFE ----------------
; This is INK cell color only: the Spectrum has 8x8 attribute resolution.
; No color bitplanes, and no sprites with multicolor within one 8x8 cell.
; As a result the narrow cockpit and engine colors can spill to neighboring
; monochrome fuselage pixels when crossing attribute-cell boundaries.
;
; Input: B=pixel X, C=pixel Y, A=INK|BRIGHT on black PAPER.
; Output: one attribute cell at $5800 + ((Y>>3)*32) + (X>>3).
; Clobbers AF, DE, HL, preserves BC and IX/IY.
ship_attr_plot:
 ld (ship_attr_ink),a     ; Store requested color while computing the address.
 ld a,b                   ; X in pixels.
 rrca                     ; Divide by 2 (circular shift; higher bits masked).
 rrca                     ; Divide by 4.
 rrca                     ; Divide by 8.
 and 31                   ; Limit to one of 32 attribute columns.
 ld e,a                   ; DE becomes 0..31.
 ld d,0                   ; Clear high byte.
 ld a,c                   ; Y in pixels.
 rrca                     ; Move row bits into lower five places.
 rrca                     ; Y / 4.
 rrca                     ; Y / 8.
 and 31                   ; Cell row 0..23.
 ld l,a                   ; HL=row.
 ld h,0                   ; Zero-extend row.
 add hl,hl                ; row*2.
 add hl,hl                ; row*4.
 add hl,hl                ; row*8.
 add hl,hl                ; row*16.
 add hl,hl                ; row*32.
 add hl,de                ; Add horizontal attribute cell.
 ld de,0xf100             ; Private attribute plane starts at $F100 (not visible to ULA).
 add hl,de                ; HL points at one actual ULA attribute byte.
 ld a,(ship_attr_ink)     ; Restore the desired color.
 ld (hl),a                ; Change only that private 8x8 color cell; VRAM untouched.
 ret                      ; Preserve caller BC.

; Input ship_attr_x/y identify current or old sprite's top-left pixel.
; A=color of central cockpit (0x45 for cyan, 0x47 for white restore).
; Destroys AF, BC, DE, HL; IX/IY untouched.
ship_paint_cockpit:
 ld (ship_attr_ink),a     ; Save ink for repeated calls.
 ld a,(ship_attr_x)       ; Ship left edge.
 add a,8                  ; Center cell left edge: original V04 matrix row.
 ld b,a                   ; B is first central horizontal point.
 ld a,(ship_attr_y)       ; Ship top edge.
 add a,4                  ; First sampling point in nose/cockpit.
 ld c,a                   ; C is first sample Y.
 ld a,(ship_attr_ink)     ; A is original ink color.
 call ship_attr_plot      ; Paint current center cell.
 ld a,(ship_attr_x)       ; Reload ship X because A was clobbered.
 add a,15                 ; Right edge of central 8px band.
 ld b,a                   ; B = second sample X.
 ld a,(ship_attr_ink)     ; Set desired color again.
 call ship_attr_plot      ; Cover possible attribute-boundary crossing.
 ret                      ; Done for cockpit.

; Input ship_attr_x/y identify current or old sprite's top-left pixel.
; A=color of central engines (0x46 yellow, or 0x47 white restore).
; Clobbers AF, BC, DE, HL; preserves IX/IY.
ship_paint_engines:
 ld (ship_attr_ink),a     ; Store desired engine attribute.
 ld a,(ship_attr_x)       ; Ship origin X.
 add a,9                  ; First left thruster pixel group.
 ld b,a                   ; Set X sample.
 ld a,(ship_attr_y)       ; Ship origin Y.
 add a,20                 ; Engine lower row sample.
 ld c,a                   ; Set Y sample.
 ld a,(ship_attr_ink)     ; Restore color.
 call ship_attr_plot      ; Set attribute of left thruster.
 ld a,(ship_attr_x)       ; Reload ship origin X.
 add a,14                 ; Right thruster pixel group.
 ld b,a                   ; Set second X sample.
 ld a,(ship_attr_ink)     ; Restore color.
 call ship_attr_plot      ; Set right thruster.
 ld a,(ship_attr_y)       ; Reload origin Y.
 add a,23                 ; Bottom edge of exhaust.
 ld c,a                   ; May cross into next 8px attribute row.
 ld a,(ship_attr_ink)     ; Desired exhaust color.
 call ship_attr_plot      ; Right lower exhaust cell.
 ld a,(ship_attr_x)       ; Reload origin X.
 add a,9                  ; Left exhaust again.
 ld b,a                   ; Set left X sample.
 ld a,(ship_attr_ink)     ; Desired exhaust color.
 call ship_attr_plot      ; Left lower exhaust cell.
 ld a,(ship_attr_y)       ; V1.2: celdas de la llama, bajo cada tobera.
 add a,26
 ld c,a
 ld a,(ship_attr_ink)
 call ship_attr_plot
 ld a,(ship_attr_x)
 add a,14
 ld b,a
 ld a,(ship_attr_ink)
 jp ship_attr_plot

; Revert only the colored old footprint. Enemy colors are applied afterwards.
; Using white default is valid because the static playfield is bright-white
; ink on black, while sprites and stars in the area are 1-bit graphics.
player_unpaint_old:
 ld a,(ship_old_x)       ; Last frame X.
 ld (ship_attr_x),a      ; Set attribute-space origin.
 ld a,(ship_old_y)       ; Last frame Y.
 ld (ship_attr_y),a      ; Set attribute-space origin.
 ld a,0x47               ; Bright white ink, black PAPER.
 call ship_paint_cockpit ; Clear old cyan cell(s).
 ld a,(shield_previous_state)  ; Was the old pixel overlay visible?
 cp 1                         ; Ignore unprotected previous frame.
 call z,shield_color_unpaint   ; Remove old perimeter attributes from private plane.
 ld a,0x47               ; Bright white ink, black PAPER.
 jp ship_paint_engines   ; Clear old yellow cell(s).

; Original V0.4 Variant D: white airframe, cyan front, yellow engines.
; Ship has priority over overlapping enemy colors in affected 8x8 cells.
player_paint_new:
 ld a,(shield_invulnerable)
 cp 100
 jr nc,player_paint_explosion
 cp 50
 ret nc
 or a
 jr z,player_paint_live
 ld a,(frame_index)
 and 2
 ret nz
player_paint_live:
 ld a,(ship_x)           ; Current ship X.
 ld (ship_attr_x),a      ; Set origin of native attribute painter.
 ld a,(ship_y)           ; Current ship Y.
 ld (ship_attr_y),a      ; Set current origin Y.
 ld a,0x45               ; BRIGHT cyan ink, black PAPER for cockpit.
 call ship_paint_cockpit ; Paint central fuselage/cockpit.
 ld a,(shield_frame_state)          ; Is shield active in the new frame?
 cp 1                         ; 1 = active.
 call z,shield_color_paint    ; Border cells green (still no VRAM writes).
 ld a,0x46               ; BRIGHT yellow ink for two thrusters.
 jp ship_paint_engines   ; Paint engine cells and return.

ship_attr_x: db 0         ; Current selected ship origin X.
ship_attr_y: db 0         ; Current selected ship origin Y.
ship_attr_ink: db 0x47    ; Scratch saved INK attribute byte.

; Process old/new as neighboring operations, not 'erase entire screen,
; run all game logic, then redraw entire screen'. Minimizes ULA tear window.
 ; Draw every live sprite on the private compositing buffer *after* restoring
 ; ALL previous footprints from the fixed background. On-screen writes only
 ; occur after the new frame is complete, so no intermediate erase frames.
player_paint_explosion:
 ld a,(ship_x)
 ld (ship_attr_x),a
 ld a,(ship_y)
 ld (ship_attr_y),a
 ld a,0x42                  ; Red explosion accents; no green/yellow ship remains.
 jp ship_paint_cockpit

composite_update:
 ; V2.0: Boss uses SAME renderer and moving stars as ordinary waves.
 ; V1.9 skipped restoration while boss was active, accumulating old
 ; projectile/ship trails in the composed screen (vertical columns).
 call stars_v13_erase_old      ; Remove moved star pixels, preserving static sky.
 call composite_restore_old   ; Restore ALL old ship/bullet/enemy rectangles.
 call stars_v13_move          ; Three star parallax rates keep moving at the MOAI.
 call stars_v13_cache_rebuild_half
 call stars_v13_draw_all      ; OR stars onto the current private background.
 call wave_draw               ; Six enemies or none during the boss scene.
 call bullet_draw_all
 call player_draw
 call enemy_bullet_draw_all
 call composite_present_old
 call composite_present_new
 call stars_v13_present_all   ; Present both moving bank positions, even at boss.
 ret

composite_restore_old:
 ld ix,old_enemy_slots
 ld a,(enemy_count)       ; V1.2: 10 con los cuervos, 6 en el resto
 ld b,a
co_re_e:
 push bc
 call comp_restore_enemy_ix
 ld de,6
 add ix,de
 pop bc
 djnz co_re_e
 ld ix,old_enemy_bullets
 ld b,3
co_re_enemy_b:
 push bc
 call comp_restore_bullet_ix
 ld de,3
 add ix,de
 pop bc
 djnz co_re_enemy_b
 ld ix,old_bullet_slots
 ld b,bullet_n
co_re_b:
 push bc
 call comp_restore_bullet_ix
 ld de,3
 add ix,de
 pop bc
 djnz co_re_b
 ld a,(ship_old_x)
 ld (spr_x),a
 ld a,(ship_old_y)
 ld (spr_y),a
 ld a,4
 ld (spr_cols),a
 ld a,28                 ; V1.2: 24 filas de nave + 4 de llama
 ld (spr_height),a
 call sprite_restore
 ld a,(shield_previous_state)
 cp 1
 ret nz
 ; Old shield extends above and beyond the 24x24 ship rectangle.
 ld a,(ship_old_x)
 sub 4
 ld (spr_x),a
 ld a,(ship_old_y)
 sub 6
 ld (spr_y),a
 ld a,5
 ld (spr_cols),a
 ld a,34                 ; V1.2: escudo (32) hasta el final de la llama
 ld (spr_height),a
 jp sprite_restore

composite_present_old:
 ; Enemy old+new footprints are merged in one rectangle per enemy.
 ; No duplicated screen transfer while they descend by 2 pixels.
 ld ix,old_bullet_slots
 ld b,bullet_n
co_pre_b:
 push bc
 call comp_present_bullet_ix
 ld de,3
 add ix,de
 pop bc
 djnz co_pre_b
 ld ix,old_enemy_bullets
 ld b,3
co_pre_enemy_b:
 push bc
 call comp_present_bullet_ix
 ld de,3
 add ix,de
 pop bc
 djnz co_pre_enemy_b
 call comp_present_ship_union
 ret

composite_present_new:
 call composite_present_enemy_pairs
 ld ix,bullet_slots
 ld b,bullet_n
co_prn_b:
 push bc
 call comp_present_bullet_ix
 ld de,3
 add ix,de
 pop bc
 djnz co_prn_b
 ld ix,enemy_bullet_slots
 ld b,3
co_prn_enemy_b:
 push bc
 call comp_present_bullet_ix
 ld de,3
 add ix,de
 pop bc
 djnz co_prn_enemy_b
 ret

composite_present_enemy_pairs:
 ld ix,old_enemy_slots
 ld iy,enemy_slots
 ld a,(enemy_count)       ; V1.2: 10 con los cuervos, 6 en el resto
 ld b,a
co_union_loop:
 push bc
 call comp_present_enemy_pair
 ld de,6
 add ix,de
 add iy,de
 pop bc
 djnz co_union_loop
 ret

comp_present_enemy_pair:
 ; V1.2: quieto, mismo estado y mismo dibujo de aleteo: ya esta en pantalla
 ; (las estrellas y las balas que pasen por encima se presentan por su cuenta).
 ld a,(anim_phase)
 ld hl,old_anim_phase
 cp (hl)
 jr nz,co_changed
 call enemy_unchanged
 jr nz,co_changed
 cp 3
 ret nz                     ; quieto y no explotando (o vacio)
co_changed:
 ld a,(ix+2)
 or a
 jp z,co_present_new_only   ; recien aparecido: solo el nuevo
 ld a,(iy+2)
 or a
 jp z,comp_present_enemy_ix ; desaparecido: solo el viejo
 ; V1.2: los dos activos: un solo rectangulo que cubre el viejo y el nuevo,
 ; con el tamano de cada tipo (cuervo 2x8, resto 3x16).
 call enemy_box_ix          ; viejo: B,C, E bytes, A alto
 ld (co_old_x),a            ; (alto, provisional)
 ld a,b
 ld (spr_x),a
 ld a,c
 ld (spr_y),a
 ld a,e
 ld (spr_cols),a
 push ix
 push iy
 pop ix
 call enemy_box_ix          ; nuevo
 pop ix
 ld d,a
 ld a,(co_old_x)
 cp d
 jp nz,co_present_fallback  ; un cuervo que pasa a explosion: por separado
 ld (spr_height),a
 ld a,(spr_x)
 rrca
 rrca
 rrca
 and 31
 ld d,a                     ; columna vieja
 ld a,b
 rrca
 rrca
 rrca
 and 31
 sub d
 jr z,co_union_y            ; misma columna
 cp 1
 jr z,co_union_wide         ; el nuevo, una a la derecha
 cp 255
 jp nz,co_present_fallback
 ld a,b
 ld (spr_x),a               ; el nuevo, una a la izquierda
co_union_wide:
 ld a,(spr_cols)
 inc a
 ld (spr_cols),a
co_union_y:
 ld a,(spr_y)
 ld d,a
 ld a,c
 sub d                      ; dy = nuevo - viejo
 cp 9
 jp nc,co_present_fallback
 ld d,a
 ld a,(spr_height)
 add a,d
 ld (spr_height),a
 jp sprite_present
co_old_x: db 0
co_present_fallback:
 call comp_present_enemy_ix
co_present_new_only:
 push ix
 push iy
 pop ix
 call comp_present_enemy_ix
 pop ix
 ret

comp_present_ship_union:
 ; V2.3 only: the actual 32x32 field extends 4px left/6px above ship.
 ld a,(shield_frame_state)
 cp 1
 jp z,comp_present_shield_pair
 ld a,(shield_previous_state)
 cp 1
 jp z,comp_present_shield_pair
 ; One merged rectangle old/new, even after 3px diagonal movement.
 ld a,(ship_old_x)
 rrca
 rrca
 rrca
 and 31
 ld b,a
 ld a,(ship_new_x)
 rrca
 rrca
 rrca
 and 31
 sub b
 jp z,cps_same_x
 cp 1
 jp z,cps_right
 cp 255
 jp z,cps_left
 jp cps_fallback
cps_same_x:
 ld a,(ship_old_x)
 ld (spr_x),a
 ld a,4
 ld (spr_cols),a
 jp cps_y
cps_right:
 ld a,(ship_old_x)
 ld (spr_x),a
 ld a,5
 ld (spr_cols),a
 jp cps_y
cps_left:
 ld a,(ship_new_x)
 ld (spr_x),a
 ld a,5
 ld (spr_cols),a
cps_y:
 ld a,(ship_old_y)
 ld c,a
 ld a,(ship_new_y)
 cp c
 jp c,cps_moved_up
 sub c
 add a,28                 ; V1.2: 24 filas de nave + 4 de llama
 ld (spr_height),a
 ld a,c
 ld (spr_y),a
 jp sprite_present
cps_moved_up:
 ld b,a
 ld a,c
 sub b
 add a,28                 ; V1.2: 24 filas de nave + 4 de llama
 ld (spr_height),a
 ld a,b
 ld (spr_y),a
 jp sprite_present
; Two 5-column regions are presented when the shield is involved.
; This is deliberately limited to the active/transition state (only 3 seconds).
comp_present_shield_pair:
 ld a,(ship_old_x)
 sub 4
 ld (spr_x),a
 ld a,(ship_old_y)
 sub 6
 ld (spr_y),a
 ld a,5
 ld (spr_cols),a
 ld a,34                 ; V1.2: escudo (32) hasta el final de la llama
 ld (spr_height),a
 call sprite_present
 ld a,(ship_new_x)
 sub 4
 ld (spr_x),a
 ld a,(ship_new_y)
 sub 6
 ld (spr_y),a
 ld a,5
 ld (spr_cols),a
 ld a,34                 ; V1.2: escudo (32) hasta el final de la llama
 ld (spr_height),a
 jp sprite_present

cps_fallback:
 ld a,(ship_old_x)
 ld (spr_x),a
 ld a,(ship_old_y)
 ld (spr_y),a
 ld a,4
 ld (spr_cols),a
 ld a,28                 ; V1.2: 24 filas de nave + 4 de llama
 ld (spr_height),a
 call sprite_present
 ld a,(ship_new_x)
 ld (spr_x),a
 ld a,(ship_new_y)
 ld (spr_y),a
 ld a,4
 ld (spr_cols),a
 ld a,28                 ; V1.2: 24 filas de nave + 4 de llama
 ld (spr_height),a
 jp sprite_present

comp_restore_enemy_ix:
 ld a,(ix+2)
 or a
 ret z
 call enemy_rect_ix
 jp sprite_restore

comp_present_enemy_ix:
 ld a,(ix+2)
 or a
 ret z
 call enemy_rect_ix
 jp sprite_present

; V1.2: un cuervo vivo (tipo 3, no explotando) es un 8x8 dentro de su celda de
; 16x16: rectangulos de 2 bytes x 8 lineas y 2x2 celdas de color (antes 3x16 y
; 3x3 como cualquier enemigo). Diez cuervos cuestan menos que seis enemigos.
; Sale: B=x, C=y, D=celdas de color, E=bytes, A=alto en lineas.
enemy_box_ix:
 ld b,(ix+0)
 ld c,(ix+1)
 ld de,0x0303
 ld a,(ix+3)
 cp 3
 ld a,16
 ret nz
 ld a,(ix+2)
 cp 3
 ld a,16
 ret z
 ld a,b
 add a,4
 ld b,a
 ld a,c
 add a,4
 ld c,a
 ld de,0x0202
 ld a,8
 ret
; Z si el registro viejo (IX) y el nuevo (IY) coinciden en estado, x e y.
; Sale con A = estado.
enemy_unchanged:
 ld a,(ix+0)
 cp (iy+0)
 ret nz
 ld a,(ix+1)
 cp (iy+1)
 ret nz
 ld a,(ix+2)
 cp (iy+2)
 ret
enemy_rect_ix:
 call enemy_box_ix
 ld (spr_height),a
 ld a,b
 ld (spr_x),a
 ld a,c
 ld (spr_y),a
 ld a,e
 ld (spr_cols),a
 ret

; V1.1: rectangulos de proyectil de 2 bytes x 4 filas, exactamente los bytes
; que pinta sprite_render (cols=2 desde x>>3). Sin columnas de guarda y con
; una preparacion propia de ~200 T (antes ~500 T por rectangulo, 3 por bala).
comp_restore_bullet_ix:
 call bullet_rect_dest      ; DE = destino base 4000; NC = no cabe / inactivo
 ret nc
 ld a,d
 add a,0x98                 ; Origen: cielo inmutable D800..
 ld h,a
 ld l,e
 add a,-24                  ; Destino: imagen de trabajo C000..
 ld d,a
 ld bc,8
 jp rest_row2

comp_present_bullet_ix:
 call bullet_rect_dest
 ret nc
 ld a,d
 add a,128                  ; Origen: trabajo C000..; destino: pantalla
 ld h,a
 ld l,e
 ld bc,8
 jp pres_row2

; IX = registro [x,y,activo]. Carry = activo y cabe (y <= 188); DE = pantalla.
bullet_rect_dest:
 ld a,(ix+2)
 or a
 ret z                      ; Z con carry 0 (OR lo pone a 0)
 ld a,(ix+1)
 cp 189
 ret nc
 ld l,a
 ld h,0
 add hl,hl
 ld de,scanline_table
 add hl,de
 ld e,(hl)
 inc hl
 ld d,(hl)
 ld a,(ix+0)
 rrca
 rrca
 rrca
 and 31
 add a,e
 ld e,a
 scf
 ret

; Sound effects are bounded (~1 ms, not a blocking music player).
; FE port bit 4 drives the beeper. Border remains black.
enemy_palettes: db 70,66,69,66  ; bright yellow, red, cyan, CROW red
old_anim_phase: db 0
anim_phase: db 0
draw_anim_phase: db 0
enemy_paint_color: db 71
old_enemy_slots: ds enemy_bytes
old_bullet_slots: ds bullet_bytes

; Render any 8-shift precomputed AND/OR sprite. Input spr_* state:
; The source pointers MUST be real assembled machine-code sprite data.
; sprite_render is in src/arcade_xor_fast.asm (GRIT ENGINE optional module).

combat_render:
 call bullet_draw_all
 call enemy_bullet_draw_all
 call wave_draw
 call player_draw
 call composite_present_new
 ld a,(ship_x)
 ld (spr_x),a
 ld a,(ship_y)
 ld (spr_y),a
 ld a,4
 ld (spr_cols),a
 ld a,28                 ; V1.2: 24 filas de nave + 4 de llama
 ld (spr_height),a
 call sprite_present
 call wave_paint_new
 call player_paint_new
 call color_shadow_present   ; Display completed palette after the initial composed frame.
 ret

player_respawn_tick:
 ld a,(player_respawn_pending)
 or a
 ret z
 ld a,(shield_invulnerable)
 cp 50
 ret nc                     ; Fighter stays away until 100 real IRQ ticks pass.
 ld a,(player_lives)
 or a
 ret z                      ; Never respawn when final life is exhausted.
 xor a
 ld (player_respawn_pending),a
 ld (enemy_bullet_slots+2),a ; V1.1: al reaparecer no queda ningun disparo
 ld (enemy_bullet_slots+5),a ; enemigo en el aire...
 ld (enemy_bullet_slots+8),a
 ld a,100                   ; ...y 2 s de invulnerabilidad (parpadeo) en vez de 1.
 ld (grace_irqs),a
 ld a,80
 ld (ship_x),a              ; Center re-entry (sprite x=80, playable 24..160).
 ret

player_draw:
 ; V2.2: 150-IRQ death lifecycle, with combat continuing behind the ESF wreck.
 ; 150..100: explosion; 99..50: no ESF; 49..1: blinking invulnerable respawn.
 ld a,(shield_invulnerable)
 cp 100
 jp nc,player_draw_death
 cp 50
 ret nc
 ld hl,grace_irqs           ; V1.1: parpadea mientras dura cualquier gracia.
 or (hl)
 jr z,player_draw_live
 ld a,(frame_index)
 and 2
 ret nz
player_draw_live:
 ld hl,player_phase_ptrs
 ; Fixed engine flames and single frame selected for maximum performance.
 ld (spr_data),hl
 ld a,(ship_x)
 ld (spr_x),a
 ld a,(ship_y)
 ld (spr_y),a
 ld a,4
 ld (spr_cols),a
 ld a,24
 ld (spr_height),a
 call sprite_render
 ; V1.2: llama de los motores, dos dibujos alternos, debajo de las toberas.
 ld hl,flame_phase_ptrs_f0
 ld a,(frame_index)
 and 2
 jr z,player_flame_ready
 ld hl,flame_phase_ptrs_f1
player_flame_ready:
 ld (spr_data),hl
 ld a,(ship_x)
 add a,8
 ld (spr_x),a
 ld a,(ship_y)
 add a,24
 ld (spr_y),a
 ld a,2
 ld (spr_cols),a
 ld a,4
 ld (spr_height),a
 call sprite_render
 ld a,(shield_frame_state)             ; Check whether field is currently active.
 cp 1                            ; 1 = protecting the ship for 3 seconds.
 ret nz                          ; No overlay when ready or recharging.
 ld hl,shield_phase_ptrs         ; 8 shifted, precomputed Z80 bitmap phases.
 ld (spr_data),hl                ; Renderer will OR the outline on existing ship.
 ld a,(ship_x)                  ; New shield is 32x32 centered around real 24x24 ESF.
 sub 4                          ; Left edge 4px outside fighter, safe at ship X>=24.
 ld (spr_x),a
 ld a,(ship_y)
 sub 6                          ; Shield outer crest above cockpit, not across it.
 ld (spr_y),a
 ld a,5                         ; Width = 32px + one phase byte.
 ld (spr_cols),a
 ld a,32
 ld (spr_height),a
 call sprite_render             ; Genuine 32x32 Z80 pre-shifted pixel sprite.
 ret                            ; The pixel compositor still never XORs the ULA screen.


; Three small 8x8 bursts make the 24x24 ESF-01 disintegrate, rather than
; instantly vanishing. All three lie inside the compositor's ship rectangle.
player_draw_death:
 ; Three distinct 24x24 bitmap frames; all pixels remain inside the old ship
 ; compositor rectangle, no dirty screen bytes or direct VRAM writes.
 ld a,(shield_invulnerable)
 cp 134
 jr c,ship_blast_second
 ld hl,ship_blast_phase_ptrs_f0
 jr ship_blast_ready
ship_blast_second:
 cp 116
 jr c,ship_blast_third
 ld hl,ship_blast_phase_ptrs_f1
 jr ship_blast_ready
ship_blast_third:
 ld hl,ship_blast_phase_ptrs_f2
ship_blast_ready:
 ld (spr_data),hl
 ld a,(ship_x)
 ld (spr_x),a
 ld a,(ship_y)
 ld (spr_y),a
 ld a,4
 ld (spr_cols),a
 ld a,24
 ld (spr_height),a
 jp sprite_render

player_keys:
 ; The fighter cannot move or activate the shield during explosion/absence.
 ld a,(shield_invulnerable)
 cp 50
 ret nc
 ; 1984 arcade: the ship cannot change Y, and A now operates the shield.
 ld a,(input_bits)     ; V1.1: O, 6 o joystick a la izquierda.
 and 2
 jp z,player_no_left   ; No movement when key released.
 ld a,(ship_x)         ; Pixel X left edge, renderer uses a shifted 24x24 sprite.
 cp 27                 ; A 3px move below 27 would cross the x=24 limit.
 jp nc,player_left_step
 ld a,24               ; Exact left limit, even when current X is 26.
 ld (ship_x),a
 jp player_no_left
player_left_step:
 sub 3                 ; Three pixel lateral step.
 ld (ship_x),a         ; Store new horizontal position.
player_no_left:
 ld a,(input_bits)    ; V1.1: P, 7 o joystick a la derecha.
 and 1
 jp z,player_no_right
 ld a,(ship_x)
 cp 158                ; Three more pixels from 158 would cross X=160.
 jp c,player_right_step
 ld a,160
 ld (ship_x),a         ; Exact final horizontal bound.
 jp player_no_right
player_right_step:
 add a,3
 ld (ship_x),a
player_no_right:
 call shield_try_activate ; A key (down) arms full 3-second shield when ready.
 ret                     ; The Y coordinate stays permanently at 152.

 ; PLAYER FIRE: edge-triggered, exactly one projectile per fresh key press.
 ; Spectrum keyboard: BC=$7FFE scans SPACE on bit 0, active low.
 ; Entry: no arguments. Exit: updates fire_held and at most one bullet slot.
 ; Clobbers: AF, BC, DE, IX, B; registers not guaranteed preserved.
 ; Keeping SPACE down does NOT spawn any more bullets; release re-arms.
player_fire:
 ld a,(shield_invulnerable)
 cp 50
 jr c,player_fire_live
 ; Keep the FIRE edge latch correct while the fighter is off-screen.
 ld a,(input_bits)
 and 16
 jr z,player_fire_release
 ld a,1
 ld (fire_held),a
 ret
player_fire_live:
 ld a,(input_bits)    ; V1.1: SPACE, 0 o fuego del joystick
 and 16
 jp z,player_fire_release ; released => reset edge detector
 ld a,(fire_held)     ; A=1 when previous sample already saw a press
 or a                ; test whether we have already fired this press
 ret nz               ; held => no new bullet, regardless of frame rate
 ld a,1              ; mark this new key-down transition as consumed
 ld (fire_held),a     ; latch stays on until SPACE is released
 ld a,(shield_state) ; Attacking is disabled during the active field.
 cp 1                ; Protected ship cannot shoot until shield expires.
 ret z               ; Consume this press to prevent delayed automatic firing.
 ld ix,bullet_slots   ; IX points to first 3-byte bullet record
 ld b,bullet_n               ; B is number of available records
player_find_slot:
 ld a,(ix+2)          ; A=active flag for this projectile
 or a                ; test active flag
 jp z,player_slot_found ; zero => free projectile slot
 ld de,3              ; DE is the size of one record
 add ix,de            ; IX advances to next projectile slot
 djnz player_find_slot ; B-- and check remaining slots
 ret                  ; slots full: do not auto-fire until release/repress
player_slot_found:
 ld a,(ship_x)        ; A is ship horizontal position in pixels
 add a,8              ; center the blaster on the interceptor
 ld (ix+0),a          ; save bullet X in free slot
 ld a,(ship_y)        ; A is ship vertical position
 sub 8                ; bullet starts 8 pixels ahead of ship
 ld (ix+1),a          ; save bullet Y
 ld (ix+2),1          ; activate bullet slot
 call sfx_shot        ; V1.2: "piu" laser
 ret                  ; done: one shot for one press
player_fire_release:
 xor a                ; A=0 denotes released key
 ld (fire_held),a     ; allow a new shot on next physical press
 ret                  ; no projectile spawned

wave_update:
 ld a,(wave_stage)
 cp 3
 jp z,boss_update           ; Boss stage driven by HP, never respawn birds.
 ld a,(card_ticks)          ; V1.1: cartel OLEADA n en curso.
 or a
 jp nz,wave_card_tick
 ld a,(wave_done)          ; Has last formation been cleared or escaped?
 or a                      ; Zero while birds still live.
 jp z,wave_update_live     ; Continue current wave.
 ; Two consecutive formations of each family: 1,1,2,2,3,3, then MOAI.
 ld a,(wave_repeat)
 or a
 jr nz,wave_advance_stage
 ld a,1
 ld (wave_repeat),a        ; First clear: repeat SAME family, not advance.
 jp wave_spawn
wave_advance_stage:
 xor a
 ld (wave_repeat),a        ; Second clear: advance to next enemy family.
 ld a,(wave_stage)
 inc a
 cp 3
 jr nz,wave_stage_store
 ld (wave_stage),a
 jp boss_start             ; Six formations lead to the MOAI.
wave_stage_store:
 ld (wave_stage),a
wave_spawn:
 jp wave_card_start         ; V1.1: primero el cartel; la formacion entra al final.
wave_spawn_now:
 ld hl,wave_initial
 ld a,(wave_stage)
 or a
 jr z,wave_spawn_copy
 ld hl,wave_hunters
 cp 1
 jr z,wave_spawn_copy
 ld hl,wave_rush
wave_spawn_copy:
 ld de,enemy_slots
 ld bc,enemy_bytes
 ldir
 ld a,(wave_stage)          ; V1.2: diez cuervos; seis en las demas oleadas
 or a
 ld a,10
 jr z,wave_spawn_count
 ld a,6
wave_spawn_count:
 ld (enemy_count),a
 xor a
 ld (wave_done),a
 ; Restart only the second-wave paired-dive scheduler when a formation begins.
 ld (hunter_pair_active),a
 ld (rush_rest_ticks),a       ; Never carry a regroup countdown into another wave.
 ld (rush_pause_active),a    ; Each kamikaze round begins immediately.
 ld (hunter_drift),a          ; Reset shared descent when new formation starts.
 ld (hunter_sway_bias),a      ; Fresh synchronized 9/8 tempo ramp.
 ld a,48                     ; Let the new formation settle before first attack.
 ld (hunter_attack_cooldown),a
wave_update_live:
 ld a,(wave_stage)
 or a
 jp z,crow_wave_update       ; Crow formation: slow descent and occasional scout.
 cp 1
 jp z,hunter_wave_update    ; Second wave: a shared slow Galaxian-style choreography.
 ld ix,enemy_slots
 ld a,(enemy_count)       ; V1.2: 10 con los cuervos, 6 en el resto
 ld b,a
wave_move_loop:
 push bc
 ld a,(ix+2)
 cp 3
 jr nz,wave_move_live
 ld a,(ix+5)             ; Countdown of small explosion animation.
 dec a
 ld (ix+5),a
 jp nz,wave_move_next
 ld (ix+2),0             ; Retire explosion without leaving image residue.
 jp wave_move_next
wave_move_live:
 or a
 jp z,wave_move_next
 cp 5                       ; V2.6: alive, resting high after a completed dive.
 jp z,wave_rush_hover
 ld a,(ix+1)              ; Y of active attacker.
 ld c,a                     ; Save old y for speed choice.
 ld a,(wave_stage)         ; 0 formation, 1 hunters, 2 kamikazes.
 inc a                      ; Per-tick dive speed 1/2/3px.
 ld b,a
 ld a,(wave_cycle)         ; Each MOAI defeated increases the tempo.
 inc a                      ; V1.1: +1 px cada DOS MOAI (a 25 ticks/s +1 por MOAI
 or a                       ; llevaba el picado a 175 px/s; ahora el tope es 125).
 rra
 add a,b
 ld b,a
 ld a,(wave_stage)
 cp 2                       ; Only third wave receives the gentle slow-down.
 jp nz,wave_speed_ready_v25
 ld a,(frame_index)
 and 3
 jp nz,wave_speed_ready_v25
 dec b                      ; One saved pixel per four ticks; still 3+cycle peak.
wave_speed_ready_v25:
 ld a,b
 add a,c
 ld (ix+1),a
 cp 167                    ; Reaching bottom triggers another attack pass.
 jr c,wave_skip_vertical
 ld a,(wave_stage)
 cp 2
 jp z,wave_rush_reenter     ; NEVER retire a surviving kamikaze after two passes.
 ld a,(ix+2)
 cp 1
 jr nz,wave_end_bird
 ld (ix+2),2               ; One return pass, still collidable.
 ld a,(ix+5)
 add a,5
 ld (ix+1),a             ; Return to upper field with staggered entry.
 jr wave_skip_vertical
wave_end_bird:
 ld (ix+2),0               ; Legacy behavior for other families only.
 jp wave_move_next
wave_rush_reenter:
 ld a,(ix+5)               ; Preserve original formation's 0..25px stagger.
 add a,5                   ; Assemble a safe high-altitude formation.
 ld (ix+1),a
 ld (ix+2),5               ; 5 = living but HOVERING, not diving or invulnerable.
 jp wave_move_next

wave_rush_hover:
 ; Two-second quiet-but-dangerous regroup: no vertical drift, gentle sway.
 ; Existing generic enemy gunner still fires from live state=5 slots.
 ld a,(frame_index)
 rrca
 rrca                      ; Slow phase: one table step per four frames.
 and 63
 ld e,a
 ld d,0
 ld hl,wave_sinus
 add hl,de
 ld a,(hl)
 rrca
 rrca
 and 15                   ; ±5px approx. very small lateral movement.
 ld b,(ix+4)
 add a,b
 ld (ix+0),a
 jp wave_move_next
wave_skip_vertical:
 ld a,(frame_index)        ; Current animation tick.
 ld c,a                     ; Save original tick index.
 ld a,(wave_stage)          ; Faster attack patterns use accelerated tables.
 or a                       ; First formation is slower and easier.
 ld a,c                     ; Restore tick without modifying flags.
 jp z,wave_stage_clock_ready ; Stage 0 uses one table step per tick.
 add a,a                    ; Stage 1/2 doubles lateral sweep speed.
 ld c,a                     ; Keep doubled index.
 ld a,(wave_stage)          ; Is it the third, most aggressive pattern?
 cp 2                       ; 2 means rapid dive patterns.
 ld a,c                     ; Restore doubled phase.
 jp nz,wave_stage_clock_ready
 add a,c                    ; Stage 2 triples lateral cycle rate.
wave_stage_clock_ready:
 ; Kamikazes steer at Y>=80, except the FIRST phase: Y>=96.
 ; V2.8.2: leave trajectory, velocity, wave timing and subsequent phases intact.
 ld a,(wave_stage)
 cp 2
 jr nz,wave_curve_motion
 ld a,(wave_cycle)
 or a
 ld b,80                    ; Normal threshold after the first MOAI.
 jr nz,wave_kamikaze_threshold
 ld b,96                    ; First phase grants more reaction time.
wave_kamikaze_threshold:
 ld a,(ix+1)
 cp b
 jr c,wave_curve_motion
 ld a,(ix+0)                ; Current enemy X, kept within 18..168.
 ld b,a
 ld a,(ship_x)
 add a,4
 cp b
 jp z,wave_move_next
 jp c,wave_steer_left
 ld a,b
 inc a
 ld (ix+0),a
 jp wave_move_next
wave_steer_left:
 ld a,b
 dec a
 cp 18
 jp c,wave_move_next
 ld (ix+0),a
 jp wave_move_next
wave_curve_motion:
 ld a,c                    ; Restore original tick for phase-table indexing.
 ld b,(ix+5)               ; Per-enemy phase offset in original array.
 add a,b                    ; Stagger all six birds.
 and 63                     ; Wave sine table wraps every 64 steps.
 ld e,a
 ld d,0
 ld hl,wave_sinus
 add hl,de
 ld a,(hl)
 ld b,(ix+4)
 add a,b
 ld (ix+0),a
wave_move_next:
 ld de,6
 add ix,de
 pop bc
 dec b
 jp nz,wave_move_loop
 call wave_rush_regroup    ; Begin real-time 100-IRQ rest ONLY once all return.
 ld hl,enemy_slots+2
 ld de,6
 ld a,(enemy_count)       ; V1.2: 10 con los cuervos, 6 en el resto
 ld b,a
wave_check_live:
 ld a,(hl)
 or a
 ret nz
 add hl,de
 djnz wave_check_live
 ld a,1
 ld (wave_done),a
 ret


; V2.6: before ANY new kamikaze pass, wait for ALL surviving birds to return.
; State 1/2 = still diving, 3 = explosion, 5 = safely regrouping high.
; Timer is 100 physical 50Hz IM2 interrupts: never count variable render ticks.
wave_rush_regroup:
 ld a,(wave_stage)
 cp 2
 ret nz
 ld ix,enemy_slots
 ld a,(enemy_count)       ; V1.2: 10 con los cuervos, 6 en el resto
 ld b,a
 xor a
 ld (rush_hover_found),a
wave_rush_scan:
 ld a,(ix+2)
 cp 1
 ret z                      ; At least one survivor is still diving.
 cp 2
 ret z
 cp 5
 jp nz,wave_rush_scan_next
 ld a,1
 ld (rush_hover_found),a
wave_rush_scan_next:
 ld de,6
 add ix,de
 djnz wave_rush_scan
 ld a,(rush_hover_found)
 or a
 ret z                      ; No living birds: normal wave-completion rules.
 ld a,(rush_pause_active)
 or a
 jp nz,wave_rush_check_clock
 ld a,1
 ld (rush_pause_active),a
 ld a,100                   ; Exactly 2s real time, regardless of frame cost.
 ld (rush_rest_ticks),a
 ret
wave_rush_check_clock:
 ld a,(rush_rest_ticks)
 or a
 ret nz                     ; Sway in place and fire until all 100 IRQs elapse.
 xor a
 ld (rush_pause_active),a
 ld ix,enemy_slots
 ld a,(enemy_count)       ; V1.2: 10 con los cuervos, 6 en el resto
 ld b,a
wave_rush_release_loop:
 ld a,(ix+2)
 cp 5
 jp nz,wave_rush_release_next
 ld (ix+2),1               ; Same survivors take the next kamikaze pass.
wave_rush_release_next:
 ld de,6
 add ix,de
 djnz wave_rush_release_loop
 ret

; ISR hook: interrupt handler already saves AF, no stack/register side effects.
rush_rest_irq_tick:
 ld a,(rush_rest_ticks)
 or a
 ret z
 dec a
 ld (rush_rest_ticks),a
 ret

; V1.3: las rutinas de los LEDs (led_*) estan ahora en src/v12_bajo.asm.
rush_rest_ticks: db 0
rush_pause_active: db 0
rush_hover_found: db 0
led_anim_clock: db 0
led_anim_phase: db 0


; WAVE TWO: six birds in synchronised choreographed movement.
; Two birds periodically leave together, DIVE towards a SINGLE SNAPSHOT of
; the ship X, fire in parallel, then return to their original formation rows.
; NO player tracking during descent: fixed targets are captured at launch.
; Zero new entity slots; all records remain six bytes as in the stable V2.3.
hunter_wave_update:
 ; Shared descent advances as a group, including while two birds are away.
 ; A returning bird can therefore rejoin the CURRENT row, not its old Y.
 ld a,(frame_index)
 and 15
 jp nz,hunter_check_pair_launch
 ld a,(hunter_sway_bias)
 inc a
 and 63
 ld (hunter_sway_bias),a    ; Additional 1/16 index rate atop former 1/2.
 ld a,(hunter_drift)
 ld b,a
 ld a,(wave_cycle)
 inc a                      ; +1..5 px every sixteen logic updates.
 add a,b
 cp 73
 jp c,hunter_drift_store
 ld a,72                    ; Row 2 ends at 104px; upper row retains spacing.
hunter_drift_store:
 ld (hunter_drift),a
hunter_check_pair_launch:
 ; Cooldown belongs to the formation scheduler, NOT the global frame index:
 ; surviving pairs reattack soon after returning, even across a 256-tick wrap.
 ld a,(hunter_attack_cooldown)
 or a
 jp z,hunter_try_launch_v25
 dec a
 ld (hunter_attack_cooldown),a
 jp hunter_after_launch_v25
hunter_try_launch_v25:
 ld a,(hunter_pair_active)
 or a
 jp nz,hunter_after_launch_v25
 call hunter_pair_launch
hunter_after_launch_v25:
 ld ix,enemy_slots
 ld a,(enemy_count)       ; V1.2: 10 con los cuervos, 6 en el resto
 ld b,a
 xor a
 ld (hunter_slot_index),a
hunter_w_loop:
 push bc
 ld a,(ix+2)
 cp 3
 jp z,hunter_w_explosion
 or a
 jp z,hunter_w_next
 cp 2
 jp z,hunter_w_dive
 cp 4
 jp z,hunter_w_return
 ; State 1 = formation. Two rows share ONE lateral AND vertical phase.
 ld c,(ix+5)               ; Immutable home row (8 or 32).
 ld a,(hunter_drift)
 add a,c
 cp 105
 jp c,hunter_w_store_y
 ld a,104
hunter_w_store_y:
 ld (ix+1),a
hunter_w_sway:
 ld a,(frame_index)
 rrca                        ; Original half-rate phase from V2.4.
 and 63
 ld b,a
 ld a,(hunter_sway_bias)
 add a,b                    ; Slight +12.5% choreography speed.
 and 63
 ld e,a
 ld d,0
 ld hl,wave_sinus
 add hl,de
 ld a,(hl)
 ld b,(ix+4)                ; Original horizontal anchor, never moved.
 add a,b
 ld (ix+0),a
 jp hunter_w_next
hunter_w_explosion:
 ld a,(ix+5)                ; Same explosion lifetime as before.
 dec a
 ld (ix+5),a
 jp nz,hunter_w_next
 ld (ix+2),0
 jp hunter_w_next
hunter_w_dive:
 ld a,(ix+1)
 add a,3                    ; Both attackers descend at the same rate.
 cp 151
 jp nc,hunter_w_turnback
 ld (ix+1),a
 ld a,(hunter_slot_index)   ; Target selected ONLY from pair's launch snapshot.
 ld b,a
 ld a,(hunter_pair_left_index)
 cp b
 jp z,hunter_w_target_left
 ld a,(hunter_target_right)
 jp hunter_w_target_ready
hunter_w_target_left:
 ld a,(hunter_target_left)
hunter_w_target_ready:
 ld c,a
 ld a,(ix+0)
 cp c
 jp z,hunter_w_next
 jp c,hunter_w_approach_right
 dec a                      ; One pixel horizontal correction per logic tick.
 ld (ix+0),a
 jp hunter_w_next
hunter_w_approach_right:
 inc a
 ld (ix+0),a
 jp hunter_w_next
hunter_w_turnback:
 ld (ix+2),4                ; Turn around, DO NOT teleport to the top.
 jp hunter_w_next
hunter_w_return:
 ld c,(ix+5)                ; Original row offset, still immutable.
 ld a,(hunter_drift)        ; Rejoin the CURRENT shared formation height.
 add a,c
 cp 105
 jp c,hunter_return_home_y_ok
 ld a,104
hunter_return_home_y_ok:
 ld c,a                     ; C=group height for the returning bird.
 ld a,(ix+1)
 cp c
 jp c,hunter_w_rejoin
 jp z,hunter_w_rejoin
 sub 4                      ; Fly back up visibly, not instant reset.
 cp c
 jp nc,hunter_w_return_y
 ld a,c
hunter_w_return_y:
 ld (ix+1),a
 jp hunter_w_next
hunter_w_rejoin:
 ld (ix+1),c
 ld (ix+2),1
 jp hunter_w_sway          ; Rejoin moving formation without a long pause.
hunter_w_next:
 ld de,6
 add ix,de
 ld a,(hunter_slot_index)
 inc a
 ld (hunter_slot_index),a
 pop bc
 dec b
 jp nz,hunter_w_loop
 call hunter_pair_fire      ; Fire from BOTH diving birds if missile slots permit.
 call hunter_pair_completion
 ld hl,enemy_slots+2
 ld de,6
 ld a,(enemy_count)       ; V1.2: 10 con los cuervos, 6 en el resto
 ld b,a
 jp wave_check_live

hunter_pair_launch:
 ld a,(hunter_pair_active)
 or a
 ret nz                   ; Never start another pair before both return/are dead.
 call hunter_pair_try_row
 ld a,(hunter_pair_active)
 or a
 ret nz                   ; Preferred row had two available birds.
 ld a,(hunter_pair_turn)    ; If one died, try the OTHER row instead.
 xor 1
 ld (hunter_pair_turn),a
 call hunter_pair_try_row   ; Attempt second row before individual fallback.
 ld a,(hunter_pair_active)
 or a
 ret nz
 jp hunter_single_launch    ; One surviving bird must still attack.
; If no complete row-pair survives, choose one of ANY six living formation
; slots (including slots 2 and 5). This is a single attack, not a new entity.
hunter_single_launch:
 ld ix,enemy_slots
 ld a,(enemy_count)       ; V1.2: 10 con los cuervos, 6 en el resto
 ld b,a
 ld c,0                     ; C is the absolute enemy slot index.
hunter_single_find:
 ld a,(ix+2)
 cp 1                       ; Only birds already back in formation can launch.
 jp z,hunter_single_ready
 ld de,6
 add ix,de
 inc c
 djnz hunter_single_find
 ret                         ; Everyone is dead/returning/exploding: no launch.
hunter_single_ready:
 ld a,c
 ld (hunter_pair_left_index),a
 ld a,(ship_x)
 add a,8
 cp 19
 jp nc,hunter_single_min_ok
 ld a,19
hunter_single_min_ok:
 cp 169
 jp c,hunter_single_max_ok
 ld a,168
hunter_single_max_ok:
 ld (hunter_target_left),a  ; Frozen target, never follow ship mid-dive.
 ld (ix+2),2
 ld a,2
 ld (hunter_pair_active),a ; Mode 2: one independent attack.
 ret

hunter_pair_try_row:
 ld a,(hunter_pair_turn)
 or a
 jp nz,hunter_pair_lower
 ld iy,enemy_slots          ; Upper pair: slots 0 and 1.
 xor a
 jp hunter_pair_ready
hunter_pair_lower:
 ld iy,enemy_slots+18       ; Lower pair: slots 3 and 4.
 ld a,3
hunter_pair_ready:
 ld (hunter_pair_left_index),a
 ld a,(iy+2)
 cp 1
 ret nz                   ; Don't revive previously destroyed enemies.
 ld de,6
 add iy,de
 ld a,(iy+2)
 cp 1
 ret nz                   ; Two live birds required for parallel attack.
 ld a,(ship_x)
 cp 40
 jp nc,hunter_target_min_ok
 ld a,40
hunter_target_min_ok:
 cp 145
 jp c,hunter_target_max_ok
 ld a,144
hunter_target_max_ok:
 sub 10
 ld (hunter_target_left),a
 add a,26                   ; Right-hand wingman follows at fixed 26px separation.
 ld (hunter_target_right),a
 ld (iy+2),2               ; Right attacker now diving.
 ld de,6
 ld ix,enemy_slots
 ld a,(hunter_pair_left_index)
 or a
 jp z,hunter_left_slot_ready
 ld ix,enemy_slots+18
hunter_left_slot_ready:
 ld (ix+2),2               ; Left attacker now diving.
 ld a,1
 ld (hunter_pair_active),a
 ld a,(hunter_pair_turn)
 xor 1
 ld (hunter_pair_turn),a    ; Alternate which ROW attacks on next run.
 ret

hunter_pair_fire:
 ld a,(hunter_pair_active)
 or a
 ret z
 ld a,(frame_index)
 and 31                   ; V1.1: 1,28 s entre rafagas (a 25 ticks/s).
 cp 16
 ret nz                   ; Short volleys, both on the SAME beat.
 ld a,(hunter_pair_active)
 cp 2
 jp z,hunter_single_fire
 ld iy,enemy_slots
 ld a,(hunter_pair_left_index)
 or a
 jp z,hunter_fire_left_ready
 ld iy,enemy_slots+18
hunter_fire_left_ready:
 call hunter_fire_one
 ld de,6
 add iy,de
 jp hunter_fire_one        ; Both share the saved target; never home in mid-dive.

hunter_single_fire:
 ld iy,enemy_slots
 ld a,(hunter_pair_left_index)
 or a
 jp z,hunter_single_fire_ready
 ld b,a
 ld de,6
hunter_single_fire_slot:
 add iy,de
 djnz hunter_single_fire_slot
hunter_single_fire_ready:
 jp hunter_fire_one          ; Same 3-bullet limit and beeper as any other bird.

hunter_fire_one:
 ld a,(iy+2)
 cp 2
 ret nz
 ld ix,enemy_bullet_slots
 ld b,3
hunter_fire_find:
 ld a,(ix+2)
 or a
 jp z,hunter_fire_spawn
 ld de,3
 add ix,de
 djnz hunter_fire_find
 ret                       ; Preserve maximum three simultaneous projectiles.
hunter_fire_spawn:
 ld a,(iy+0)
 add a,7
 ld (ix+0),a
 ld a,(iy+1)
 add a,15
 cp 109                    ; V1.1: igual que el resto: disparo siempre esquivable.
 ret nc
 ld (ix+1),a
 ld (ix+2),1
 call sfx_enemy_fire
 ret

hunter_pair_completion:
 ld a,(hunter_pair_active)
 or a
 ret z
 cp 2
 jp z,hunter_single_completion
 ld ix,enemy_slots
 ld a,(hunter_pair_left_index)
 or a
 jp z,hunter_left_check
 ld ix,enemy_slots+18
hunter_left_check:
 ld a,(ix+2)
 cp 2
 ret z
 cp 4
 ret z
 ld de,6
 add ix,de
 ld a,(ix+2)
 cp 2
 ret z
 cp 4
 ret z
 xor a
 ld (hunter_pair_active),a
 ld a,16                     ; Brief beat before next attack, never 128-tick idle.
 ld (hunter_attack_cooldown),a
 ret
hunter_single_completion:
 ld ix,enemy_slots
 ld a,(hunter_pair_left_index)
 or a
 jp z,hunter_single_completion_check
 ld b,a
 ld de,6
hunter_single_complete_slot:
 add ix,de
 djnz hunter_single_complete_slot
hunter_single_completion_check:
 ld a,(ix+2)
 cp 2
 ret z
 cp 4
 ret z
 xor a
 ld (hunter_pair_active),a
 ld a,12                     ; Solo bird makes the surviving formation threatening.
 ld (hunter_attack_cooldown),a
 ret

; CROW / WAVE ONE: all six 8x8 invaders glide as a coordinated formation.
; A 1px descent occurs every 64 logical updates, +1 per completed MOAI loop.
; A single scout can break away every 128 ticks, dive, then fly back up.
; Enemy record [X,Y,state=1 formation/2 dive/4 return, type=3,baseX,homeY].
crow_wave_update:
 ld a,(frame_index)
 and 127
 cp 96                      ; Let the player read the formation before first scout.
 jp nz,crow_wave_movement
 ld ix,enemy_slots
 ld a,(enemy_count)       ; V1.2: 10 con los cuervos, 6 en el resto
 ld b,a
crow_select_scout:
 ld a,(ix+2)
 cp 1
 jp z,crow_scout_selected
 ld de,6
 add ix,de
 djnz crow_select_scout
 jp crow_wave_movement
crow_scout_selected:
 ld (ix+2),2               ; Choose the first available live formation bird.
crow_wave_movement:
 ld ix,enemy_slots
 ld a,(enemy_count)       ; V1.2: 10 con los cuervos, 6 en el resto
 ld b,a
crow_wave_loop:
 push bc
 ld a,(ix+2)
 cp 3
 jp z,crow_explosion_tick
 or a
 jp z,crow_wave_next
 cp 2
 jp z,crow_scout_dive
 cp 4
 jp z,crow_scout_return
 ; State 1: deliberate 1980s Space Invaders style movement.
 ld a,(frame_index)
 and 63
 jp nz,crow_move_across
 ld a,(ix+1)
 cp 75
 jp nc,crow_move_across
 ld b,a
 ld a,(wave_cycle)
 inc a
 add a,b
 ld (ix+1),a
crow_move_across:
 ld a,(frame_index)
 rrca
 rrca
 and 63                    ; Shared lateral phase: move as one formation.
 ld e,a
 ld d,0
 ld hl,wave_sinus
 add hl,de
 ld a,(hl)
 ld b,a
 ld a,(ix+4)              ; Original X anchor in pixel coordinates.
 add a,b
 ld (ix+0),a
 jp crow_wave_next
crow_scout_dive:
 ld a,(ix+1)
 add a,2                    ; Slow, deliberate exploratory dive.
 cp 169
 jp nc,crow_scout_turn
 ld (ix+1),a
 ld a,(ix+0)
 ld b,a
 ld a,(ship_x)
 add a,8
 cp b
 jp z,crow_wave_next
 jp c,crow_scout_left
 ld a,b
 inc a
 ld (ix+0),a
 jp crow_wave_next
crow_scout_left:
 ld a,b
 dec a
 cp 19
 jp c,crow_wave_next
 ld (ix+0),a
 jp crow_wave_next
crow_scout_turn:
 ld (ix+2),4              ; Return trip never teleports over the player.
 jp crow_wave_next
crow_scout_return:
 ld a,(ix+1)
 sub 3
 ; FINAL 1.0.1: con Y<3 la resta daba la vuelta (253..255) y el Crow se
 ; pintaba fuera de la tabla de 192 lineas: el compositor escribia sobre el
 ; propio codigo (call $8635 -> call $1035) y el Spectrum se reseteaba o se
 ; colgaba. Si la subida se pasa del borde, el Crow aterriza en su sitio.
 jp c,crow_scout_home
 ld b,a
 ld a,(ix+5)              ; Initial home Y for this Crow.
 cp b
 jp nc,crow_scout_joins
 ld a,b
 ld (ix+1),a
 jp crow_wave_next
crow_scout_home:
 ld a,(ix+5)
crow_scout_joins:
 ld (ix+1),a
 ld (ix+2),1
 jp crow_wave_next
crow_explosion_tick:
 ld a,(ix+5)              ; Normal three-step explosion decay.
 dec a
 ld (ix+5),a
 jp nz,crow_wave_next
 ld (ix+2),0
crow_wave_next:
 ld de,6
 add ix,de
 pop bc
 dec b
 jp nz,crow_wave_loop
 ld hl,enemy_slots+2
 ld de,6
 ld a,(enemy_count)       ; V1.2: 10 con los cuervos, 6 en el resto
 ld b,a
 jp wave_check_live

wave_draw:
 ld ix,enemy_slots
 ld a,(anim_phase)
 ld (draw_anim_phase),a
 ld a,(enemy_count)       ; V1.2: 10 con los cuervos, 6 en el resto
 ld b,a
wave_draw_loop:
 push bc
 call enemy_draw_ix
 ld de,6
 add ix,de
 pop bc
 djnz wave_draw_loop
 ret

enemy_draw_ix:
 ld a,(ix+2)
 or a
 ret z
 cp 3
 jp z,enemy_draw_explosion
 ld a,(ix+3)
 cp 3
 jp z,enemy_kind_crow
 or a
 jp z,enemy_kind_falcon
 cp 1
 jp z,enemy_kind_raptor
 ld hl,enemy_drone_phase_ptrs
 ld a,(draw_anim_phase)
 or a
 jp z,enemy_kind_ready
 ld hl,enemy_drone_phase_ptrs_f1
 jp enemy_kind_ready
enemy_kind_raptor:
 ld hl,enemy_blade_phase_ptrs
 ld a,(draw_anim_phase)
 or a
 jp z,enemy_kind_ready
 ld hl,enemy_blade_phase_ptrs_f1
 jp enemy_kind_ready
enemy_kind_falcon:
 ld hl,enemy_needle_phase_ptrs
 ld a,(draw_anim_phase)
 or a
 jp z,enemy_kind_ready
 ld hl,enemy_needle_phase_ptrs_f1
 jp enemy_kind_ready       ; Prevent fall-through into explosion renderer!
enemy_kind_crow:
 ; Precisely 8x8 red Crow, centered in its original 16x16 collision cell.
 ld hl,crow_phase_ptrs
 ld a,(draw_anim_phase)
 or a
 jr z,crow_sprite_ready
 ld hl,crow_phase_ptrs_f1
crow_sprite_ready:
 ld (spr_data),hl
 ld a,(ix+0)
 add a,4
 ld (spr_x),a
 ld a,(ix+1)
 add a,4
 ld (spr_y),a
 ld a,2
 ld (spr_cols),a
 ld a,8
 ld (spr_height),a
 jp sprite_render
enemy_draw_explosion:
 ; V1.2: explosion de 16x16 en tres tiempos (destello, estallido, chispas).
 ; Las fases desplazadas se generan al arrancar en $5B00 (explosion_shift_init).
 ld a,(ix+5)
 ld hl,explosion_phase_ptrs_f0
 cp 5
 jp nc,enemy_kind_ready
 ld hl,explosion_phase_ptrs_f1
 cp 3
 jp nc,enemy_kind_ready
 ld hl,explosion_phase_ptrs_f2
enemy_kind_ready:
 ld (spr_data),hl
 ld a,(ix+0)
 ld (spr_x),a
 ld a,(ix+1)
 ld (spr_y),a
 ld a,3
 ld (spr_cols),a
 ld a,16
 ld (spr_height),a
 call sprite_render
 ret

bullet_update:
 ld ix,bullet_slots
 ld b,bullet_n
bullet_update_loop:
 push bc
 ld a,(ix+2)
 or a
 jp z,bullet_next
 ld a,(ix+1)
 cp 12
 jp nc,bullet_continue
 ld (ix+2),0
 jp bullet_next
bullet_continue:
 sub 12                  ; V1.2: 12 px por tick (antes 9); maximo 2 balas.
 ld (ix+1),a
 ld a,(wave_stage)
 cp 3
 jp z,bullet_check_boss
 ld iy,enemy_slots
 ld a,(enemy_count)       ; V1.2: 10 con los cuervos, 6 en el resto
 ld b,a
bullet_check_enemy:
 push bc
 ld a,(iy+2)
 cp 3
 jp z,bullet_no_hit     ; Explosion no longer collidable.
 or a
 jp z,bullet_no_hit
 ld b,(iy+0)
 ld a,(ix+0)
 sub b
 cp 16
 jp nc,bullet_no_hit
 ld b,(iy+1)
 ld a,(ix+1)
 sub b
 cp 16
 jp nc,bullet_no_hit
 ld (iy+2),3             ; 3-tick explosion state, prevents double hits.
 ld (iy+5),6             ; Six visible blast updates (~0.25s at 25Hz).
 ld (ix+2),0
 call score_add_kill     ; V1.1: marcador de 16 bits y vida extra.
 call sfx_explode
 jp bullet_check_done
bullet_no_hit:
 ld de,6
 add iy,de
 pop bc
 dec b
 jp nz,bullet_check_enemy
 jp bullet_next
bullet_check_done:
 pop bc
 jp bullet_next
; During the MOAI, a direct hit on its 48x88 portrait costs one HP.
; All coordinates are in native pixel space, no screen write here.
bullet_check_boss:
 ld a,(ix+1)
 cp 96
 jp nc,bullet_next
 ld a,(ix+0)
 cp 72
 jp c,bullet_next
 cp 120
 jp nc,bullet_next
 ld (ix+2),0             ; Consume the shot on boss impact.
 ld a,(boss_hp)
 or a
 jp z,bullet_next
 dec a
 ld (boss_hp),a
 push af
 call boss_damage_check     ; V1.2: grietas al bajar a 12, 6 y 3.
 pop af
 jr nz,boss_bullet_hit_score
 ; MOAI defeated: neutralize all remaining eye shots immediately.
 xor a
 ld (enemy_bullet_slots+2),a
 ld (enemy_bullet_slots+5),a
 ld (enemy_bullet_slots+8),a
boss_bullet_hit_score:
 call score_add_kill
 call sfx_boss_hit
 jp bullet_next
bullet_next:
 ld de,3
 add ix,de
 pop bc
 dec b
 jp nz,bullet_update_loop
 ret

bullet_draw_all:
 ld ix,bullet_slots
 ld b,bullet_n
bullet_draw_loop:
 push bc
 call bullet_draw_ix
 ld de,3
 add ix,de
 pop bc
 djnz bullet_draw_loop
 ret
bullet_draw_ix:
 ; V1.1: dibujo OR directo de 2x4 bytes (mismo resultado que sprite_render
 ; con shot_phase_ptrs, sin pasar por las variables spr_*).
 ld bc,shot_phase_ptrs       ; V1.2: haz propio; los enemigos usan el rombo
bullet_draw_with:
 call bullet_rect_dest       ; DE = pantalla; NC = inactivo o no cabe
 ret nc
 ld a,(ix+0)
 and 7
 add a,a
 ld l,a
 ld h,0
 add hl,bc
 ld a,(hl)
 inc hl
 ld h,(hl)
 ld l,a                      ; HL = fase desplazada del proyectil
 ld a,d
 add a,128
 ld d,a                      ; DE = imagen de trabajo
 ld b,4
 jp sprite_row2

 ; Four rightmost score digits: kills x 10, up to 2550 without overflow.
 ; This runs only on a kill and writes the *native* HUD bitmap in screen RAM.
; V1.2: score_draw esta en src/v12_hud.asm (cifras gruesas + record).
; Six original GRIT-style 5px digits, horizontal pixel positions 9,17,...49.
; Pixel bits 6..2 align within tile from x%8==1, no border touching.
digit_bitmaps:
 db 56,76,84,84,84,100,56    ; 0 from original bitmap source
 db 16,48,16,16,16,16,56     ; 1
 db 56,68,4,24,32,64,124    ; 2
 db 56,68,4,24,4,68,56      ; 3
 db 8,24,40,72,124,8,8      ; 4
 db 124,64,64,120,4,68,56   ; 5
 db 56,64,64,120,68,68,56   ; 6
 db 124,4,8,16,16,16,16     ; 7
 db 56,68,68,56,68,68,56    ; 8
 db 56,68,68,60,4,4,56      ; 9

; x,y,active,type,base_x,phase for one coordinated Galaga/Phoenix wave.
wave_initial:
 ; V1.2: diez cuervos en dos filas de cinco, escalonados, moviendose a la vez.
 db 34,0,1,3,16,0
 db 64,6,1,3,46,6
 db 94,0,1,3,76,0
 db 124,6,1,3,106,6
 db 154,0,1,3,136,0
 db 34,22,1,3,16,22
 db 64,28,1,3,46,28
 db 94,22,1,3,76,22
 db 124,28,1,3,106,28
 db 154,22,1,3,136,22

; Second and third waves have distinct positions, families and phase offsets.
wave_hunters:
 ; Two close staggered rows, all share the same 64-step side-to-side sway.
 db 38,8,1,1,20,8
 db 88,8,1,0,70,8
 db 144,8,1,1,126,8
 db 38,32,1,2,20,32
 db 88,32,1,1,70,32
 db 144,32,1,2,126,32
 db 0,0,0,0,0,0
 db 0,0,0,0,0,0
 db 0,0,0,0,0,0
 db 0,0,0,0,0,0   ; V1.2: huecos 7-10 vacios en esta oleada
wave_rush:
 db 24,11,1,2,18,0
 db 54,33,1,1,36,5
 db 87,10,1,1,69,10
 db 114,45,1,0,96,15
 db 144,20,1,2,126,20
 db 158,63,1,1,140,25
 db 0,0,0,0,0,0
 db 0,0,0,0,0,0
 db 0,0,0,0,0,0
 db 0,0,0,0,0,0   ; V1.2: huecos 7-10 vacios en esta oleada
wave_cycle: db 0
wave_repeat: db 0         ; 0=first formation, 1=repeat before advancing.
hunter_pair_active: db 0
hunter_drift: db 0         ; Shared vertical position of both Galaxian rows.
hunter_pair_turn: db 0
hunter_pair_left_index: db 0
hunter_attack_cooldown: db 0
hunter_sway_bias: db 0
hunter_target_left: db 0
hunter_target_right: db 0
hunter_slot_index: db 0
ship_old_x: db 80
ship_old_y: db 152
ship_new_x: db 80
ship_new_y: db 152
ship_x: db 80
ship_y: db 152
fire_held: db 0 ; edge detector for SPACE, one shot per press
player_respawn_pending: db 0 ; once-only center re-entry after the death pause
kills: db 0
wave_done: db 0
wave_stage: db 0             ; 0 formation, 1 fast hunters, 2 kamikaze sweeps.
; spr_* scratch is allocated by arcade_xor_fast.asm
enemy_slots: ds enemy_bytes
bullet_slots: ds bullet_bytes
