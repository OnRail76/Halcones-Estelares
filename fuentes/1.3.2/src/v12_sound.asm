; HALCONES ESTELARES 1.2 - SONIDO.
; El beeper lo mueve la CPU: aqui solo se toca en el tiempo que sobra. Durante
; la partida, tick_wait toca el efecto en curso mientras espera la interrupcion
; (el juego no pierde ni un fotograma); en titulo, fase superada y GAME OVER
; music_frame toca la melodia hasta cada interrupcion.
; Efecto: db prioridad; segmentos dw semiperiodo, db delta (con signo, por tick),
; db ticks, db modo (0 tono, 1 ruido, 2 silencio); fin = dw 0.
snd_ear equ 0xf050
snd_seg equ 0xf051          ; puntero al siguiente segmento (0 = sin efecto)
snd_hp equ 0xf053           ; semiperiodo en curso (iteraciones de 26 T)
snd_delta equ 0xf055
snd_left equ 0xf056
snd_mode equ 0xf057
snd_prio equ 0xf058
snd_rng equ 0xf059
mus_ptr equ 0xf05a
mus_left equ 0xf05c
mus_note equ 0xf05d
mus_loop equ 0xf05e
snd_play_mode equ 0xf060

; HL = efecto. Solo suena si su prioridad es >= la del efecto en curso.
sfx_start:
 ld a,(snd_left)
 or a
 jr z,sfx_take
 ld a,(snd_prio)
 cp (hl)
 jr z,sfx_take
 ret nc
sfx_take:
 ld a,(hl)
 ld (snd_prio),a
 inc hl
; HL = segmento a cargar.
sfx_load:
 ld a,(hl)
 inc hl
 ld e,a
 ld a,(hl)
 inc hl
 ld d,a
 or e
 jr z,sfx_end
 ld (snd_hp),de
 ld a,(hl)
 inc hl
 ld (snd_delta),a
 ld a,(hl)
 inc hl
 ld (snd_left),a
 ld a,(hl)
 inc hl
 ld (snd_mode),a
 ld (snd_seg),hl
 ret
sfx_end:
 xor a
 ld (snd_left),a
 ld (snd_prio),a
 ret

; Una vez por tick de juego: avanza el efecto (barrido y segmentos).
snd_tick:
 ld a,(snd_left)
 or a
 ret z
 dec a
 ld (snd_left),a
 jr nz,snd_sweep
 ld hl,(snd_seg)
 jr sfx_load
snd_sweep:
 ld a,(snd_delta)
 ld e,a
 ld d,0
 bit 7,a
 jr z,snd_sweep_add
 dec d
snd_sweep_add:
 ld hl,(snd_hp)
 add hl,de
 ld (snd_hp),hl
 ret

; Toca el efecto en curso hasta que tick_irqs deje de valer E (o espera).
; V1.3: el rato que se pasa aqui se cuenta en snd_idle (unidades de 26 T) para
; saber cuanto sobra en cada tick y tocar parte a mitad de tick (snd_mid).
snd_slice:
 ld a,(snd_left)
 or a
 jr z,snd_rest
 ld a,(snd_mode)
 cp 2
 jr z,snd_rest
 ld hl,(snd_hp)
 ld (snd_play_mode),a
 jr tone_half
; A = modo (0 tono, 1 ruido), HL = semiperiodo: suena hasta la siguiente IRQ.
tone_until_irq:
 ld (snd_play_mode),a
 ld a,(tick_irqs)
 ld e,a
tone_half:
 call snd_half
 push hl
 ld bc,(snd_idle)
 add hl,bc
 ld bc,8                    ; lo que cuesta cada media onda ademas del retardo
 add hl,bc
 ld (snd_idle),hl
 pop hl
 ld a,(tick_irqs)
 cp e
 jr z,tone_half
 ret
; Media onda: HL = semiperiodo. Conserva HL y DE.
snd_half:
 ld a,(snd_play_mode)
 or a
 jr z,tone_square
 ld a,(snd_rng)
 add a,a
 jr nc,tone_noise_ok
 xor 0x1d
tone_noise_ok:
 ld (snd_rng),a
 and 16
 jr tone_out
tone_square:
 ld a,(snd_ear)
 xor 16
tone_out:
 ld (snd_ear),a
 out (0xfe),a
 ld b,h
 ld c,l
tone_delay:
 dec bc
 ld a,b
 or c
 jr nz,tone_delay
 ret
; Sin efecto: espera contando (antes HALT) para medir el rato libre.
snd_rest:
 push hl
snd_rest_loop:
 ld a,(tick_irqs)
 cp e
 jr nz,snd_rest_end
 ld hl,(snd_idle)
 inc hl
 inc hl
 inc hl
 ld (snd_idle),hl
 jr snd_rest_loop
snd_rest_end:
 pop hl
 ret

; V1.3: desde la interrupcion de mitad de tick (tick_irqs pasa a 1) toca la
; mitad de lo que sobro en el tick anterior (snd_budget). Asi el efecto suena
; dos veces por tick y los huecos de silencio son la mitad de largos, sin
; gastar mas tiempo del que ya sobraba. Conserva todo salvo AF y HL.
snd_mid:
 ld a,(snd_mid_ok)
 or a
 ret z
 ld a,(tick_irqs)
 dec a
 ret nz
 ld (snd_mid_ok),a          ; una vez por tick
 ld a,(snd_left)
 or a
 ret z
 ld a,(snd_mode)
 cp 2
 ret z
 ld (snd_play_mode),a
 push bc
 push de
 ld de,(snd_budget)
 ld hl,(snd_idle)           ; cuenta como rato libre del tick (el final
 add hl,de                  ; del tick sobrara eso menos)
 ld (snd_idle),hl
 ld hl,(snd_hp)
