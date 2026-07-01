# App-Logos

Lege hier deine App-Logos ab. Empfohlene Dateinamen:

```txt
pulliku.svg
meiku.svg
keyku.svg
libiku.svg
nestiku.svg
seediku.svg
```

## Anforderungen

- Bevorzugt SVG für skalierbare Header-, Favicon- und PWA-Nutzung.
- Alternativ PNG/WebP mit mindestens 512x512 px.
- Symbol-Logo bevorzugen; ein langes Schriftlogo ist im mobilen Header meist schlechter lesbar.
- Transparenter Hintergrund ist erlaubt.
- Das Logo darf nicht das Theme-System ersetzen: keine App-spezifischen CSS-Farben aus dem Logo ableiten.
- In Light und Dark Mode muss das Logo erkennbar bleiben. Falls nötig, `light_src` und `dark_src` im Manifest angeben.
- Wenn das Logo fehlschlägt, muss `app_symbol` als lokaler Icon-Fallback sichtbar bleiben.

## Manifest-Beispiel

```json
{
  "app_logo": {
    "src": "assets/logos/pulliku.svg",
    "light_src": "assets/logos/pulliku.svg",
    "dark_src": "assets/logos/pulliku-dark.svg",
    "favicon": "assets/logos/pulliku.svg",
    "pwa_icon_192": "assets/pwa/pulliku-192.png",
    "pwa_icon_512": "assets/pwa/pulliku-512.png",
    "alt": "",
    "use_as_header_symbol": true,
    "use_as_favicon": true,
    "use_as_about_symbol": true,
    "use_as_empty_state_symbol": true
  }
}
```

`alt` bleibt im Header normalerweise leer, weil direkt daneben der Appname steht.
