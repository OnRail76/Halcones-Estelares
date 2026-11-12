; HALCONES ESTELARES V1.9 — small original 1-bit beeper event palette.
; All FE writes keep border black; all effects run outside the IM2 handler.
; They are VERY SHORT, events only; no held beeper, no ROM BEEP.
; IN: none, OUT: AF BC clobbered, IX/IY preserved.
beep_enemy_destroy:
 ; V2.8: one short audible arcade BLIP for an enemy kill (~4.8ms at 3.5 MHz).
 ; No ROM calls; outside IM2; only AF, BC modified, matching the old contract.
 ld c,7                    ; Seven short cycles, approximately 1.4 kHz.
beep_enemy_blip_cycle:
 ld a,16                   ; EAR on, BORDER black.
 out (0xfe),a
 ld b,90                   ; Very short high half-cycle.
beep_enemy_blip_high:
 djnz beep_enemy_blip_high
 xor a                      ; EAR off, BORDER black.
 out (0xfe),a
 ld b,90                   ; Matching low half-cycle.
beep_enemy_blip_low:
 djnz beep_enemy_blip_low
 dec c
 jr nz,beep_enemy_blip_cycle
 ret
beep_player_death:
 ; V2.3: short audible PFF burst of fast pseudo-random EAR flips, not a melody.
 ; 16 * 190 samples of variable FE bit4 = about 45 ms at 3.5 MHz.
 ; Keep border black and restore DE; only this one-shot effect blocks gameplay.
 push de
 ld d,0xa7
 ld e,16
sfx_death_noise_burst:
 ld b,190
sfx_death_noise_next:
 ld a,d
 rrca
 xor d
 add a,0x3d
 ld d,a
 and 16
 out (0xfe),a
 djnz sfx_death_noise_next
 dec e
 jr nz,sfx_death_noise_burst
 xor a
 out (0xfe),a
 pop de
 ret
beep_boss_destroy:
 ; V2.4: deep, long ~0.20s pseudo-white-noise burst for defeated MOAI.
 ; Stronger and LONGER than ESF fighter death, but still event-triggered.
 ; Uses FE EAR bit only, border remains black; CPU returns with SP balanced.
 push de
 ld d,0xe3                 ; Distinct non-repeating seed from player destruction.
 ld e,76                   ; 76 x 190 noise iterations, approximate 0.2 seconds.
sfx_boss_rumble_outer:
 ld b,190
sfx_boss_rumble_inner:
 ld a,d
 rrca
 xor d
 add a,0x7b
 ld d,a
 and 16
 out (0xfe),a
 djnz sfx_boss_rumble_inner
 dec e
 jr nz,sfx_boss_rumble_outer
 xor a
 out (0xfe),a
 pop de
 ret
