; HALCONES ESTELARES / ARCADE RULES V1.8 — Standard Z80, ORG inherited $8000.
; Original custom routines. No undocumented opcodes. Calibrated game rules:
;   O/P horizontal only, A shield by press, SPACE single fire per press.
;   Shield ACTIVE 150 IRQ (3s), then CHARGE 300 IRQ (6s); 50Hz IM2 source.
; Timers are independent of the graphics renderer and protected by the ISR.
; FIELD state: 0 READY, 1 ACTIVE, 2 RECHARGING.
; Enemies shot into three independent projectile slots, no overwrites of player shots.

shield_init:
 xor a                       ; A=0 means no active shield or edge-latch.
 ld (shield_state),a         ; Start with shield ready.
 ld (shield_key_held),a      ; First A press counts as a fresh edge.
 ld (shield_previous_state),a ; No field on the prior visible frame.
 ld (shield_frame_state),a   ; Renderer snapshot begins unprotected.
 ld (shield_timer),a         ; Clear countdown low byte.
 ld (shield_timer+1),a       ; Clear countdown high byte.
 ld (shield_charge_frame),a  ; Secondary one-second counter.
 ld (shield_invulnerable),a  ; No grace period needed at boot.
 ld (shield_ready_pending),a ; No pending ready chirp at boot.
 ld (shot_spawn_turn),a      ; Reset selection of enemy shooter.
 ld (lives_displayed),a      ; Force drawing accurate lives on first tick.
 ld a,3                     ; Arcade-style three lives on starting.
 ld (player_lives),a         ; Record lives independent from HUD.
 ld a,8                     ; Eight green bar segments mean READY.
 ld (shield_meter),a         ; Meter starts full.
 ld (shield_meter_displayed),a ; HUD already contains the full bar.
 ld hl,enemy_bullet_slots    ; Three records of 3 bytes each.
 ld de,enemy_bullet_slots+1   ; Fill forward from zero first byte.
 ld bc,8                     ; Eight remaining bytes to clear.
 xor a                       ; Put zero in first slot byte.
 ld (hl),a                   ; Initialize all slots inactive.
 ldir                        ; Replicate zero across 9 bytes.
 ret                         ; Return to combat_init with all timers ready.

; Called from IM2. Destroys AF,HL; caller saves them. Never touches graphics.
shield_irq_tick:
 ld a,(shield_invulnerable)  ; Read temporary safety after losing a life.
 or a                        ; Skip zero countdown.
 jr z,shield_irq_state       ; No respawn invulnerability.
 dec a                       ; Count a real 1/50-second hardware tick.
 ld (shield_invulnerable),a  ; Store remaining grace period.
shield_irq_state:
 ld a,(shield_state)         ; Read phase byte.
 or a                        ; Zero means ready; no timer work.
 ret z                       ; Nothing further to count.
 ld hl,(shield_timer)        ; HL=remaining 50Hz ticks, 1..300.
 dec hl                      ; Consume exactly one IRQ tick.
 ld (shield_timer),hl        ; Store full 16-bit remaining interval.
 ld a,(shield_state)         ; Read current shield phase.
 cp 2                        ; 2 means six-second recharge.
 jr nz,shield_irq_expiry     ; Active shield does not build green meter.
 ; 6s / 8 original HUD segments = 37.5 IRQ each. Alternate 38/37 IRQ.
 ; Even meter (0,2,4,6) needs 38; odd meter (1,3,5,7) needs 37.
 ; Only AF/HL are clobbered, as required by the IM2 wrapper.
 ld a,(shield_meter)
 and 1
 jr nz,shield_irq_segment_37
 ld a,(shield_charge_frame)
 inc a
 cp 38
 jr c,shield_irq_store_sub
 jr shield_irq_segment_done
shield_irq_segment_37:
 ld a,(shield_charge_frame)
 inc a
 cp 37
 jr c,shield_irq_store_sub
