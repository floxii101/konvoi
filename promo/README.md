# Konvoi – Werbevideos

- `konvoi-werbung-20s.mp4` (21,5 s) und `konvoi-teaser-9s.mp4` (9 s), 1080×1920, ohne Ton.
- `konvoi-werbung-20s-vo.mp4` und `konvoi-teaser-9s-vo.mp4`: dieselben Videos mit Voice-Over und leiser Musik (AAC 192k, ca. −16 LUFS).
- Neu rendern: Ordner nach `/tmp/promo` kopieren, dann `python3 make_videos.py both` (braucht Pillow + ffmpeg).
- `screens/` = App-Screenshots (3x), `map.svg` = nachgebaute Kartengrafik.

## Voice-Over: Text und Timing
Werbespot:
| Zeit | Text |
|---|---|
| 0–4,8 s | Kennt ihr das? Zu viert losgefahren … und plötzlich fehlt einer. |
| 4,8–8,6 s | Mit Konvoi seht ihr euch alle live auf der Karte. |
| 8,6–11,4 s | Einer muss tanken? Ein Tipp, und alle wissen, wohin. |
| 11,4–13,8 s | Und du siehst, wer mitkommt. |
| 13,8–16,4 s | Panne? Alle wissen sofort Bescheid. |
| 16,4–18,8 s | Und am Ende: eure Fahrt als Bild. |
| 18,8–21,5 s | Konvoi. Kostenlos, ohne Anmeldung. |

Teaser:
| Zeit | Text |
|---|---|
| 0–3,3 s | Deine Crew. Live auf der Karte. |
| 3,3–6 s | Einer muss tanken? Ein Tipp, und alle fahren hin. |
| 6–9 s | Konvoi. Probier's aus. |

Stil: locker, deutsch, männlich oder weiblich, eher natürlich als werblich; leise Musik darunter ist okay.

Abweichung im Werbespot: „Eine Panne?“ statt „Panne?“ – das einzelne Wort wurde von der Sprachausgabe nicht sauber ausgesprochen.

## Voice-Over: wie es gebaut wurde (`voiceover/`)
- **Stimme:** [Chatterbox Multilingual](https://github.com/resemble-ai/chatterbox) (MIT-Lizenz), Sprache `de`, geklont von ca. 13 s Aufnahmen aus dem Stil „amüsiert“ des gemeinfreien Thorsten-Voice-Datensatzes (CC0, `Thorsten-Voice/TV-44kHz-Full`). Mehrere Takes pro Satz (`gen.py`), automatisch per Whisper auf Versprecher geprüft (`check.py`), Auswahl in `choice.json`.
- **Musik:** selbst erzeugter Lo-Fi-Loop (`music.py`, 96 BPM, C–G–Am–F), also frei von Rechten Dritter.
- **Mix:** `assemble.py` legt jeden Satz kurz nach dem Schnitt an (bei Bedarf bis 12 % schneller), Musik −17 dB mit Ducking unter der Stimme, Loudnorm.
- `vo-*.flac` = reine Sprachspur, `musik-*.flac` = reine Musik, z. B. für einen eigenen Schnitt.
- Hinweis: Chatterbox setzt ein unhörbares Wasserzeichen (Perth) in die Sprachausgabe.
