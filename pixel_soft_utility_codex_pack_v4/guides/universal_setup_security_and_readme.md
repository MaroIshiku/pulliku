# Universal Setup, Security und README Standard

Dieses Modul ergänzt Pixel Soft Utility um gemeinsame Betriebs- und Dokumentationsregeln.

## Ziel

Jede ishiku App soll gleich starten, gleich dokumentiert sein und dieselben Grundregeln für Admin-Erstellung, Secrets, Docker und README verwenden.

## First-Run Setup

Wenn beim Start keine Admin-Identität existiert, darf die normale App nicht sichtbar werden. Stattdessen erscheint sofort das `RegisterWindow`.

Das Fenster nutzt dieselben Komponenten wie der Rest des Systems:

- App-Logo oben
- Titel `Admin einrichten`
- Setup-Secret-Feld
- Admin-Benutzername
- Anzeigename
- optional E-Mail
- Admin-Passwort
- Passwort wiederholen
- klare Passwortregeln
- Primary Action `Adminaccount erstellen`

Nach erfolgreicher Registrierung wird Setup als abgeschlossen markiert. Danach ist öffentliche Registrierung geschlossen.

## Setup Secret

Bevorzugt wird ein Docker Secret als Datei:

```yaml
secrets:
  ishiku_setup_secret:
    file: ./secrets/setup_secret.txt
```

Die App liest zuerst:

```txt
ISHIKU_SETUP_SECRET_FILE=/run/secrets/ishiku_setup_secret
```

Nur falls das nicht verfügbar ist, darf ein ENV-Fallback genutzt werden:

```txt
ISHIKU_SETUP_SECRET=...
```

## Admin-Passwort

Das Admin-Passwort muss sich vom Setup-Secret unterscheiden. Diese Regel wird serverseitig geprüft, nicht nur im Frontend.

Empfohlen:

- mindestens 12 Zeichen
- kein Platzhalter wie `admin`, `password`, `passwort`, `changeme`
- nicht gleich Benutzername, App-ID oder App-Name
- Hashing mit Argon2id, falls Stack verfügbar; sonst bcrypt/scrypt/PBKDF2 nach Stack-Standard

## GitHub README

Jede App nutzt dieselbe Struktur aus `templates/github/README.template.md`.

Wichtig:

- Teil der ishiku-Familie immer früh erwähnen
- Installation und First-Run-Setup immer gleich erklären
- Docker Secrets dokumentieren
- Codex-Hinweis immer gleich platzieren
- keine echten Secrets oder lokalen privaten Pfade in README