shield_irq_segment_done:
 xor a
 ld (shield_charge_frame),a
 ld a,(shield_meter)         ; Read 0..8 green segments.
 inc a
 ld (shield_meter),a         ; Renderer notices on next game update.
 jr shield_irq_expiry
shield_irq_store_sub:
 ld (shield_charge_frame),a  ; Save current partial segment tick count.
shield_irq_expiry:
 ld a,h                      ; HL remaining countdown high byte.
 or l                        ; Z only when both high and low are zero.
 ret nz                      ; Continue the current phase.
 ld a,(shield_state)         ; Which timer just expired?
 cp 1                        ; Active three-second phase completed?
 jr nz,shield_irq_ready      ; Otherwise recharge timer finished.
 ld hl,300                   ; 300*20ms = six seconds.
 ld (shield_timer),hl        ; Arm recharge countdown.
 ld a,2                      ; State now RECHARGING.
 ld (shield_state),a         ; Disable contact attack and invulnerability.
 xor a                       ; Reset recharge segment subcounter.
 ld (shield_charge_frame),a  ; First of eight original HUD segments.
 ret                         ; Return without touching visible screen.
shield_irq_ready:
 ld a,1
 ld (shield_ready_pending),a ; Notify game loop without sound inside ISR.
 xor a                       ; READY state once all 300 IRQ ticks expire.
 ld (shield_state),a         ; Enable the next A key activation.
 ret                         ; The meter was just filled to eight segments.

; Test A down: bit0 from ULA row FD (Q/A). Only press EDGE activates field.
shield_try_activate:
 ld a,(input_bits)          ; V1.1: A/Q, 8/9 o joystick arriba/abajo.
 and 12
 jp z,shield_key_release    ; Release resets edge latch.
 ld a,(shield_key_held)      ; Is A still being held from a prior check?
 or a                       ; Z = new key press.
 ret nz                     ; Held key cannot reactivate by itself.
 ld a,1                     ; Mark this keypress as consumed.
 ld (shield_key_held),a      ; Keep latch until actual release.
 ld a,(shield_state)         ; Current shield phase.
 or a                       ; Only ready (0) is accepted.
 ret nz                     ; No shield on partial recharge or during active.
 di                          ; Atomic update relative to 50Hz IM2 IRQ.
 ld hl,150                  ; 150*20ms = three seconds.
 ld (shield_timer),hl        ; Start 3s protection countdown.
 ld a,1                     ; New state ACTIVE.
 ld (shield_state),a         ; Commit protection before interrupts resume.
 xor a                       ; 0 segments, entire bar consumed.
 ld (shield_meter),a        ; HUD empties on following presentation.
 ei                          ; Restore IM2 maskable IRQs.
 call sfx_shield_on        ; V1.2: "vuuum" y zumbido mientras dura.
 ret                         ; Field activated with one physical press.
shield_key_release:
 xor a                       ; Unlatch key once physically released.
 ld (shield_key_held),a      ; Next press can activate when charged.
 ret                         ; Return without changing shield state.

; Active shield destroys any touching bird, for score +10 like shot.
; Enemies are 16x16, player is 24x24 fixed y=152. Tests are rectangle intersections.
shield_collisions:
 ld a,(shield_state)         ; State check at current logic tick.
 cp 1                        ; Only active field has collision attack.
 ret nz                      ; Unprotected or recharging do not destroy.
 ld ix,enemy_slots          ; Iterate six enemy records, 6 bytes each.
 ld a,(enemy_count)       ; V1.2: 10 con los cuervos, 6 en el resto
 ld b,a
