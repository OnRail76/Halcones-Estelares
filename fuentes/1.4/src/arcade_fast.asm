; ESF fixed-screen 48K arcade renderer. Purpose: motion before embellishments.
; Native 0x4000 picture, 0x5800 attributes. XOR sprites reversible byte-for-byte
; on an immutable starfield; no dirty queue, shadow framebuffer or scroll.
arcade_screen_clear:
 xor a
 ld hl,0x4000
 ld de,0x4001
 ld bc,6143
 ld (hl),a
 ldir
 ld a,0x47       ; bright white ink on black; ESF HUD overwrites x192..255
 ld hl,0x5800
 ld de,0x5801
 ld bc,767
 ld (hl),a
 ldir
 ret
