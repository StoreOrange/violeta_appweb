# Despliegue Ubuntu VPS

Proyecto objetivo:

- Codigo: `/home/ubuntu/Documents/Violeta`
- Dominio: `www.violeta.storeorange.ovh`
- Stack: `gunicorn + nginx + certbot`

## 1. Entrar al servidor y actualizar codigo

```bash
cd /home/ubuntu/Documents/Violeta
git fetch origin
git checkout main
git pull origin main
```

## 2. Crear entorno virtual

```bash
cd /home/ubuntu/Documents/Violeta
sudo apt update
sudo apt install -y python3-venv python3-pip nginx
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Configurar variables sensibles

Edita `config.toml` o exporta variables de entorno. Minimo:

```toml
[smtp]
host = "smtp.zoho.com"
port = 587
user = "TU_USUARIO_SMTP"
password = "TU_PASSWORD_SMTP"
sender_name = "Violeta Workspace"
use_tls = true
```

Tambien puedes usar:

```bash
export SECRET_KEY="una-clave-larga-y-segura"
export DATABASE_URL="postgresql://USUARIO:CLAVE@localhost:5432/GESTIONDB"
export CONFIG_TOML_PATH="/home/ubuntu/Documents/Violeta/config.toml"
```

## 4. Probar gunicorn manualmente

```bash
cd /home/ubuntu/Documents/Violeta
source .venv/bin/activate
gunicorn --workers 3 --bind 127.0.0.1:8000 wsgi:app
```

Si responde sin errores, detenlo con `Ctrl+C`.

## 5. Instalar servicio systemd

```bash
sudo cp /home/ubuntu/Documents/Violeta/deploy/ubuntu/violeta.service /etc/systemd/system/violeta.service
sudo systemctl daemon-reload
sudo systemctl enable violeta
sudo systemctl start violeta
sudo systemctl status violeta
```

## 6. Configurar nginx

```bash
sudo cp /home/ubuntu/Documents/Violeta/deploy/ubuntu/violeta.nginx.conf /etc/nginx/sites-available/violeta
sudo ln -sf /etc/nginx/sites-available/violeta /etc/nginx/sites-enabled/violeta
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

## 7. Activar HTTPS con Certbot

Segun las instrucciones oficiales de Certbot para Nginx en Ubuntu, la via recomendada es `snap` y luego `certbot --nginx`.

```bash
sudo snap install core
sudo snap refresh core
sudo apt-get remove -y certbot
sudo snap install --classic certbot
sudo ln -sf /snap/bin/certbot /usr/local/bin/certbot
sudo certbot --nginx -d www.violeta.storeorange.ovh
sudo certbot renew --dry-run
```

## 8. Abrir firewall si usas UFW

```bash
sudo ufw allow 'Nginx Full'
sudo ufw status
```

## 9. Comandos de mantenimiento

Ver logs del servicio:

```bash
sudo journalctl -u violeta -f
```

Reiniciar despues de actualizar:

```bash
cd /home/ubuntu/Documents/Violeta
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart violeta
sudo systemctl reload nginx
```

## 9.1. Alinear una base existente con el proyecto actual

Si la base ya existia antes de integrar Alembic, primero aplica el parche seguro:

```bash
cd /home/ubuntu/Documents/Violeta
PGPASSWORD=1234 psql -h localhost -U user -d gestiondb -f deploy/ubuntu/update_schema_violeta.sql
```

Luego marca la base con la revision inicial de migraciones:

```bash
source .venv/bin/activate
export FLASK_APP=wsgi.py
flask db stamp faa6f74cbb59
```

Despues de eso, las siguientes actualizaciones ya pueden usar:

```bash
flask db upgrade
```

## 10. Validaciones finales

```bash
curl -I http://www.violeta.storeorange.ovh
curl -I https://www.violeta.storeorange.ovh
```

La URL segura debe mostrar candado en el navegador cuando:

- el DNS del subdominio apunta al VPS
- nginx responde por el dominio correcto
- certbot instala el certificado sin errores