shield_bird_loop:
 push bc                      ; Save loop counter across scoring.
 ld a,(ix+2)                ; Is this enemy alive (not explosion)?
 cp 3
 jr z,shield_bird_next
 or a                        ; 0 means empty/dead.
 jr z,shield_bird_next       ; Skip dead records.
 ld a,(ix+1)                ; Enemy top Y.
 cp 176                      ; Enemy entirely below player after Y=176.
 jr nc,shield_bird_next      ; No intersection with 152..176.
 cp 137                      ; Need enemy bottom to reach 152 (137+16=153).
 jr c,shield_bird_next       ; Too high to contact shield.
 ld a,(ix+0)                ; Enemy left X.
 ld c,a                     ; Save left X.
 ld a,(ship_x)              ; Player left X.
 add a,24                   ; Player right X (exclusive).
 cp c                        ; Enemy left is right of ship boundary?
 jr c,shield_bird_next      ; No horizontal overlap.
 ld a,c                     ; Enemy X.
 add a,16                   ; Enemy right boundary.
 ld c,a                     ; Save enemy right.
 ld a,(ship_x)              ; Player left boundary.
 cp c                        ; Player is to right of enemy?
 jr nc,shield_bird_next     ; No intersection.
 ld (ix+2),3                ; Replace bird with short explosion.
 ld (ix+5),6                ; Six-update explosion, visible to the player.
 call sfx_explode
 call score_add_kill         ; V1.1: marcador de 16 bits y vida extra.
shield_bird_next:
 ld de,6                     ; Size of enemy record.
 add ix,de                   ; Next bird.
 pop bc                      ; Restore outer count.
 djnz shield_bird_loop       ; Check all birds (multiple kills per charge).
 ret                         ; Enemy bullets handled by their own update routine.

; Enemy projectiles: three 3-byte slots, moving DOWN by 5px per game update.
; Spawn once every 32 game ticks from an existing bird; limited to 3 simultaneous.
enemy_bullet_update:
 ld ix,enemy_bullet_slots    ; IX=current downward shot record.
 ld b,3                      ; Three independent enemy bullets maximum.
enemy_bullet_move_loop:
 push bc                      ; Protect outer counter.
 ld a,(ix+2)                ; 0 means unused slot.
 or a                        ; Active?
 jr z,enemy_bullet_next      ; No movement for empty slot.
 ld a,(ix+1)                ; Current Y pixel coordinate.
 add a,5                    ; Downward projectile velocity.
 cp 185                      ; Bottom cutoff before 4px sprite leaves view.
 jr nc,enemy_bullet_remove   ; Deactivate and restore old footprint.
 ld (ix+1),a                ; Commit new vertical position.
 ; V1.1: caja de impacto con la silueta del ESF, no el cuadrado de 24x24:
 ; morro estrecho (x+9..x+14) en las 13 primeras filas, alas (x+3..x+20) debajo.
 add a,3                    ; Fila inferior del proyectil.
 ld b,a
 ld a,(ship_y)
 ld c,a
 ld a,b
 sub c                      ; A = fila de la nave que toca el proyectil.
 jr c,enemy_bullet_next     ; Aun por encima del morro.
 cp 27
 jr nc,enemy_bullet_next    ; Ya por debajo de la nave.
 ld de,0x0f09               ; D = borde derecho (exclusivo), E = izquierdo.
 cp 13
 jr c,eb_hitbox
 ld de,0x1503
eb_hitbox:
 ld a,(ship_x)
 add a,e
 ld e,a
 ld a,(ship_x)
 add a,d
 ld d,a
 ld a,(ix+0)                ; Proyectil: x .. x+2.
 cp d
 jr nc,enemy_bullet_next
 add a,3
 cp e
 jr c,enemy_bullet_next
 jr z,enemy_bullet_next
 ld (ix+2),0                ; Projectile removed on collision.
 ld a,(shield_state)         ; Does shield protect the player?
 cp 1                        ; Active field neutralizes the projectile.
 jr z,enemy_bullet_next      ; Protected ship survives.
 call player_take_hit        ; Unprotected player loses one life.
 jr enemy_bullet_next        ; Continue processing other shots.
enemy_bullet_remove:
 ld (ix+2),0                 ; Shot has left the viewport.
