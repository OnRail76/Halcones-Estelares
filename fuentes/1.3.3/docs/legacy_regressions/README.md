# Regresiones históricas (NO incluidas en la suite vigente)

Se preservan intactos los tests `test_v281_logo_bird_pulse.py`, `test_v282_kamikazes_first_phase.py`, `test_v283_moai_shield.py` y `test_v284_smileys_firma.py`, y el README histórico V2.8.4.

Algunos comparan archivos mediante rutas absolutas `/mnt/data/HALCONES_V281_CORREGIDO`, `/mnt/data/HALCONES_V282_KAMIKAZES_SUAVES` o `/mnt/data/HALCONES_V283_EQUILIBRIO`. Esos bancos externos no son parte de esta entrega; por tanto no deben formar parte de la suite de v1.3.3. No se han borrado ni alterado las pruebas históricas.

Ejecución actual: desde raíz `python3 -m pytest -q` (limitada a `tests/` por `pytest.ini`).
