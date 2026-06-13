# Micu Market Roadmap

## Starea verificata local

Data verificarii: 2026-06-13.

Comenzi rulate:

```bash
venv/bin/python manage.py check --settings=Micu_market.settings
DJANGO_DEBUG=1 venv/bin/python manage.py test --settings=Micu_market.settings
```

Rezultat:

- `manage.py check`: OK.
- `manage.py test`: 49 teste, OK cu `DJANGO_DEBUG=1`.
- Fara `DJANGO_DEBUG=1`, testele locale primesc redirect `301` spre HTTPS deoarece `.env` local activeaza comportament de productie.

## Corectii fata de auditul initial

- Proiectul are teste automate in `accounts`, `api`, `chat`, `favorites`, `listings`, `pages` si `reviews`.
- CI exista in `.github/workflows/ci.yml` si ruleaza check-uri Django, migrari, teste si `pip-audit`.
- Rate limiting exista deja partial prin `django-ratelimit` in chat, listings si reviews.
- Chat-ul are suport pentru atasamente private prin `MessageAttachment`.
- Email templates pentru allauth exista in `templates/account/email/`.
- `is_featured` exista pe `Listing`, dar fluxul de promovare/monetizare nu este implementat.
- WebSocket/Channels nu este activ in configuratia reproductibila: app-ul `ws` exista, dar nu este in `INSTALLED_APPS`, iar dependintele Channels/Redis nu sunt declarate in `requirements.txt`.
- Exista o discrepanta intre `requirements.txt` si mediul local: requirements cere `Django==6.0.6`, iar `venv` are `Django==5.2.15`.

## Prioritati

### P0 - Stabilizare si reproductibilitate

1. Alinierea dependintelor:
   - decizie explicita intre Django 5.2 LTS si Django 6.x;
   - actualizare `requirements.txt`;
   - eliminarea dependintelor implicite din `venv` care nu sunt documentate.
2. Separarea clara intre setarile de development, test si productie:
   - testele trebuie sa ruleze predictibil fara sa depinda de `.env` local;
   - HTTPS redirect sa ramana activ in productie, dar sa nu mascheze rezultatele testelor locale.
3. Actualizarea README si runbook-ului pentru comenzi reale de setup, test si deploy.

### P1 - Siguranta produsului

1. Audit pentru upload-uri:
   - validare MIME reala, nu doar extensie;
   - limite clare pentru numar, marime si tipuri de fisiere;
   - teste pentru atasamente invalide.
2. Protectie anti-abuz:
   - rate limit pe API create/toggle, contact si notificari sensibile;
   - throttling pentru view count;
   - jurnalizare pentru actiuni administrative si moderare.
3. Raportare anunturi:
   - model dedicat;
   - UI pentru raportare;
   - coada de moderare in admin.

### P2 - Conversie marketplace

1. Promovare anunturi:
   - stari si intervale pentru `is_featured`;
   - dashboard pentru vanzator;
   - integrare ulterioara cu plati.
2. Incredere intre utilizatori:
   - flux de verificare profil;
   - badge-uri consistente;
   - criterii clare pentru recenzii dupa interactiuni reale.
3. SEO si indexare:
   - meta tags per listing/category;
   - `sitemap.xml`;
   - `robots.txt`;
   - structured data pentru anunturi.

### P3 - Experienta utilizator

1. Optimizare imagini:
   - lazy loading in template-uri;
   - dimensiuni responsive;
   - placeholder-uri consecvente.
2. Feedback vizual:
   - skeleton states pentru liste si carduri;
   - empty states mai actionabile;
   - micro-interactiuni pe favorite, chat si formulare.
3. Dashboard seller:
   - grafice reale pentru views/favorites;
   - trenduri pe 7/30 zile;
   - insight-uri pe anunt.

### P4 - Functionalitati avansate

1. Realtime:
   - activare Channels doar daca exista nevoie clara;
   - Redis si worker setup documentat;
   - fallback AJAX pastrat.
2. API matur:
   - decizie intre API manual si DRF;
   - autentificare token/session explicita;
   - paginare si erori standardizate.
3. Internationalizare:
   - extragerea textelor hardcodate;
   - limba romana ca default;
   - pregatire pentru engleza.

## Prima etapa recomandata

Prima etapa practica este P0:

1. Introducem setari de test predictibile.
2. Aliniem README cu starea reala.
3. Stabilim versiunea Django tinta.
4. Rulam testele si CI local cat permite mediul.
5. Facem commit scurt pentru fiecare bucata stabila.