enemy_bullet_next:
 ld de,3                     ; Advance one bullet record.
 add ix,de                   ; IX=next slot.
 pop bc                      ; Restore bullet counter.
 djnz enemy_bullet_move_loop ; Process three shots.
 ; V1.1: cadencia por temporizador en ticks de 25/s (antes mascaras de
 ; frame_index a un ritmo que variaba entre 12 y 17 ticks/s segun la escena).
 ld a,(wave_stage)
 cp 3
 jr nz,enemy_fire_countdown
 ld a,(boss_hp)            ; No laser fire during MOAI defeat sequence.
 or a
 ret z
enemy_fire_countdown:
 ld a,(enemy_fire_cd)
 or a
 jr z,enemy_fire_due
 dec a
 ld (enemy_fire_cd),a
 ret
enemy_fire_due:
 ld a,(wave_stage)
 ld e,a
 ld d,0
 ld hl,fire_period_first
 ld a,(wave_cycle)
 or a
 jr z,enemy_fire_period
 ld hl,fire_period_later
enemy_fire_period:
 add hl,de
 ld a,(wave_cycle)          ; -3 ticks por cada MOAI derrotado a partir del segundo.
 or a
 jr z,enemy_fire_period_ok
 dec a
 ld b,a
 add a,a
 add a,b
 ld b,a
 ld a,(hl)
 sub b
 jr enemy_fire_period_set
enemy_fire_period_ok:
 ld a,(hl)
enemy_fire_period_set:
 ld (enemy_fire_cd),a
 ld ix,enemy_bullet_slots    ; Find first inactive slot.
 ld b,3                      ; Search up to three.
enemy_bullet_find:
 ld a,(ix+2)                ; Active flag.
 or a                        ; Zero = free.
 jr z,enemy_bullet_free      ; Slot found.
 ld de,3                     ; Record size.
 add ix,de                   ; Next projectile slot.
 djnz enemy_bullet_find      ; Check remaining slots.
 ret                         ; Maximum simultaneous enemy fire reached.
enemy_bullet_free:
 ld a,(wave_stage)
 cp 3
 jp z,boss_bullet_spawn
 ld iy,enemy_slots          ; Source of six records (each six bytes).
 ld a,(shot_spawn_turn)     ; Next preferred gunner 0..5.
 inc a
 ld hl,enemy_count
 cp (hl)
 jr c,enemy_shooter_turn_ok
 xor a
enemy_shooter_turn_ok:
 ld (shot_spawn_turn),a
 or a
 jr z,enemy_shooter_start
 ld b,a
 ld de,6
enemy_shooter_offset:
 add iy,de
 djnz enemy_shooter_offset
enemy_shooter_start:
 ld hl,enemy_count        ; V1.2: 10 con los cuervos, 6 en el resto
 ld b,(hl)
 ld (shot_shooter_index),a
enemy_bullet_bird:
 ld a,(iy+2)                ; Active enemy?
 cp 3
 jr z,enemy_bullet_shooter_next
 or a                        ; Z means dead.
 jr nz,enemy_bullet_spawn    ; Live shooter found.
enemy_bullet_shooter_next:
 ld a,(shot_shooter_index)
 inc a
 ld hl,enemy_count
 cp (hl)
 jr c,enemy_shooter_no_wrap
 xor a
 ld iy,enemy_slots          ; Wrap back to the first record.
 jr enemy_shooter_advance
enemy_shooter_no_wrap:
 ld de,6
 add iy,de
enemy_shooter_advance:
 ld (shot_shooter_index),a
 djnz enemy_bullet_bird      ; Search all slots.
 ret                         ; No active enemy available to shoot.
enemy_bullet_spawn:
 ld a,(iy+0)                ; Bird X.
 add a,7                    ; Approximate beak/muzzle horizontal center.
 ld (ix+0),a                ; New bullet X.
 ld a,(iy+1)                ; Bird Y.
 add a,15                   ; Spawn directly underneath 16px enemy.
 cp 109                      ; V1.1: nunca a menos de 43px del morro: siempre esquivable.
 ret nc
 ld (ix+1),a                ; New downward shot Y.
 ld (ix+2),1                 ; Activate this free projectile slot.
 call sfx_enemy_fire
 ret                         ; Render it in the compositing pass.

