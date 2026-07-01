# Pixel Soft Utility Codex Pack v4

Gemeinsames Design-, Setup-, Security- und Dokumentationspaket für ishiku Webapps.

## Neu in v4

- Universal First-Run Setup mit `RegisterWindow`
- Docker-Secret-Vertrag für initiale Admin-Registrierung
- Regel: Admin-Passwort darf nicht mit Setup-Secret übereinstimmen
- Registrierung schließt nach dem ersten Adminaccount
- gemeinsame Auth-/Setup-Komponentenstyles
- `setup-flow.js` mit Frontend-Validierungshelfern
- Docker Compose Template mit Secret-Datei
- standardisierte GitHub README-Struktur
- README-Template mit Segmenten wie Installation, Teil der ishiku-Familie und Erstellt mit ChatGPT Codex
- zusätzlicher Runtime-Vertrag für Healthchecks, Datenpfade, Env-Variablen und Repository-Konventionen

## Reihenfolge für Codex

1. `contracts/pixel_soft_utility_codex_contract.yaml`
2. `contracts/setup_bootstrap_contract.yaml`
3. `contracts/github_readme_contract.yaml`
4. `contracts/app.manifest.schema.yaml`
5. konkretes `app.manifest.json`
6. `contracts/component_usage_matrix.yaml`
7. `contracts/universal_app_runtime_contract.yaml`
8. `design-system/*.css` und `design-system/*.js`
9. `templates/github/README.template.md`
10. `templates/docker/docker-compose.example.yml`

## Kernaussage

Jede App soll nicht nur gleich aussehen, sondern auch gleich starten, gleich dokumentiert sein und dieselben Grundregeln für Admin-Erstellung, Docker-Secrets, About/Admin-Bereiche und README-Struktur verwenden.

## Wichtige Dateien

- `contracts/setup_bootstrap_contract.yaml`
- `contracts/github_readme_contract.yaml`
- `contracts/universal_app_runtime_contract.yaml`
- `design-system/setup-flow.js`
- `templates/vanilla/setup.html`
- `templates/docker/docker-compose.example.yml`
- `templates/docker/.env.example`
- `templates/github/README.template.md`
- `checklists/setup_security_readme_checklist.md`

## Logo-Regel bleibt erhalten

`app_logo` ist weiterhin das primäre App-Symbol für Header, Favicon, PWA, About, ProfileSheet und Empty States. `app_symbol` bleibt Fallback. Theme-Farben werden nicht aus Logos abgeleitet.

## Theme-Regel bleibt erhalten

Alle Apps nutzen dieselben sechs Themes:

- Lavender
- Mint
- Sky
- Amber
- Rose
- Graphite

Jedes Theme unterstützt Light, Dark und System Mode.
