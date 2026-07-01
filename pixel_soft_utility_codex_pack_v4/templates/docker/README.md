# Docker Template

Use this template for every ishiku app.

Preferred setup secret path:

```txt
/run/secrets/ishiku_setup_secret
```

The app should read `ISHIKU_SETUP_SECRET_FILE` first. `ISHIKU_SETUP_SECRET` is only a fallback for simple local deployments.

Never commit real `secrets/setup_secret.txt`, `.env`, `/data`, logs, or database files.
