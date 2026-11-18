; HALCONES ESTELARES V1.5 — STANDALONE INTERRUPT CONTROLLER (Z80/48K)
; This uses David M. Webb's robust IM2 scheme, independently implemented.
; Rationale: the original IM1 ROM interrupt changes Spectrum system variables,
; scans the keyboard and can interact with games using IX/IY and their own SP.
; The ESF game reads the ULA keyboard directly via IN A,(C): ROM ISR is unnecessary.
;
; Memory map: $FDFD..$FDFF = JP trampoline, $FE00..$FF00 = 257-byte
;            interrupt vector table (ALL bytes $FD); stack starts at $FFF0.
; Even an odd/even interrupt bus byte yields pointer $FDFD; no external
; assumption about whether the floating bus is $FF. Each instruction is Z80.
;
; INPUT: none; interrupts disabled by caller; SP valid.
; OUTPUT: I=$FE, IM2, 257 table bytes and vector jump installed.
; CLOBBERS: AF BC DE HL; preserves IX IY SP; does NOT enable IRQ itself.
irq_im2_install:
 ld hl,0xfe00            ; HL points to the first vector-table byte.
 ld de,0xfe01            ; DE points one byte beyond HL, to fill by propagation.
 ld bc,256               ; BC counts the 256 following bytes (257 total).
 ld (hl),0xfd            ; Any vector pair must form $FDFD.
 ldir                    ; Fill $FE01..$FF00 with $FD, without ROM calls.
 ld hl,0xfdfd            ; HL points to three-byte JP immediately before table.
 ld (hl),0xc3            ; $C3 = Z80 JP nn absolute.
 inc hl                  ; HL points to low byte of jump destination.
 ld de,irq_im2_handler   ; DE holds address of ISR in code segment at $8000+.
 ld (hl),e               ; Store the low byte at $FDFE.
 inc hl                  ; HL points to $FDFF.
 ld (hl),d               ; Store the high byte at $FDFF.
 ld a,0xfe               ; High byte of vector page $FE00.
 ld i,a                  ; Z80 interrupt register I = $FE.
 im 2                    ; Use our 257-byte RAM vector table instead of ROM $0038.
 ret                     ; Return to caller with maskable interrupts still disabled.

; INPUT: Z80 maskable IM2 interrupt.  No register changes / no system access.
; OUTPUT: resumes interrupted instruction stream after Z80 RETI.
; REGISTER/FLAGS: unchanged; SP balanced; IFF reenabled for next refresh.
irq_im2_handler:
 push af                 ; Save interrupted AF (including flags) before changing timer.
 push hl                 ; Save interrupted HL because timer uses a 16-bit counter.
 ld hl,tick_irqs         ; V1.1: cuenta las interrupciones del tick en curso.
 inc (hl)
 ld a,(game_paused)      ; V1.1: en pausa no corre ningun temporizador.
 or a
 jr nz,irq_paused
 call shield_irq_tick    ; Exactly one 50 Hz hardware IRQ, even if renderer is slow.
 call rush_rest_irq_tick   ; V2.6: 100 physical IRQ ticks per kamikaze regroup.
 call gameover_irq_tick  ; Three-second GAME OVER input lockout (150 real IRQs).
 call grace_irq_tick     ; V1.1: invulnerabilidad extra al reaparecer.
 call snd_mid            ; V1.3: trozo de sonido a mitad de tick (< 1 fotograma).
irq_paused:
 pop hl                  ; Restore HL exactly as interrupted.
 pop af                  ; Restore A and original flags exactly.
 ei                      ; Enable following interrupts after RETI as required by Z80.
 reti                    ; Return to interrupted program without calling ROM IM1.
