# Pulliku

Medien herunterladen

> Pulliku ist ein ruhiges, self-hosted Webinterface für Medien-Downloads.

## Kurzbeschreibung

Pulliku ist eine self-hosted Web-App aus der ishiku-Familie. Die App ist für private oder kleine eigene Deployments gedacht und folgt dem gemeinsamen Pixel Soft Utility Designsystem.

## Teil der ishiku-Familie

Pulliku verwendet die gemeinsame ishiku Oberfläche:

- ruhige, abgerundete Pixel-Soft-Utility-Komponenten
- sechs gemeinsame Themes: Lavender, Mint, Sky, Amber, Rose und Graphite
- Light, Dark und System Mode
- einheitlicher AppHeader, Profil-/Einstellungs-Sheets und About/Admin-Bereiche
- einheitliches First-Run-Setup für den ersten Adminaccount

Die App soll sich bewusst wie Teil einer gemeinsamen Suite anfühlen, nicht wie eine separate Marke mit eigener Designsprache.

## Funktionen

- URL-basierte Download-Aufgaben
- Queue- und Verlaufskarten im Pixel Soft Utility Design
- Einheitliches Admin-Setup mit Docker-Secret

## Screenshots

> Screenshots können hier ergänzt werden, sobald die UI final ist.

```md
![Mobile Ansicht](docs/screenshots/mobile.png)
![Desktop Ansicht](docs/screenshots/desktop.png)
```

## Tech Stack

- Frontend: Bitte an Projekt anpassen
- Backend: Bitte an Projekt anpassen
- Datenhaltung: Bitte an Projekt anpassen
- Deployment: Docker / Docker Compose

## Installation

### Docker Compose

```bash
mkdir -p pulliku/secrets pulliku/data
cd pulliku
cp docker-compose.example.yml docker-compose.yml
cp .env.example .env
```

Lege anschließend ein langes zufälliges Setup-Secret an:

```bash
openssl rand -base64 48 > secrets/setup_secret.txt
chmod 600 secrets/setup_secret.txt
```

Starte die App:

```bash
docker compose up -d
```

### Erstes Starten

Beim ersten Öffnen zeigt die App automatisch das Registrierungsfenster für den ersten Adminaccount an. Die Registrierung ist nur möglich, wenn das Setup-Secret korrekt eingegeben wird.

### Adminaccount erstellen

Im Registrierungsfenster werden benötigt:

- Setup-Secret aus `secrets/setup_secret.txt`
- Admin-Benutzername
- Anzeigename
- Admin-Passwort

Das Admin-Passwort darf nicht mit dem Setup-Secret übereinstimmen. Nach erfolgreicher Erstellung des ersten Adminaccounts wird die öffentliche Registrierung automatisch geschlossen.

## Konfiguration

### Umgebungsvariablen

| Variable | Beschreibung | Standard |
| --- | --- | --- |
| `TZ` | Zeitzone für Logs und Anzeige | `Europe/Berlin` |
| `ISHIKU_APP_URL` | Öffentliche URL der App | leer |
| `ISHIKU_BASE_PATH` | Basis-Pfad hinter Reverse Proxy | `/` |
| `ISHIKU_DATA_DIR` | Persistenter Datenpfad im Container | `/data` |
| `ISHIKU_LOG_LEVEL` | Log-Level | `info` |
| `ISHIKU_SETUP_SECRET_FILE` | Pfad zum Docker-Secret | `/run/secrets/ishiku_setup_secret` |
| `ISHIKU_SETUP_SECRET` | Fallback-Secret als ENV, nur wenn kein Secret-File genutzt wird | leer |

### Docker Secrets

Bevorzugt wird ein Docker/Compose Secret als Datei. In `docker-compose.example.yml` wird dieses Secret nach `/run/secrets/ishiku_setup_secret` gemountet.

### Persistente Daten

Persistente Daten liegen standardmäßig in:

```txt
/data
```

Sichere diesen Ordner regelmäßig, wenn die App produktiv genutzt wird.

## Sicherheit

- Das Setup-Secret dient nur zur ersten Admin-Registrierung.
- Das Admin-Passwort darf nicht dem Setup-Secret entsprechen.
- Passwörter werden nicht im Klartext gespeichert.
- Die öffentliche Registrierung wird nach dem ersten Adminaccount geschlossen.
- Secrets, `.env`, Datenbanken und Logs gehören nicht ins Repository.

## Updates und Backup

```bash
docker compose pull
docker compose up -d
```

Vor Updates sollte der persistente Datenordner gesichert werden:

```bash
tar -czf backup-pulliku-$(date +%Y%m%d).tar.gz data
```

## Entwicklung

```bash
# Beispiel, bitte an den tatsächlichen Stack anpassen
npm install
npm run dev
```

Codex soll bei Änderungen das gemeinsame Pixel Soft Utility Designsystem beibehalten und keine app-spezifischen UI-Abweichungen einführen.

## Erstellt mit ChatGPT Codex

Dieses Projekt wurde mit Unterstützung von ChatGPT Codex erstellt bzw. überarbeitet. Codex wurde verwendet, um Code, Struktur, UI-Komponenten und Dokumentation nach den Vorgaben der ishiku / Pixel Soft Utility Standards zu generieren.

Die Verantwortung für Betrieb, Prüfung, Sicherheit und Veröffentlichung liegt beim Repository-Betreiber.

## Status und Lizenz

Status: Privates/self-hosted Projekt

Lizenz: Bitte Lizenz eintragen