boss_bullet_spawn:
 ld a,(boss_eye)            ; V1.1: un ojo y luego el otro, siempre.
 xor 1
 ld (boss_eye),a
 ld a,85                   ; MOAI left eye.
 jr z,boss_bullet_left
 ld a,109                  ; MOAI right eye.
boss_bullet_left:
 ld (ix+0),a
 ld a,48                   ; Shots leave the mask well above our ESF.
 ld (ix+1),a
 ld (ix+2),1
 call sfx_boss_fire
 jp mouth_open              ; V1.2: el MOAI abre la boca al disparar.

; Three active enemy bullets are OR-rendered by a pre-shifted 4px missile shape.
enemy_bullet_draw_all:
 ld ix,enemy_bullet_slots    ; Z80 pointer to enemy projectile records.
 ld b,3                      ; Render three records maximum.
enemy_bullet_draw_loop:
 push bc                      ; Sprite renderer destroys BC.
 ld bc,enemy_shot_phase_ptrs ; V1.2: rombo de plasma, distinto del haz propio.
 call bullet_draw_with
enemy_bullet_draw_next:
 ld de,3                     ; Advance to next projectile.
 add ix,de                   ; IX=next record.
 pop bc                      ; Restore outer count.
 djnz enemy_bullet_draw_loop ; Repeat for all slots.
 ret                         ; Finished.

; Unprotected contact with any bird in player row causes death (not shield).
ship_hit_collisions:
 ld a,(shield_state)         ; Shield active?
 cp 1                        ; 1 means complete protection.
 ret z                       ; Field cancels body collisions.
 ld a,(shield_invulnerable)  ; Respawn grace period from 50Hz interrupt.
 ld hl,grace_irqs           ; V1.1: mas la gracia al reaparecer.
 or (hl)
 ret nz                      ; Temporarily invulnerable after hit.
 ld ix,enemy_slots          ; Scan live birds.
 ld a,(enemy_count)       ; V1.2: 10 con los cuervos, 6 en el resto
 ld b,a
ship_hit_bird_loop:
 push bc                      ; Preserve loop counter.
 ld a,(ix+2)                ; Active flag.
 cp 3
 jr z,ship_hit_bird_next    ; Blast pixels are not physical enemies.
 or a                        ; Is enemy live?
 jr z,ship_hit_bird_next     ; Skip inactive enemy.
 ; V1.1: cajas ajustadas a los dibujos (enemigo x+2..x+13, nave x+4..x+19,
 ; y solo si el enemigo pasa del morro): sin choques por esquinas vacias.
 ld a,(ix+1)                ; Enemy Y.
 cp 172
 jr nc,ship_hit_bird_next    ; Too low.
 cp 141
 jr c,ship_hit_bird_next     ; Too high.
 ld a,(ix+0)                ; Enemy X.
 add a,2
 ld c,a                     ; Enemy left.
 ld a,(ship_x)
 add a,20                   ; Ship right (exclusive).
 cp c
 jr c,ship_hit_bird_next     ; No overlap.
 jr z,ship_hit_bird_next
 ld a,c
 add a,12
 ld c,a                     ; Enemy right (exclusive).
 ld a,(ship_x)
 add a,4                    ; Ship left.
 cp c
 jr nc,ship_hit_bird_next    ; No overlap.
 ld (ix+2),3                ; Contact explosion, not an instant disappearance.
 ld (ix+5),6                ; Six visible blast updates; excludes repeat hits.
 call sfx_explode
 call player_take_hit       ; One life lost, if grace period not in progress.
ship_hit_bird_next:
 ld de,6                     ; Next bird record.
 add ix,de                   ; Advance IX.
 pop bc                      ; Restore loop count.
 djnz ship_hit_bird_loop     ; Check all birds.
 ret                         ; Finished contact collisions.

