# PWA Icons

Wenn eine App ein Webmanifest nutzt, generiere die PWA-Icons aus demselben App-Logo.

Empfohlen:

```txt
assets/pwa/{app_id}-192.png
assets/pwa/{app_id}-512.png
assets/pwa/{app_id}-maskable-512.png
```

Regeln:

- PWA-Icons müssen aus dem App-Logo abgeleitet sein, nicht aus einer neuen Grafik.
- Maskable Icons brauchen ausreichend Safe Area.
- Favicon und PWA-Icon sollen dieselbe Identität zeigen.
- Theme-Farben kommen weiter aus den sechs Pixel-Soft-Utility-Themes.
