# Guía de Despliegue — FiguSwap

## Arquitectura de producción

```
Browser (HTTPS)
    │
    ▼
Firebase Hosting  →  frontend estático (React/Vite)
    │ peticiones API
    ▼
Nginx (HTTPS :443, Let's Encrypt)   ←  EC2 Debian
    │ proxy inverso
    ▼
Uvicorn / FastAPI (:8000)
    │
    ▼
MongoDB Atlas (nube)
```

| Servicio   | URL de producción                                          |
|------------|------------------------------------------------------------|
| Frontend   | https://figuswap-prod-utn-fb999.web.app                    |
| Backend    | https://figuswap-api.duckdns.org                           |
| DB         | clustertacs.ycfpq3j.mongodb.net (MongoDB Atlas)            |

---

## 1. Backend — EC2 (Debian)

### 1.1 Instalar Docker

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

### 1.2 Clonar el repositorio

```bash
git clone https://github.com/Marcosifran/TRABAJO-TACS-2026.git
cd TRABAJO-TACS-2026
```

### 1.3 Crear el archivo `.env`

```bash
nano .env
```

Contenido mínimo requerido:

```env
JWT_SECRET=<valor-largo-y-aleatorio>
SEED_USER_PASSWORD=figuswap123

MONGODB_URL=mongodb+srv://<usuario>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority&appName=<AppName>
MONGODB_DB_NAME=mundial_figuritas_db

CORS_ORIGINS=["https://<dominio-backend>","https://<dominio-frontend>"]

TELEGRAM_BOT_TOKEN=<token-de-botfather>
```

> El token de Telegram se obtiene hablando con @BotFather en Telegram (`/newbot`).

> Para generar UUIDs: `python3 -c "import uuid; print(uuid.uuid4())"`

### 1.4 Crear el compose de producción

```bash
cat > docker-compose.prod.yml << 'EOF'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file: .env
    restart: unless-stopped

  telegram_bot:
    build: ./telegram_bot
    env_file: .env
    environment:
      - BACKEND_URL=http://backend:8000/api/v1
    depends_on:
      - backend
    restart: unless-stopped
EOF
```

> El bot usa long polling (conexión saliente a `api.telegram.org`). No necesita
> puerto expuesto, cambios en Nginx ni en el Security Group de AWS.

### 1.5 Levantar el backend

```bash
docker compose -f docker-compose.prod.yml up --build -d
docker compose -f docker-compose.prod.yml logs -f
```

Verificar: `curl http://localhost:8000/` → `{"Hello":"World"}`

### 1.6 Configurar HTTPS con Nginx + Let's Encrypt

Requisitos previos:
- Subdominio apuntando a la IP del EC2 (se usó [DuckDNS](https://www.duckdns.org))
- Puertos **80** y **443** abiertos en el Security Group de AWS

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

Crear la configuración de nginx en `/etc/nginx/sites-available/figuswap`:

```nginx
server {
    listen 80;
    server_name <subdominio.duckdns.org>;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

> El header `X-Forwarded-Proto` es obligatorio para que FastAPI genere
> redirects con `https://` en lugar de `http://` cuando está detrás del proxy.

Activar y obtener el certificado:

```bash
sudo ln -s /etc/nginx/sites-available/figuswap /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d <subdominio.duckdns.org>
```

Certbot modifica automáticamente la config para agregar el bloque HTTPS
y el redirect 301 de HTTP → HTTPS.

### 1.7 Dockerfile de producción

El `backend/Dockerfile` debe usar `--proxy-headers` para que uvicorn
respete `X-Forwarded-Proto` y genere URLs correctas en los redirects:

```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips=*"]
```

> Sin `--proxy-headers`, los redirects automáticos de FastAPI (por ejemplo,
> normalización de trailing slashes) generan URLs `http://` en lugar de
> `https://`, lo que provoca errores de Mixed Content en el browser.

---

## 2. Frontend — Firebase Hosting

### 2.1 Variables de entorno

Crear el archivo `.env` en la **raíz del proyecto** (no dentro de `frontend/`),
ya que `vite.config.js` usa `envDir: '../'`:

```env
VITE_USER_1_TOKEN=<mismo valor que USER_1_TOKEN del backend>
VITE_USER_2_TOKEN=<mismo valor que USER_2_TOKEN del backend>
VITE_API_URL=https://<subdominio-backend.duckdns.org>/api/v1
```

> Los tokens `VITE_USER_*` deben coincidir exactamente con los `USER_*_TOKEN`
> del `.env` del servidor, o todas las requests devolverán 401.

### 2.2 Instalar Firebase CLI

```bash
npm install -g firebase-tools
firebase login
```

### 2.3 Inicializar Firebase Hosting

Desde la raíz del proyecto:

```bash
firebase init hosting
```

| Pregunta | Respuesta |
|---|---|
| Which Firebase project? | Use an existing project → `figuswap-prod-utn-fb999` |
| Public directory | `frontend/dist` |
| Single-page app? | Yes |
| Automatic builds with GitHub? | No |
| Overwrite index.html? | No |

### 2.4 Build y deploy

```bash
cd frontend
npm install
npm run build
cd ..
firebase deploy --only hosting
```

---

## 3. Actualizar en producción

### Backend — nuevo código

```bash
# En el EC2
cd /home/admin/TRABAJO-TACS-2026
git pull origin main
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up --build -d
```

### Backend — solo variables de entorno

```bash
# Editar .env
nano .env
# Recrear el container para que tome los nuevos valores
# (restart no alcanza, se necesita down + up)
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

### Telegram Bot — nuevo código

```bash
# En el EC2
cd /home/admin/TRABAJO-TACS-2026
git pull origin main
docker compose -f docker-compose.prod.yml up --build -d telegram_bot
# Ver logs del bot
docker compose -f docker-compose.prod.yml logs -f telegram_bot
```

### Frontend — nuevo código o variables de entorno

```bash
# Desde la máquina de desarrollo, en la raíz del proyecto
cd frontend && npm run build && cd ..
firebase deploy --only hosting
```

### Agregar un nuevo origen al CORS

Editar `.env` en el EC2 y agregar la URL al array:

```env
CORS_ORIGINS=["https://backend.duckdns.org","https://nuevo-frontend.web.app"]
```

Luego recrear el container:

```bash
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

---

## 4. Comandos útiles en el servidor

```bash
# Ver logs del backend
docker compose -f docker-compose.prod.yml logs -f

# Ver logs de nginx
sudo tail -f /var/log/nginx/error.log

# Estado del container
docker compose -f docker-compose.prod.yml ps

# Renovación del certificado SSL (automática, pero se puede forzar)
sudo certbot renew --dry-run
```

---

## 5. Security Group de AWS (puertos requeridos)

| Puerto | Protocolo | Uso |
|--------|-----------|-----|
| 22 | TCP | SSH |
| 80 | TCP | HTTP (redirect a HTTPS por nginx) |
| 443 | TCP | HTTPS (nginx → uvicorn) |
| 8000 | TCP | Acceso directo al backend (opcional, se puede cerrar) |
