# 🏪 Micu's Market

**Micu's Market** este o platformă modernă de tip marketplace local (anunțuri de mică publicitate), dezvoltată în Python folosind framework-ul **Django**. Platforma permite utilizatorilor să publice anunțuri, să comunice în timp real prin chat, să își salveze anunțurile favorite și să își acorde recenzii reciproce pentru tranzacții.

---

## 🚀 Caracteristici Principale

### 🔐 Autentificare & Securitate (Allauth)
* **Autentificare pe bază de Email:** Logarea se face exclusiv prin adresă de email validă și unică.
* **Verificare Obligatorie:** Utilizatorii trebuie să își confirme adresa de email pentru a activa contul.
* **Securitate Sporită:** Criptare parole cu Argon2, indicator de putere a parolei la înregistrare/resetare și rate-limiting pe login, signup și trimiteri de email.
* **Protecții CSRF & Metodă POST:** Deconectarea (logout) și ștergerile se fac exclusiv prin cereri POST pentru a preveni atacurile de deconectare forțată.
* **Hardening:** URL de admin configurabil, security headers (HSTS, X-Frame, CSP), audit logging, IP real restaurat din Cloudflare pentru rate-limiting corect.

### 📦 Gestiune Anunțuri (Listings)
* **Creare & Editare completă:** Utilizatorii pot adăuga detalii ca: titlu, descriere, preț, negociabilitate, stare produs, locație (oraș/județ) și date de contact.
* **Imagini Multiple:** Suport pentru încărcare de până la 10 imagini per anunț, cu validare strictă server-side a extensiilor și dimensiunii imaginii (folosind Pillow).
* **Filtrare Avansată:** Sortare și filtrare după categorii/subcategorii ierarhice, plajă de preț, județ/oraș și căutare textuală.

### 💬 Chat în Timp Real (WebSocket)
* **Mesaje live prin WebSocket** (Django Channels + layer Redis): mesaje, indicator de „scrie…" real și confirmări de citire (✓✓), fără reîncărcarea paginii.
* **Atașamente Securizate:** Imagini sau documente (PDF, Word, Excel, TXT) cu limite stricte (max. 10MB per fișier, verificare integritate imagini). Atașamentele sunt private — servite doar de Django, după verificarea participării la conversație.
* **Fallback robust:** dacă WebSocket-ul nu e disponibil, trimiterea cade automat pe AJAX; mesajele cu atașamente folosesc tot AJAX dar apar live la ambii participanți.
* **Notificări inbox:** contorizarea mesajelor necitite.

### ⭐ Recenzii & Rating-uri
* **Feedback Tranzacțional:** Cumpărătorii și vânzătorii își pot acorda note (1-5 stele) asociate unui anunț specific.
* **Răspunsuri la Recenzii:** Utilizatorii recenzați pot adăuga un singur răspuns oficial la recenzia primită.
* **Prevenire Abuse:** Sistemul blochează auto-recenziile (self-review), recenziile duplicate și permite limitarea frecvenței acestora.

### 🔔 Notificări & Favorite
* **Sistem de Notificări:** Alerte vizuale pentru mesaje noi sau recenzii primite, cu dispecer de email pe fundal.
* **Listă Favorite:** Salvarea anunțurilor de interes direct în contul de utilizator.

### 🎨 Design & UX
* **Sistem de design pe token-uri** (`static/css/tokens.css`): paletă unitară (accent teal), spațiere, raze, umbre — sursă unică pentru tot CSS-ul.
* **Dark mode** cu buton de comutare în header (persistat în localStorage, fără flash la încărcare).
* **PWA:** manifest, service worker și pagină offline. Font Awesome este self-hosted (fără CDN).

### 🔎 SEO
* `sitemap.xml` (pagini statice + anunțuri active) și `robots.txt` generate dinamic.
* Meta tags OG/Twitter, canonical și structured data în template-ul de bază.

---

## 🛠️ Stack Tehnologic