snd_mid_loop:
 call snd_half
 ex de,hl
 or a
 sbc hl,de
 jr c,snd_mid_end
 ld bc,8
 sbc hl,bc
 jr c,snd_mid_end
 ex de,hl
 jr snd_mid_loop
snd_mid_end:
 pop de
 pop bc
 ret

; MUSICA: tune = pares (nota 1..18, fotogramas); nota 0 = silencio; 255 = fin.
; HL = melodia, DE = punto de vuelta (0 = no se repite).
music_start:
 ld (mus_ptr),hl
 ld (mus_loop),de
 xor a
 ld (mus_left),a
 ret
music_stop:
 ld hl,0
 ld (mus_ptr),hl
 xor a
 ld (mus_left),a
 ret
; Toca un fotograma de musica (hasta la siguiente IRQ).
music_frame:
 ld a,(tick_irqs)
 ld e,a
 ld a,(mus_left)
 or a
 jr nz,music_play
 ld hl,(mus_ptr)
 ld a,h
 or l
 jr z,music_rest
 ld a,(hl)
 cp 255
 jr nz,music_note
 ld hl,(mus_loop)
 ld a,h
 or l
 jr z,music_end
 ld a,(hl)
music_note:
 ld (mus_note),a
 inc hl
 ld a,(hl)
 inc hl
 ld (mus_left),a
 ld (mus_ptr),hl
music_play:
 ld a,(mus_left)
 dec a
 ld (mus_left),a
 ld a,(mus_note)
 or a
 jr z,music_rest
 add a,a
 ld l,a
 ld h,0
 ld de,note_hp-2
 add hl,de
 ld a,(hl)
 inc hl
 ld h,(hl)
 ld l,a
 xor a
 jp tone_until_irq
music_end:
 call music_stop
music_rest:
 ld a,(tick_irqs)
 ld e,a
 jp snd_rest

; Llamadas de efecto (sustituyen a los clics de la 1.1).
sfx_shot:
 ld hl,fx_shot
 jp sfx_start
sfx_enemy_fire:
 ld hl,fx_enemy_fire
 jp sfx_start
sfx_boss_fire:
 ld hl,fx_boss_fire
 jp sfx_start
sfx_explode:
 ld hl,fx_explode
 jp sfx_start
sfx_boss_hit:
 ld hl,fx_boss_hit
 ld a,(boss_hp)
 cp 6
 jp nc,sfx_start
 ld hl,fx_boss_hit_low
 jp sfx_start
sfx_shield_on:
 ld hl,fx_shield_on
 jp sfx_start
sfx_shield_ready:
 ld hl,fx_shield_ready
 jp sfx_start
sfx_life:
 ld hl,fx_life
 jp sfx_start
sfx_card:
 ld hl,fx_card
 jp sfx_start
sfx_siren:
 ld hl,fx_siren
 jp sfx_start

; efectos: prioridad, segmentos (semiperiodo, delta, ticks, modo), fin
; V1.3: rehechos para el beeper troceado (suena a rafagas, dos por tick): golpe
; de ruido al principio, que es lo que mejor se oye a trozos, y barridos cortos.
fx_shot: db 1
 dw 5
 db 0,1,1                   ; chasquido
 dw 28
 db 22,3,0                  ; piu que cae
 dw 0
fx_enemy_fire: db 1
 dw 90
 db 242,3,0                 ; trino que sube
 dw 0
fx_boss_fire: db 2
 dw 60
 db 0,1,1                   ; soplido
 dw 260
 db 24,3,0                  ; disparo grave
 dw 0
fx_explode: db 2
 dw 4
 db 0,2,1                   ; estallido
 dw 18
 db 6,6,1                   ; retumbo que se apaga
 dw 0
fx_boss_hit: db 2
 dw 30
 db 0,1,1                   ; golpe en la piedra
 dw 340
 db 40,2,0
 dw 0
fx_boss_hit_low: db 2
 dw 12
 db 0,1,1                   ; la piedra cruje (le queda poco)
 dw 140
 db 30,3,0
 dw 0
fx_shield_on: db 3
 dw 420
 db 216,8,0
 dw 950
 db 1,67,0
 dw 0
fx_shield_ready: db 2
 dw 46
 db 0,2,0
 dw 1
 db 0,1,2
 dw 36
 db 0,3,0
 dw 0
fx_life: db 4
 dw 125
 db 0,3,0
 dw 98
 db 0,3,0
 dw 82
 db 0,3,0
 dw 60
 db 0,6,0
 dw 0
fx_card: db 1
 dw 104
 db 0,2,0
 dw 1
 db 0,1,2
 dw 104
 db 0,2,0
 dw 1
 db 0,1,2
 dw 68
 db 0,5,0
 dw 0
fx_siren: db 3
 dw 300
 db 236,8,0
 dw 140
 db 20,8,0
 dw 300
 db 236,8,0
 dw 140
 db 20,8,0
 dw 300
 db 236,8,0
 dw 140
 db 20,8,0
 dw 0
