# 🏪 Micu's Market

**Micu's Market** este o platformă modernă de tip marketplace local (anunțuri de mică publicitate), dezvoltată în Python folosind framework-ul **Django**. Platforma permite utilizatorilor să publice anunțuri, să comunice securizat prin chat, să își salveze anunțurile favorite și să își acorde recenzii reciproce pentru tranzacții.

---

## 🚀 Caracteristici Principale

### 🔐 Autentificare & Securitate (Allauth)
* **Autentificare pe bază de Email:** Logarea se face exclusiv prin adresă de email validă și unică.
* **Verificare Obligatorie:** Utilizatorii trebuie să își confirme adresa de email pentru a activa contul.
* **Securitate Sporită:** Criptare parole cu Argon2, indicator de putere a parolei la înregistrare/resetare și rate-limiting pe login, signup și trimiteri de email.
* **Protecții CSRF & Metodă POST:** Deconectarea (logout) și ștergerile se fac exclusiv prin cereri POST pentru a preveni atacurile de deconectare forțată.

### 📦 Gestiune Anunțuri (Listings)
* **Creare & Editare completă:** Utilizatorii pot adăuga detalii ca: titlu, descriere, preț, negociabilitate, stare produs, locație (oraș/județ) și date de contact.
* **Imagini Multiple:** Suport pentru încărcare de până la 10 imagini per anunț, cu validare strictă server-side a extensiilor și dimensiunii imaginii (folosind Pillow).
* **Filtrare Avansată:** Sortare și filtrare după categorii/subcategorii ierarhice, plajă de preț, județ/oraș și căutare textuală.

### 💬 Sistem de Chat & Atașamente
* **Conversații AJAX:** Trimitere și primire mesaje direct din pagină, cu mesaje automate de întâmpinare la inițierea contactului.
* **Atașamente Securizate:** Permite atașarea de imagini sau documente (PDF, Word, Excel, TXT) cu limite stricte de securitate (max. 10MB per fișier și verificare integritate imagini).
* **Notificări inbox:** Contorizarea mesajelor necitite.

### ⭐ Recenzii & Rating-uri
* **Feedback Tranzacțional:** Cumpărătorii și vânzătorii își pot acorda note (1-5 stele) asociate unui anunț specific.
* **Răspunsuri la Recenzii:** Utilizatorii recenzați pot adăuga un singur răspuns oficial la recenzia primită.
* **Prevenire Abuse:** Sistemul blochează auto-recenziile (self-review), recenziile duplicate și permite limitarea frecvenței acestora.

### 🔔 Notificări & Favorite
* **Sistem de Notificări:** Alerte vizuale pentru mesaje noi sau recenzii primite.
* **Listă Favorite:** Salvarea anunțurilor de interes direct în contul de utilizator.

---

## 🛠️ Stack Tehnologic

* **Backend:** Python / Django (vezi versiunile fixate în `requirements.txt`)
* **Bază de date:** PostgreSQL
* **Chat:** HTTP/AJAX, fără WebSockets active în configurația curentă
* **Server Web (Producție):** Gunicorn cu Uvicorn Workers (`uvicorn.workers.UvicornWorker`)
* **Fișiere Statice:** WhiteNoise (comprimare și caching)
* **Validări imagini:** Pillow (PIL)

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
Creați un fișier numit `.env` în rădăcina proiectului (lângă `manage.py`) și adăugați datele de configurare. Model de configurare:

```env
# Django Settings
DJANGO_SECRET_KEY="cheie_secreta_pentru_dezvoltare"
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

# Configurare Bază de date (PostgreSQL)
DB_NAME=micu_market
DB_USER=micu
DB_PASS=parola_bazei_de_date
DB_HOST=127.0.0.1
DB_PORT=5432

# Setări Email (SMTP/cPanel)
EMAIL_HOST=mail.domeniu.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=market@domeniu.com
EMAIL_HOST_PASSWORD=parola_email
DEFAULT_FROM_EMAIL="Micu Market <market@domeniu.com>"
SERVER_EMAIL=server@domeniu.com
```

### 5. Rularea migrărilor și pornirea serverului
```bash
# Aplicați migrările pe baza de date
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

## 🧪 Rularea Testelor Unitare

Pentru a rula suita de teste fără să depindeți de valorile din `.env` local:

```bash
python manage.py test --settings=Micu_market.settings_test
```

În mediul local din acest repo, `python` poate lipsi din PATH; folosiți `venv/bin/python` după activarea sau crearea mediului virtual.

---

## 🌐 Configurare Producție

În producție, aplicația folosește fișierul `settings_production.py` pentru optimizări de performanță și securitate:
* Cererile non-HTTPS sunt redirecționate automat (SSL redirect activ).
* Autentificarea cookie utilizează flag-urile `SECURE` și `HTTPONLY`.
* Pentru pornirea serviciului se folosește Gunicorn configurat cu Uvicorn:
  ```bash
  gunicorn -c gunicorn.conf.py Micu_market.asgi:application
  ```