player_take_hit:
 ld a,(shield_invulnerable)  ; Is post-hit grace period active?
 ld hl,grace_irqs           ; V1.1: tambien durante la gracia al reaparecer.
 or (hl)                     ; Zero = can lose a life.
 ret nz                      ; One death cannot remove multiple lives.
 ld a,(player_lives)         ; Remaining life icons.
 or a                        ; Guard against negative lives.
 ret z                       ; At zero, no additional decrements.
 dec a                       ; One fatal collision.
 ld (player_lives),a         ; Record new count.
 ld a,150                   ; 3s: 1s explosion + 1s absence + 1s respawn flash.
 ld (shield_invulnerable),a  ; Exact real-time counter in 50Hz IM2.
 ld a,1
 ld (fire_held),a          ; No accidental auto-shot if SPACE is held on death.
 ld (player_respawn_pending),a ; Respawn once in center, only after absence.
 call beep_player_death      ; Distinct short descending death cue.
 ret                         ; HUD sync occurs in combat_tick.

; V1.2: shield_bar_present y lives_hud_present estan en src/v12_hud.asm.

; Old/new shield color outline; allow cyan cockpit and yellow thrusters to win.
shield_color_unpaint:
 ld a,0x47                   ; White original ink on black background.
 jp shield_color_apply       ; Restore perimeter samples to default.
shield_color_paint:
 ld a,0x44                   ; Bright green field ink.
 jp shield_color_apply       ; Paint private palette, not ULA attributes.
shield_color_apply:
 ld (shield_outline_color),a ; Save desired cell ink.
 ld a,(ship_attr_x)          ; Current/old ship left pixel.
 ld b,a                      ; B=x left edge for cell sample.
 ld a,(ship_attr_y)          ; Ship top pixel.
 sub 5                      ; Top stripe of the actual 32x32 parabrisas.
 ld c,a
 ld a,(ship_attr_x)
 add a,8
 ld b,a
 ld a,(shield_outline_color)
 call ship_attr_plot         ; Upper-left energy arch (separate from nose).
 ld a,(ship_attr_x)
 add a,15
 ld b,a
 ld a,(shield_outline_color)
 call ship_attr_plot         ; Upper-right energy arch.
 ld a,(ship_attr_y)
 add a,11
 ld c,a
 ld a,(ship_attr_x)
 sub 4
 ld b,a
 ld a,(shield_outline_color)
 call ship_attr_plot         ; Far-left canopy border.
 ld a,(ship_attr_x)
 add a,27
 ld b,a
 ld a,(shield_outline_color)
 call ship_attr_plot         ; Far-right canopy border.
 ret                         ; Cockpit and engines retain original ink priority.

shield_state: db 0           ; 0 ready, 1 active, 2 recharging.
shield_key_held: db 0        ; A edge latch independent of FIRE latch.
shield_previous_state: db 0  ; Last visible frame state for old attributes.
shield_frame_state: db 0     ; Stable one-frame shield state, sampled after input.
shield_timer: dw 0           ; 50Hz countdown for 3s+6s phases.
shield_charge_frame: db 0    ; 0..37 partial eighth segment.
shield_meter: db 8           ; 0..8 green segments.
shield_meter_displayed: db 8 ; Last drawn meter state.
shield_ready_pending: db 0  ; ISR only flags sound; beeper driven by main loop.
shield_invulnerable: db 0    ; Post-hit protection in real IRQs.
player_lives: db 3           ; Three lives as classic arcade.
lives_displayed: db 3       ; Last native HUD lives visible.
shield_outline_color: db 0x44 ; Ink for current shield perimeter attr.
shot_spawn_turn: db 0       ; Preferred rotating gunner (0..5).
shot_shooter_index: db 0     ; Current scan index, wraps safely.
old_enemy_bullets: ds 9    ; Previous 3 enemy bullets (3 bytes each).
enemy_bullet_slots: ds 9   ; Current enemy bullets (3 bytes each).
