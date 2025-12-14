# Nasazení aplikace na web

Tato příručka popisuje, jak nasadit aplikaci "Správa rozpočtu" na veřejný web.

## Varianty nasazení

### Varianta 1: Heroku (nejjednodušší)

#### Předpoklady
- Heroku účet (registrace na https://www.heroku.com)
- Git
- Heroku CLI

#### Kroky

1. **Přidejte Procfile**
```bash
# V kořenovém adresáři aplikace
echo "web: gunicorn app:app" > Procfile
```

2. **Aktualizujte requirements.txt**
```bash
pip freeze > requirements.txt
# Přidejte gunicorn
echo "gunicorn==21.2.0" >> requirements.txt
```

3. **Inicializujte git repository**
```bash
git init
git add .
git commit -m "Initial commit"
```

4. **Vytvoření aplikace na Heroku**
```bash
heroku login
heroku create jmeno-aplikace
```

5. **Nastavení konfigurací**
```bash
# Produkční konfigurace
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(16))')

# PostgreSQL databáze (místo SQLite)
heroku addons:create heroku-postgresql:hobby-dev
```

6. **Nasazení**
```bash
git push heroku main
```

7. **Inicializace databáze**
```bash
heroku run python init_db.py
```

8. **Aplikace je dostupná na**
```
https://jmeno-aplikace.herokuapp.com
```

---

### Varianta 2: DigitalOcean (více kontroly)

#### Předpoklady
- DigitalOcean účet
- Droplet s Ubuntu 20.04+
- SSH přístup

#### Kroky

1. **Vytvoření Droplet**
   - Vytvořte nový Droplet s Ubuntu 20.04
   - Vyberte velikost podle potřeby (2GB RAM minimum)

2. **Připojení SSH**
```bash
ssh root@your_droplet_ip
```

3. **Instalace závislostí**
```bash
apt update
apt upgrade -y
apt install -y python3 python3-pip python3-venv git nginx supervisor
```

4. **Klonování aplikace**
```bash
cd /var/www
git clone <repository-url> library_budget
cd library_budget
```

5. **Vytvoření virtuálního prostředí**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

6. **Inicializace databáze**
```bash
python init_db.py
```

7. **Konfigurace Supervisor**
```bash
# Vytvořte /etc/supervisor/conf.d/library_budget.conf
cat > /etc/supervisor/conf.d/library_budget.conf << EOF
[program:library_budget]
directory=/var/www/library_budget
command=/var/www/library_budget/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 app:app
autostart=true
autorestart=true
stderr_logfile=/var/log/library_budget/err.log
stdout_logfile=/var/log/library_budget/out.log
EOF

mkdir -p /var/log/library_budget
```

8. **Konfigurace Nginx**
```bash
cat > /etc/nginx/sites-available/library_budget << EOF
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

ln -s /etc/nginx/sites-available/library_budget /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

9. **SSL certifikát (Let's Encrypt)**
```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d your_domain.com
```

10. **Spuštění aplikace**
```bash
supervisorctl reread
supervisorctl update
supervisorctl start library_budget
```

---

### Varianta 3: Docker (kontejner)

#### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalace systémových závislostí
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Kopírování requirements a instalace Python balíčků
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Kopírování aplikace
COPY . .

# Inicializace databáze
RUN python init_db.py

# Spuštění aplikace
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]

EXPOSE 5000
```

#### Docker Compose
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      FLASK_ENV: production
      SECRET_KEY: your-secret-key-here
    volumes:
      - ./library_budget.db:/app/library_budget.db
```

#### Spuštění
```bash
docker-compose up -d
```

---

## Bezpečnostní opatření pro produkci

### 1. Tajné klíče
```python
# config.py
import os
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY není nastavena!")
```

### 2. HTTPS
```python
# app.py
from flask_talisman import Talisman
Talisman(app)
```

### 3. Databázové zálohy
```bash
# Automatické zálohování
0 2 * * * pg_dump -U user dbname > /backups/db_$(date +\%Y\%m\%d).sql
```

### 4. Monitoring
- Nastavte error notifications (e.g., Sentry)
- Logujte všechny aktivity
- Sledujte výkon aplikace

### 5. Autentizace
```python
# app.py - přidejte login
from flask_login import LoginManager

login_manager = LoginManager()
login_manager.init_app(app)
```

## Backupy a obnova

### Heroku
```bash
# Zálohování databáze
heroku pg:backups capture
heroku pg:backups download

# Obnovení
heroku pg:backups restore <backup-id>
```

### DigitalOcean
```bash
# Zálohování SQLite
cp library_budget.db /backups/library_budget_$(date +%Y%m%d_%H%M%S).db

# Obnovení
cp /backups/library_budget_20240101_120000.db library_budget.db
```

## Monitoring a údržba

### Kontrola stavů
```bash
# Heroku
heroku logs --tail

# DigitalOcean
tail -f /var/log/library_budget/err.log
tail -f /var/log/library_budget/out.log
```

### Aktualizace aplikace
```bash
# Heroku
git push heroku main

# DigitalOcean
cd /var/www/library_budget
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
supervisorctl restart library_budget
```

## Propojení domény

### DNS nastavení
```
your_domain.com  A  123.45.67.89     (IP vaší aplikace)
www              CNAME  your_domain.com
```

## Škálování pro více uživatelů

1. **Load Balancer** - Nginx/HAProxy
2. **Database** - PostgreSQL (místo SQLite)
3. **Cache** - Redis
4. **CDN** - CloudFlare
5. **Storage** - S3 (pro soubory)

## Kontakt na podporu

- Heroku Support: support@heroku.com
- DigitalOcean Community: community.digitalocean.com
- GitHub: issues/discussions v repozitáři