* **Backend:** Python / Django (vezi versiunile fixate în `requirements.txt`)
* **Bază de date:** PostgreSQL (conexiuni persistente cu `CONN_MAX_AGE`)
* **Real-time:** Django Channels + `channels-redis` (layer Redis pentru WebSocket)
* **Cache & rate-limit & channel layer:** Redis
* **Server Web (Producție):** Gunicorn cu worker ASGI `uvicorn_worker.UvicornWorker`
* **Reverse proxy:** nginx (unix socket + bloc `/ws/` pentru WebSocket), în spatele Cloudflare
* **Fișiere Statice:** WhiteNoise (comprimare, caching, manifest hash-uit)
* **Validări imagini:** Pillow (PIL)
* **Backup offsite:** Cloudflare R2 (S3-compatibil) via boto3

---

## 💻 Instalare și Configurare Locală

### 1. Clonarea proiectului
```bash
git clone <url-repository>
cd Micu_market
```

### 2. Crearea și activarea mediului virtual
```bash
python3 -m venv venv
source venv/bin/activate  # Pe Linux/macOS
# sau
venv\Scripts\activate     # Pe Windows
```

### 3. Instalarea dependențelor
```bash
pip install -r requirements.txt
```

### 4. Configurarea variabilelor de mediu
Copiați `.env.example` în `.env` și completați valorile. `.env.example` conține toate cheile (Django, DB, Redis, email, R2, storage). Minim pentru dezvoltare:

```env
DJANGO_SECRET_KEY="cheie_secreta_pentru_dezvoltare"
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=micu_market
DB_USER=micu
DB_PASS=parola_bazei_de_date
DB_HOST=127.0.0.1
DB_PORT=5432

# Redis (cache + channel layer pentru chat real-time).
# Fără Redis local, pentru dezvoltare/teste poți forța channel layer in-memory:
CHANNELS_IN_MEMORY=1
```

### 5. Rularea migrărilor și pornirea serverului
```bash
python manage.py migrate

# (Opțional) Populați categoriile implicite
python populate_categories_script.py

# Creați un cont de administrator (Superuser)
python manage.py createsuperuser

# Porniți serverul de dezvoltare
python manage.py runserver
```
Aplicația va fi accesibilă la adresa `http://127.0.0.1:8000/`.

---

## 🧪 Teste & CI

Rulați suita de teste fără să depindeți de `.env` local (channel layer in-memory, fără Redis):

```bash
python manage.py test --settings=Micu_market.settings_test
```

În mediul local din acest repo, `python` poate lipsi din PATH; folosiți `venv/bin/python`.

CI (GitHub Actions, `.github/workflows/ci.yml`) rulează pe fiecare push/PR: `manage.py check`, verificare migrații necomise, suita de teste (Python 3.13 & 3.14), `pip-audit`, `bandit` și `check --deploy`.

---

## 🌐 Configurare Producție

Producția folosește `settings_production.py` (SSL redirect, cookie `SECURE`/`HTTPONLY`, HSTS, conexiuni DB persistente). Componente:

* **Aplicație:** serviciu systemd care rulează Gunicorn + worker ASGI peste un unix socket:
  ```bash
  gunicorn -c gunicorn.conf.py Micu_market.asgi:application
  ```
* **nginx:** servește static/media, proxy către socket și un bloc `location /ws/` cu header-ele de upgrade pentru WebSocket. Atașamentele de chat (`/media/chat/`) sunt blocate la nivel nginx (servite doar de Django, cu autorizare). Vezi `deploy/nginx/` și `deploy/cloudflare-nginx.md`.
* **Redis** (cache, rate-limit, channel layer) și **PostgreSQL** ca servicii.
* **Timere systemd** (`deploy/systemd/`): backup zilnic, worker de joburi, dispecer email-uri și cleanup media. Backup-ul face dump local **și** upload offsite în Cloudflare R2 (`scripts/backup_postgres.sh` + `scripts/r2_upload.py`, activat de `R2_ENABLED=1`).
* **Health check:** `GET /healthz` verifică DB + cache și întoarce `503` dacă pică ceva (potrivit pentru un monitor de uptime).

Pași de deploy și operare: vezi `deploy/ops-runbook.md`.

---

## 📄 Licență

Vezi fișierul `LICENSE`.
