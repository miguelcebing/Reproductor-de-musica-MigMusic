# infra/ — Despliegue en AWS

Todo lo necesario para llevar MigMusic a un servidor propio (`us-east-1`) con HTTPS,
sin depender de Vercel ni Render. La app corre entera en una instancia EC2; la base de
datos sigue en Neon.

## Topología

```
navegador ──HTTPS(443)──▶ Nginx ──┬── /assets, /icons, /   ──▶ /opt/migmusic/frontend/dist  (SPA)
                                  └── /api/, /health        ──▶ Gunicorn 127.0.0.1:8000    (FastAPI)
                                                                    │
                                                                    ▼
                                                          Neon PostgreSQL (us-east-2)
```

- **Un solo origen**: la SPA y la API comparten dominio, así que las cookies de sesión
  (`HttpOnly`, `Secure`, `SameSite=None`) viajan *first-party* y el OAuth no necesita
  proxy externo.
- **Nginx** sirve los estáticos con caché agresiva (`/assets/*` es inmutable por el
  hash de Vite) y hace de reverse proxy con rate limiting por IP.
- **Gunicorn** corre sobre `uvicorn.workers` con 2 workers (la instancia tiene 2 vCPU).
- **Let's Encrypt** gestiona el TLS; `certbot.timer` renueva en segundo plano.

## Componentes

| Archivo | Qué hace |
|---|---|
| `scripts/provision.sh` | Prepara el servidor limpio. **Idempotente**: se puede re-ejecutar sin daño. |
| `scripts/deploy.ps1` | Empaqueta, sube y despliega desde Windows. Orquesta lo de abajo. |
| `scripts/apply-deploy.sh` | Se ejecuta **en el servidor**: `uv sync`, nginx, systemd y health check. |
| `scripts/backup-db.sh` | Volcado nocturno de Neon; lo lanza `migmusic-backup.timer`. |
| `nginx/migmusic.conf` | Vhost: estáticos, proxy `/api/*`, CSP y rate limiting. |
| `nginx/security-headers.conf` | Cabeceras de seguridad compartidas (HSTS, `X-Frame-Options`…). |
| `systemd/migmusic.service` | Unidad del backend, con endurecimiento (`ProtectSystem=strict`…). |
| `systemd/migmusic-backup.{service,timer}` | Backup diario de la base de datos. |
| `gunicorn/gunicorn.conf.py` | Workers, bind y logs. |
| `env/migmusic.env.example` | **Solo nombres** de variables; nunca valores reales. |
| `iam/migmusic-deploy-policy.json` | Política least-privilege para el usuario IAM del despliegue. |

## Puesta en marcha

### 1. Provisionar (una sola vez)

```bash
bash infra/scripts/provision.sh
```

Crea el usuario de servicio `migmusic`, instala nginx/certbot/fail2ban, activa ufw
(solo el 22 desde la IP del administrador, más 80 y 443), añade 2 GB de swap y `uv`.

> **SSH restringido**: la regla de ufw para el puerto 22 usa `${SSH_SOURCE}`. Si tu IP
> cambia, o si el `HOME` del usuario debe salir de `/home` por el endurecimiento del
> systemd, `provision.sh` lo resuelve (`ProtectHome=yes` + libpq necesitan una home
> accesible, de ahí `/var/lib/migmusic`).

### 2. Secretos

Copia `env/migmusic.env.example`, rellena los valores y súbelo a
`/etc/migmusic/migmusic.env` en el servidor:

```bash
sudo install -o root -g migmusic -m 0640 migmusic.env /etc/migmusic/migmusic.env
```

Debe quedar en **LF** (un `\r` rompe la lectura de libpq y del propio bash).

### 3. Desplegar

Desde Windows (repositorio local):

```powershell
.\infra\scripts\deploy.ps1 -Target 54.166.184.47
.\infra\scripts\deploy.ps1 -Target 54.166.184.47 -SkipBuild   # reutiliza frontend/dist
```

El script empaqueta el repo, lo sube por SSH y ejecuta `apply-deploy.sh`, que termina
validando `/health` con reintentos. Los secretos **no** van en el paquete.

### 4. HTTPS

```bash
sudo certbot --nginx -d migmusicreproductor.duckdns.org --redirect
```

La renovación es automática (`systemctl status certbot.timer`). Comprobar sin gastar
cuota: `sudo certbot renew --dry-run`.

### 5. Spotify

En el Dashboard de Spotify, el **Redirect URI** debe ser exacto:

```
https://migmusicreproductor.duckdns.org/api/auth/callback
```

Sin barra final y sin `www`. Spotify exige HTTPS en producción.

## Operación

```bash
journalctl -u migmusic -f              # logs en vivo (una línea JSON por evento)
systemctl status migmusic nginx        # estado
systemctl list-timers                  # backup nocturno + renovación TLS
sudo systemctl start migmusic-backup.service   # backup manual
sudo nginx -t && sudo systemctl reload nginx   # tras tocar el vhost
```

## Rollback

1. `git checkout <commit-sano>`
2. `.\infra\scripts\deploy.ps1 -Target <ip>`

El health check decide si el despliegue se mantiene. Para la base de datos, restaura el
volcado nocturno o usa *Restore* de Neon.

## Notas de seguridad

- Secretos **solo** en `/etc/migmusic/migmusic.env` (`root:migmusic`, `0640`).
- El usuario `migmusic` no tiene shell (`/usr/sbin/nologin`) ni home bajo `/home`.
- El despliegue **nunca** copia `.env`, `credentials.env` ni claves al servidor.
- `infra/iam/migmusic-deploy-policy.json` documenta los permisos mínimos que necesita
  la cuenta que despliega (EC2, SNS, Budgets). Adáptala antes de usarla en otra cuenta.
