# Arturia MiniLab 37 — script FL Studio (workflow)

Script personalizado del MiniLab 37 para FL Studio: los pads del **Bank A** no actúan como batería, sino como transporte y atajos de ventanas. El **Bank B** se deja libre para sampling (p. ej. Momentum).

Basado en el script de Farès MEZDOUR / Arturia, adaptado al workflow local.

---

## Instalación

1. Copia (o mantén) esta carpeta en:
   ```
   Documentos\Image-Line\FL Studio\Settings\Hardware\Arturia MiniLab 37\
   ```
2. En el MiniLab: **Shift + Prog** hasta que diga **DAW**.
3. Abre FL Studio → **Options → MIDI settings**.
4. Configura así:

| Dispositivo | Enable | Controller type | Port |
|-------------|--------|-----------------|------|
| **Minilab37 DAW** (Input) | On | **MiniLab 37** | **236** |
| **Minilab37 MIDI** (Input) | On | **MiniLab 37 Arturia** | libre (o el que uses para tocar) |
| **Minilab37 DAW** (Output) | On | — | **236** (mismo que el input DAW) |
| **Minilab37 MIDI** (Output) | **Off** | — | — |

5. Pulsa **Update MIDI scripts** → OK.
6. Recarga si hace falta: **View → Script output** → pestañas DAW/MIDI → **Reload script**.

Sin el **Output DAW en puerto 236**, las teclas pueden funcionar pero **los colores de los pads no**.

---

## Mapa de pads (Bank A)

Quédate en **Bank A**. Bank B = notas para Momentum / sampling.

| Pad (ícono) | Función | Color |
|-------------|---------|--------|
| **Arp** | Mixer (abre / cierra) | Azul (tenue) |
| **Pad** | Playlist (abre / cierra) | Cyan |
| **Prog** | Piano roll (abre / cierra) | Magenta |
| **Loop** | Undo | Naranja |
| **Stop** | Stop | Gris |
| **Play** | Play / Pause | Verde |
| **Record** | Record | Rojo |
| **Tap** | Metrónomo | Amarillo |

- Mixer / Playlist / Piano roll: **1er toque abre**, **2º cierra** (si esa ventana está enfocada).
- Channel Rack: sigue entrando con la **perilla master** (como antes).
- **Shift + pads Bank A** (notas): modo drums opcional (FPC). Casi no se usa.

---

## Qué hace cada archivo

| Archivo | Rol |
|---------|-----|
| `device_MiniLab37.py` | Script principal DAW (`# name=MiniLab 37`). Init, refresh, idle, colores. |
| `device_MiniLab37 MIDI.py` | Script del puerto MIDI (`# name=MiniLab 37 Arturia`). Notas de pads → acciones; bloquea Bank A para que no suenen; reenvía CCs a Analog Lab (puerto 10). |
| `MiniLab37Process.py` | Mapeo CC/notas → Stop, Play, Record, ventanas, Undo, metrónomo, knobs, plugins. |
| `MiniLab37Return.py` | LEDs de pads (colores por función, menos brillantes). |
| `MiniLab37Navigation.py` | Textos en la pantalla del MiniLab (Mixer, Undo, etc.). |
| `MiniLab37Display.py` / `MiniLab37Pages.py` | Pantalla / páginas temporales. |
| `MiniLab37Connexion.py` | Conexión modo DAW / Arturia (sin spamear SysEx que blanqueaba los LEDs). |
| `MiniLab37Dispatch.py` | Despacho de eventos MIDI + `send_to_device` (SysEx). |
| `MiniLab37Plugin.py` | Mapeo de knobs/faders a parámetros de plugins. |
| `ArturiaVCOL.py` | Lista de plugins Arturia (Analog Lab, etc.). |
| `_backup_original/` | Copia del script original **antes** del tuneo (local; no va a git). |

---

## Puertos MIDI (MiniLab 37)

El MiniLab 37 solo tiene dos puertos (no DIN THRU / MCU / ALV como el MiniLab 3):

- **Minilab37 MIDI** — teclas, knobs, notas de pads.
- **Minilab37 DAW** — script de control + SysEx (pantalla y colores).

---

## Problemas frecuentes

| Síntoma | Qué revisar |
|---------|-------------|
| Pads suenan notas graves | Estás en **Bank B**, o falta el script **MiniLab 37 Arturia** en el input MIDI. |
| Pads no abren ventanas | Modo **DAW** en el teclado; Reload de ambos scripts. |
| Pads todos blancos | Output **DAW** encendido y puerto **236** igual que el input DAW. |
| Al dar Stop/Play se blanquean y no vuelven | Recarga el script DAW (ya se mitiga en versiones recientes). |
| Nada funciona / error `_mk3` | Script output → Reload; no pongas el script **MiniLab 37** en *los dos* inputs (solo DAW). |
| Teclas muertas | No uses un Controller type roto en MIDI; debe ser **MiniLab 37 Arturia**. |

Script output (errores): **View → Script output**.

---

## Git

- `_backup_original/` y `__pycache__/` están en `.gitignore`.
- Para restaurar el stock: copia desde `_backup_original/` sobre los `.py` de la carpeta.
