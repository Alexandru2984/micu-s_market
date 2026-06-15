import os
import random
import urllib.request
from urllib.parse import urlparse
from io import BytesIO
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.db import transaction
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image, ImageDraw, ImageFont

from categories.models import Category
from listings.models import Listing, ListingImage
from accounts.models import UserProfile

User = get_user_model()


def get_image_keyword_for_listing(title, category_name):
    title_lower = title.lower()
    if "iphone" in title_lower:
        return "iphone"
    elif "samsung" in title_lower:
        return "samsung,phone"
    elif "macbook" in title_lower:
        return "macbook"
    elif "lenovo" in title_lower or "laptop" in title_lower:
        return "laptop"
    elif "playstation" in title_lower or "ps5" in title_lower:
        return "playstation,console"
    elif "tv" in title_lower or "televizor" in title_lower:
        return "television"
    elif "dvr" in title_lower or "cameră auto" in title_lower:
        return "dashcam"
    elif "audi" in title_lower or "bmw" in title_lower or "golf" in title_lower or "logan" in title_lower or "volkswagen" in title_lower or "dacia" in title_lower:
        return "car"
    elif "jante" in title_lower:
        return "rims"
    elif "canapea" in title_lower:
        return "sofa"
    elif "masă" in title_lower or "dining" in title_lower:
        return "table"
    elif "espressor" in title_lower or "delonghi" in title_lower:
        return "espresso,coffee"
    elif "roborock" in title_lower or "aspirator" in title_lower:
        return "vacuum"
    elif "geacă" in title_lower or "haine" in title_lower:
        return "jacket"
    elif "bicicletă" in title_lower:
        return "bicycle"
    elif "lego" in title_lower:
        return "lego"
    elif "dune" in title_lower or "sapiens" in title_lower or "carte" in title_lower:
        return "book"
    elif "adidași" in title_lower or "incaltaminte" in title_lower:
        return "sneakers"
    elif "ceas" in title_lower or "fenix" in title_lower:
        return "smartwatch"
    elif "scaun" in title_lower:
        return "babycarseat"
    elif "chitară" in title_lower or "yamaha" in title_lower:
        return "guitar"
    elif "hrană" in title_lower:
        return "dogfood"
    elif "monopoly" in title_lower:
        return "boardgame"
    elif "ratan" in title_lower or "gradina" in title_lower:
        return "patio"
    elif "bosch" in title_lower or "masina de insurubat" in title_lower:
        return "drill"
    
    cat_lower = category_name.lower()
    if "telefoane" in cat_lower:
        return "phone"
    elif "laptopuri" in cat_lower:
        return "laptop"
    elif "auto" in cat_lower:
        return "car"
    elif "mobilier" in cat_lower:
        return "furniture"
    elif "haine" in cat_lower:
        return "clothing"
    elif "biciclete" in cat_lower:
        return "bicycle"
    elif "jucarii" in cat_lower:
        return "toy"
    elif "carti" in cat_lower:
        return "book"
    elif "muzicale" in cat_lower:
        return "music"
    elif "animale" in cat_lower:
        return "pet"
    return "object"


def download_real_image_bytes(keyword):
    url = f"https://loremflickr.com/800/600/{keyword}"
    parsed_url = urlparse(url)
    if parsed_url.scheme != "https" or parsed_url.netloc != "loremflickr.com":
        raise ValueError("Sursa imaginii demo nu este permisă.")
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    )
    with urllib.request.urlopen(req, timeout=15) as response:  # nosec B310
        return response.read()



def get_font(size=72):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_img_bytes(title, subtitle=""):
    W, H = 1200, 800
    img = Image.new("RGB", (W, H), (230, 232, 236))
    d = ImageDraw.Draw(img)

    # Large centered title, scaled to fit
    f = get_font(96)
    while d.textlength(title, font=f) > W - 160 and getattr(f, "size", 96) > 36:
        f = get_font(getattr(f, "size", 96) - 6)
    tw = d.textlength(title, font=f)
    try:
        th = f.getbbox(title)[3] - f.getbbox(title)[1]
    except Exception:
        th = 100
    x = (W - tw) // 2
    y = H // 2 - th
    d.text((x, y), title, font=f, fill=(30, 30, 30))

    if subtitle:
        f2 = get_font(max(36, int(getattr(f, "size", 96) * 0.5)))
        tw2 = d.textlength(subtitle, font=f2)
        d.text(((W - tw2) // 2, y + th + 20), subtitle, font=f2, fill=(90, 90, 90))

    # Watermark
    f3 = get_font(24)
    d.text((W - 240, H - 40), "Micu’s Market", font=f3, fill=(120, 124, 130))

    buf = BytesIO()
    img.save(buf, "JPEG", quality=88)
    return buf.getvalue()


class Command(BaseCommand):
    help = "Populează baza de date cu categorii, utilizatori fictivi, anunțuri și imagini de tip placeholder."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Șterge toate anunțurile și utilizatorii fictivi existenți înainte de populare.",
        )
        parser.add_argument(
            "--user-password",
            default=os.getenv("POPULATE_DB_USER_PASSWORD"),
            help="Parola pentru utilizatorii fictivi. Dacă lipsește, conturile primesc parolă inutilizabilă.",
        )

    def handle(self, *args, **options):
        clear_existing = options["clear"]
        seed_user_password = options["user_password"]

        if clear_existing:
            self.stdout.write(self.style.WARNING("🗑️  Ștergem datele existente..."))
            # Delete only the fixture listings and users (but keep superusers)
            Listing.objects.all().delete()
            User.objects.filter(is_superuser=False).exclude(username="alex_mihai984").delete()
            self.stdout.write(self.style.SUCCESS("✅ Datele existente au fost șterse."))

        # ---------------------------------------------------------
        # 1. Define category data (source: populate_categories_script.py)
        # ---------------------------------------------------------
        categories_data = {
            'Electronice': {
                'icon': 'fas fa-laptop',
                'description': 'Telefoane, laptopuri, televizoare și alte gadget-uri',
                'subcategories': [
                    'Telefoane Mobile',
                    'Laptopuri & Computere',
                    'Televizoare',
                    'Audio & Video',
                    'Console & Gaming',
                    'Accesorii Electronice',
                    'Camere Foto',
                    'Smart Home',
                ]
            },
            'Auto & Moto': {
                'icon': 'fas fa-car',
                'description': 'Mașini, motociclete și piese auto',
                'subcategories': [
                    'Autoturisme',
                    'Motociclete',
                    'Piese Auto',
                    'Anvelope',
                    'Accesorii Auto',
                    'Camioane & Utilitare',
                    'ATV & Scutere',
                ]
            },
            'Casă & Grădină': {
                'icon': 'fas fa-home',
                'description': 'Mobilier, decorațiuni și articole pentru grădină',
                'subcategories': [
                    'Mobilier',
                    'Decorațiuni',
                    'Electrocasnice',
                    'Grădină & Exterior',
                    'Scule & DIY',
                    'Iluminat',
                    'Textile & Covoare',
                ]
            },
            'Modă & Beauty': {
                'icon': 'fas fa-tshirt',
                'description': 'Îmbrăcăminte, încălțăminte și produse de înfrumusețare',
                'subcategories': [
                    'Îmbrăcăminte Femei',
                    'Îmbrăcăminte Bărbați',
                    'Încălțăminte',
                    'Accesorii Fashion',
                    'Bijuterii & Ceasuri',
                    'Produse de Beauty',
                    'Parfumuri',
                ]
            },
            'Sport & Hobby': {
                'icon': 'fas fa-dumbbell',
                'description': 'Echipamente sportive, hobby și timp liber',
                'subcategories': [
                    'Fitness & Gym',
                    'Biciclete',
                    'Sporturi de Iarnă',
                    'Sporturi Acvatice',
                    'Echipament Outdoor',
                    'Hobby & Colecții',
                    'Instrumente Muzicale',
                ]
            },
            'Copii & Bebeluși': {
                'icon': 'fas fa-baby',
                'description': 'Produse pentru copii și bebeluși',
                'subcategories': [
                    'Îmbrăcăminte Copii',
                    'Jucării',
                    'Cărți & Educație',
                    'Produse pentru Bebeluși',
                    'Cărucioare & Scaune Auto',
                    'Mobilier Copii',
                ]
            },
            'Cărți & Educație': {
                'icon': 'fas fa-book',
                'description': 'Cărți, materiale educaționale și cursuri',
                'subcategories': [
                    'Cărți Fiction',
                    'Cărți Non-Fiction',
                    'Manuale Școlare',
                    'Cursuri Online',
                    'Materiale Educative',
                    'Reviste',
                ]
            },
            'Servicii': {
                'icon': 'fas fa-tools',
                'description': 'Diverse servicii profesionale',
                'subcategories': [
                    'Servicii IT',
                    'Reparații',
                    'Curățenie',
                    'Transport',
                    'Evenimente',
                    'Consultanță',
                    'Design & Marketing',
                ]
            },
            'Animale': {
                'icon': 'fas fa-paw',
                'description': 'Animale de companie și accesorii',
                'subcategories': [
                    'Câini',
                    'Pisici',
                    'Păsări',
                    'Pești & Acvariu',
                    'Animale Mici',
                    'Hrană Animale',
                    'Accesorii Animale',
                ]
            },
            'Altele': {
                'icon': 'fas fa-ellipsis-h',
                'description': 'Diverse produse și servicii',
                'subcategories': [
                    'Antichități',
                    'Artă & Artizanat',
                    'Materiale Construcții',
                    'Echipamente Industriale',
                    'Diverse',
                ]
            }
        }

        self.stdout.write("📂 Populare / Verificare categorii...")
        with transaction.atomic():
            order = 0
            for category_name, category_data in categories_data.items():
                main_category, created = Category.objects.get_or_create(
                    name=category_name,
                    defaults={
                        'slug': slugify(category_name),
                        'description': category_data['description'],
                        'icon': category_data['icon'],
                        'order': order,
                        'is_active': True,
                    }
                )
                
                sub_order = 0
                for sub_name in category_data['subcategories']:
                    Category.objects.get_or_create(
                        name=sub_name,
                        defaults={
                            'slug': slugify(sub_name),
                            'parent': main_category,
                            'order': sub_order,
                            'is_active': True,
                        }
                    )
                    sub_order += 1
                order += 1
        self.stdout.write(self.style.SUCCESS("✅ Categorii populate cu succes."))

        # ---------------------------------------------------------
        # 2. Creare utilizatori fictivi
        # ---------------------------------------------------------
        self.stdout.write("👤 Creare / Actualizare utilizatori...")
        users_data = [
            {
                'username': 'alex_mihai984',
                'email': 'alex_mihai984@yahoo.com',
                'first_name': 'Alexandru',
                'last_name': 'Mihai',
                'phone': '0721123456',
                'city': 'București',
                'county': 'București',
                'bio': 'Pasionat de tehnologie și gadgeturi noi. Vând doar lucruri personale, bine întreținute.'
            },
            {
                'username': 'maria_popescu',
                'email': 'maria.popescu@gmail.com',
                'first_name': 'Maria',
                'last_name': 'Popescu',
                'phone': '0732987654',
                'city': 'Cluj-Napoca',
                'county': 'Cluj',
                'bio': 'Designer de interior și iubitoare de plante. Vând mobilă și accesorii home-decor.'
            },
            {
                'username': 'vlad_ionescu',
                'email': 'vlad.ionescu@gmail.com',
                'first_name': 'Vlad',
                'last_name': 'Ionescu',
                'phone': '0743555666',
                'city': 'Iași',
                'county': 'Iași',
                'bio': 'Pasionat de mașini și mecanică. Din când în când vând piese auto de calitate sau accesorii.'
            },
            {
                'username': 'elena_nistor',
                'email': 'elena.nistor@gmail.com',
                'first_name': 'Elena',
                'last_name': 'Nistor',
                'phone': '0754111222',
                'city': 'Timișoara',
                'county': 'Timiș',
                'bio': 'Mamă a doi copii minunați. Vând haine de copii rămase mici, jucării și articole utile pentru bebeluși.'
            },
            {
                'username': 'andrei_gabor',
                'email': 'andrei.g@yahoo.com',
                'first_name': 'Andrei',
                'last_name': 'Gabor',
                'phone': '0765999888',
                'city': 'Brașov',
                'county': 'Brașov',
                'bio': 'Iubitor de munte, sport în aer liber și muzică. Vând echipamente sportive, biciclete și instrumente muzicale.'
            }
        ]

        user_objects = {}
        for u_info in users_data:
            user, created = User.objects.get_or_create(
                username=u_info['username'],
                defaults={
                    'email': u_info['email'],
                    'first_name': u_info['first_name'],
                    'last_name': u_info['last_name'],
                }
            )
            if created:
                if seed_user_password:
                    user.set_password(seed_user_password)
                else:
                    user.set_unusable_password()
                user.save()
                self.stdout.write(f"   + Creat utilizatorul {user.username}")
            else:
                self.stdout.write(f"   ~ Utilizatorul {user.username} există deja")

            # Update or create the associated profile
            profile, p_created = UserProfile.objects.get_or_create(user=user)
            profile.phone = u_info['phone']
            profile.city = u_info['city']
            profile.county = u_info['county']
            profile.bio = u_info['bio']
            profile.is_verified = True
            profile.save()
            user_objects[user.username] = user

        self.stdout.write(self.style.SUCCESS("✅ Utilizatori și profile configurate."))

        # ---------------------------------------------------------
        # 3. Create listings
        # ---------------------------------------------------------
        self.stdout.write("📦 Populare anunțuri...")
        listings_data = [
            {
                'title': "iPhone 14 Pro Max 256GB - Stare Perfectă",
                'description': "Vând iPhone 14 Pro Max, stocare 256GB, culoare Deep Purple. Telefonul arată și funcționează impecabil, sănătatea bateriei este de 92%. Vine însoțit de cutia originală, cablu de încărcare și 2 huse cadou. A fost ținut mereu în husă și cu folie de sticlă pe ecran. Fără schimburi.",
                'price': 3800.00,
                'condition': "like_new",
                'category_name': "Telefoane Mobile",
                'negotiable': True,
                'city': "București",
                'county': "București",
                'contact_phone': "0721123456",
                'owner_username': "alex_mihai984"
            },
            {
                'title': "Samsung Galaxy S23 Ultra 512GB Phantom Black",
                'description': "Telefon personal Samsung Galaxy S23 Ultra, varianta de 512GB stocare și 12GB RAM. Culoare Phantom Black. Se prezintă în stare foarte bună, mici urme normale de utilizare pe ramă. Ecranul este perfect, fără zgârieturi. Vine cu încărcător original de 45W inclus.",
                'price': 3500.00,
                'condition': "good",
                'category_name': "Telefoane Mobile",
                'negotiable': True,
                'city': "București",
                'county': "București",
                'contact_phone': "0721123456",
                'owner_username': "alex_mihai984"
            },
            {
                'title': "MacBook Pro 14 M2 Pro (2023) 16GB RAM 512GB",
                'description': "Vând MacBook Pro 14 inch cu procesor M2 Pro, 16GB RAM și 512GB SSD. Laptopul a fost folosit doar la birou în regim de desktop. Cicluri baterie: 85, sănătate baterie: 98%. Nu prezintă nicio zgârietură sau problemă de funcționare. Vine cu cutie și încărcător original.",
                'price': 6900.00,
                'condition': "like_new",
                'category_name': "Laptopuri & Computere",
                'negotiable': False,
                'city': "București",
                'county': "București",
                'contact_phone': "0721123456",
                'owner_username': "alex_mihai984"
            },
            {
                'title': "Laptop Gaming Lenovo Legion 5 Pro RTX 3070",
                'description': "Laptop Gaming Lenovo Legion 5 Pro în stare excepțională. Specificații: Ecran QHD 165Hz, Procesor AMD Ryzen 7 5800H, 16GB RAM DDR4, SSD 1TB, Placă video NVIDIA RTX 3070 8GB (TGP maxim). Rulează orice joc recent la detalii ultra. Schimbat recent pasta termică.",
                'price': 4200.00,
                'condition': "good",
                'category_name': "Laptopuri & Computere",
                'negotiable': True,
                'city': "București",
                'county': "București",
                'contact_phone': "0721123456",
                'owner_username': "alex_mihai984"
            },
            {
                'title': "Volkswagen Golf VII 2.0 TDI BlueMotion 2018",
                'description': "Proprietar, vând Volkswagen Golf VII, an fabricație 2018, motor 2.0 TDI (150 CP), cutie automată DSG. Kilometraj real: 185.000 km, cu istoric complet de service. Dotări: faruri LED, senzori parcare 360, navigație mare cu ecran tactil, climă pe două zone, scaune încălzite. Stare mecanică și estetică excelentă.",
                'price': 12500.00,
                'condition': "good",
                'category_name': "Autoturisme",
                'negotiable': True,
                'city': "Iași",
                'county': "Iași",
                'contact_phone': "0743555666",
                'owner_username': "vlad_ionescu"
            },
            {
                'title': "Dacia Logan 0.9 TCe + GPL de fabrică 2020",
                'description': "Vând Dacia Logan, an 2020, motor 0.9 TCe benzină + GPL din fabrică. Kilometri la bord: 75.000 km. Foarte economică, consum mic, ideală pentru oraș sau navetă/Uber. Întreținută exemplar, revizii efectuate la fiecare 10.000 km. Aer condiționat funcțional, geamuri electrice față.",
                'price': 7400.00,
                'condition': "good",
                'category_name': "Autoturisme",
                'negotiable': True,
                'city': "Iași",
                'county': "Iași",
                'contact_phone': "0743555666",
                'owner_username': "vlad_ionescu"
            },
            {
                'title': "Set 4 Jante aliaj R17 cu anvelope de vară",
                'description': "Set jante aliaj originale R17, prindere 5x112, în stare foarte bună, nu sunt strâmbe sau sudate. Vin echipate cu anvelope de vară Michelin Primacy 4 (profil 5-6mm), dimensiuni 225/45 R17. Se potrivesc pe gama VW, Audi, Skoda, Seat.",
                'price': 1600.00,
                'condition': "good",
                'category_name': "Piese Auto",
                'negotiable': True,
                'city': "Iași",
                'county': "Iași",
                'contact_phone': "0743555666",
                'owner_username': "vlad_ionescu"
            },
            {
                'title': "Canapea Extensibilă 3 Locuri Velvet Turcoaz",
                'description': "Canapea extensibilă cu 3 locuri, tapițerie din catifea fină turcoaz, picioare din lemn masiv de fag. Dimensiuni: lungime 210cm, lățime 85cm. Sistem de extensie tip click-clack, include lădă de depozitare spațioasă. A fost folosită foarte puțin într-o cameră de oaspeți.",
                'price': 1200.00,
                'condition': "like_new",
                'category_name': "Mobilier",
                'negotiable': True,
                'city': "Cluj-Napoca",
                'county': "Cluj",
                'contact_phone': "0732987654",
                'owner_username': "maria_popescu"
            },
            {
                'title': "Masă de dining din lemn masiv de stejar",
                'description': "Masă modernă din lemn masiv de stejar (blat de 4cm grosime) cu picioare metalice în formă de X, vopsite electrostatic în negru. Dimensiuni blat: 160 x 90 cm. Ideală pentru 6 persoane. Masa este realizată manual și se află în stare impecabilă.",
                'price': 1800.00,
                'condition': "new",
                'category_name': "Mobilier",
                'negotiable': False,
                'city': "Cluj-Napoca",
                'county': "Cluj",
                'contact_phone': "0732987654",
                'owner_username': "maria_popescu"
            },
            {
                'title': "Espressor Automat DeLonghi Magnifica S",
                'description': "Espressor automat DeLonghi Magnifica S, folosit aproximativ 1 an. Funcționează perfect cu cafea boabe sau măcinată. Sistem manual de spumare a laptelui pentru cappuccino cremos. Râșniță silențioasă cu 13 setări. Curățat și decalcifiat periodic.",
                'price': 950.00,
                'condition': "good",
                'category_name': "Electrocasnice",
                'negotiable': True,
                'city': "Cluj-Napoca",
                'county': "Cluj",
                'contact_phone': "0732987654",
                'owner_username': "maria_popescu"
            },
            {
                'title': "Robot de aspirare Roborock S7 - Mop VibraRise",
                'description': "Aspirator robot Roborock S7 în stare foarte bună de funcționare. Dispune de mop cu vibrații ultrasonice și ridicare automată pe covoare, putere de aspirare 2500 Pa, navigație LiDAR precisă. Vine cu stația de încărcare și toate accesoriile originale.",
                'price': 1400.00,
                'condition': "good",
                'category_name': "Electrocasnice",
                'negotiable': True,
                'city': "Cluj-Napoca",
                'county': "Cluj",
                'contact_phone': "0732987654",
                'owner_username': "maria_popescu"
            },
            {
                'title': "Geacă de piele naturală tip biker Zara - M",
                'description': "Geacă din piele naturală de ovine, marca Zara Man, mărimea M. Croială modernă slim-fit, detalii metalice argintii, buzunare cu fermoar. Purtată de maxim 3 ori, se află în stare impecabilă, fără zgârieturi sau semne de uzură.",
                'price': 350.00,
                'condition': "like_new",
                'category_name': "Îmbrăcăminte Bărbați",
                'negotiable': True,
                'city': "Timișoara",
                'county': "Timiș",
                'contact_phone': "0754111222",
                'owner_username': "elena_nistor"
            },
            {
                'title': "Bicicletă MTB Trek Marlin 7 2022",
                'description': "Bicicletă Mountain Bike Trek Marlin 7, model 2022, cadru mărimea L, roți de 29 inch. Transmisie Shimano Deore 1x10 viteze, furcă RockShox Judy cu blocaj, frâne hidraulice pe disc Shimano. Bicicleta a fost folosită doar pe trasee ușoare de pădure, are revizia făcută recent.",
                'price': 2600.00,
                'condition': "good",
                'category_name': "Biciclete",
                'negotiable': True,
                'city': "Brașov",
                'county': "Brașov",
                'contact_phone': "0765999888",
                'owner_username': "andrei_gabor"
            },
            {
                'title': "Set LEGO Star Wars Millennium Falcon 75257",
                'description': "Set LEGO original Star Wars, Millennium Falcon (75257), sigilat, cutie impecabilă. Conține 1351 piese și 7 minifigurine, inclusiv Lando Calrissian, Chewbacca, Finn și R2-D2. Cadoul ideal pentru colecționari sau copii pasionați.",
                'price': 600.00,
                'condition': "new",
                'category_name': "Jucării",
                'negotiable': False,
                'city': "Timișoara",
                'county': "Timiș",
                'contact_phone': "0754111222",
                'owner_username': "elena_nistor"
            },
            {
                'title': "Pachet Cărți Dune (Seria clasică, 6 volume)",
                'description': "Pachet complet format din cele 6 volume ale seriei originale Dune scrise de Frank Herbert (Dune, Mântuirea Dunei, Copiii Dunei, Împăratul-Zeu al Dunei, Ereticii Dunei, Canonicatul Dunei). Ediție cartonată de la editura Nemira. Cărțile sunt necitite, stare impecabilă.",
                'price': 180.00,
                'condition': "new",
                'category_name': "Cărți Fiction",
                'negotiable': False,
                'city': "Brașov",
                'county': "Brașov",
                'contact_phone': "0765999888",
                'owner_username': "andrei_gabor"
            },
            {
                'title': "Consolă PlayStation 5 (PS5) Slim Disc Edition",
                'description': "Vând consolă PlayStation 5 modelul Slim (cu unitate disc), stocare SSD de 1TB. Pachetul conține consola, 1 controler DualSense original, cablu HDMI, cablu de alimentare și jocul God of War Ragnarok pe disc. Cumpărată acum 3 luni, dețin factură și garanție 2 ani.",
                'price': 2100.00,
                'condition': "like_new",
                'category_name': "Console & Gaming",
                'negotiable': False,
                'city': "București",
                'county': "București",
                'contact_phone': "0721123456",
                'owner_username': "alex_mihai984"
            },
            {
                'title': "Aparat Foto Mirrorless Sony Alpha A6400 + Obiectiv 16-50mm",
                'description': "Aparat mirrorless Sony A6400 împreună cu obiectivul de kit 16-50mm f/3.5-5.6 OSS. Perfect pentru vlogging și fotografie de călătorie datorită ecranului rabatabil la 180 de grade și autofocusului ultra-rapid. Număr cadre: 4200 shutter count. Vine cu acumulator original și curea.",
                'price': 3200.00,
                'condition': "like_new",
                'category_name': "Camere Foto",
                'negotiable': True,
                'city': "București",
                'county': "București",
                'contact_phone': "0721123456",
                'owner_username': "alex_mihai984"
            },
            {
                'title': "Căști Wireless Over-Ear Sony WH-1000XM4",
                'description': "Căști wireless Sony WH-1000XM4 cu anulare activă a zgomotului (ANC). Culoare argintiu/gri. Autonomie baterie până la 30 ore. Sunet excepțional, conectare multipoint. Vin însoțite de husă rigidă pentru transport și adaptor pentru avion.",
                'price': 850.00,
                'condition': "good",
                'category_name': "Audio & Video",
                'negotiable': True,
                'city': "București",
                'county': "București",
                'contact_phone': "0721123456",
                'owner_username': "alex_mihai984"
            },
            {
                'title': "Smart TV LG OLED 55C2 139cm 4K 120Hz",
                'description': "Televizor OLED LG din seria C2, diagonală 139 cm (55 inch), rezoluție 4K, ideal pentru console de nouă generație datorită porturilor HDMI 2.1 și ecranului de 120Hz. Culori uimitoare și negru perfect. Stare impecabilă, fără burn-in, folosit moderat.",
                'price': 3900.00,
                'condition': "good",
                'category_name': "Televizoare",
                'negotiable': True,
                'city': "București",
                'county': "București",
                'contact_phone': "0721123456",
                'owner_username': "alex_mihai984"
            },
            {
                'title': "Cameră Auto DVR 70mai Dash Cam Pro Plus+ A500S",
                'description': "Cameră de bord DVR 70mai A500S Pro Plus+, filmare rezoluție 2.7K, modul GPS integrat, monitorizare parcare, ADAS. Vine la pachet cu card MicroSD Sandisk de 64GB special pentru camere auto. Stare perfectă, folosită jumătate de an.",
                'price': 280.00,
                'condition': "good",
                'category_name': "Accesorii Auto",
                'negotiable': True,
                'city': "Iași",
                'county': "Iași",
                'contact_phone': "0743555666",
                'owner_username': "vlad_ionescu"
            },
            {
                'title': "Set Mobilier Grădină / Terasă din Ratan Sintetic",
                'description': "Set mobilier terasă format din masă cu blat de sticlă securizată și 4 scaune cu perne incluse. Structură metalică îmbrăcată în ratan sintetic maro, rezistent la intemperii și raze UV. Dimensiuni compacte, ideală pentru balcon sau grădină.",
                'price': 750.00,
                'condition': "good",
                'category_name': "Grădină & Exterior",
                'negotiable': True,
                'city': "Cluj-Napoca",
                'county': "Cluj",
                'contact_phone': "0732987654",
                'owner_username': "maria_popescu"
            },
            {
                'title': "Mașină de înșurubat și găurit Bosch Professional GSR 18V-50",
                'description': "Filetantă Bosch albastră cu motor brushless (fără perii), cuplu de 50 Nm. Pachetul conține mașina de găurit, 2 acumulatori Li-Ion de 18V 2.0Ah, încărcător rapid și valiză profesională de transport L-CASE. Folosită doar pentru proiecte personale DIY în casă.",
                'price': 550.00,
                'condition': "good",
                'category_name': "Scule & DIY",
                'negotiable': True,
                'city': "Cluj-Napoca",
                'county': "Cluj",
                'contact_phone': "0732987654",
                'owner_username': "maria_popescu"
            },
            {
                'title': "Adidași Nike Air Jordan 1 Retro High - Mărimea 43",
                'description': "Adidași originali Nike Air Jordan 1 Retro High, colorway clasic roșu/negru/alb. Mărimea 43. Cumpărați de pe site-ul oficial Nike, vin în cutia originală cu șireturi de rezervă. Purtați de 2 ori, nu prezintă urme de uzură sau cute (creases) pe piele.",
                'price': 650.00,
                'condition': "like_new",
                'category_name': "Încălțăminte",
                'negotiable': True,
                'city': "Timișoara",
                'county': "Timiș",
                'contact_phone': "0754111222",
                'owner_username': "elena_nistor"
            },
            {
                'title': "Ceas Smartwatch Garmin Fenix 7 Sapphire Solar",
                'description': "Ceas sport profesional Garmin Fenix 7 Sapphire Solar, ediție cu geam safir și încărcare solară. Diametru carcasă 47mm. Hărți integrate, GPS multi-band, autonomie impresionantă a bateriei. Prezintă mici urme fine pe bezelul metalic, ecranul din safir este absolut perfect.",
                'price': 2200.00,
                'condition': "good",
                'category_name': "Bijuterii & Ceasuri",
                'negotiable': True,
                'city': "Brașov",
                'county': "Brașov",
                'contact_phone': "0765999888",
                'owner_username': "andrei_gabor"
            },
            {
                'title': "Scaun Auto Copii Britax Romer Dualfix M i-Size",
                'description': "Scaun auto premium Britax Romer Dualfix M i-Size, cu rotație 360 grade pentru așezare ușoară a copilului. Potrivit pentru copii de la 61 la 105 cm (aprox. 3 luni la 4 ani). Fixare sigură prin sistem ISOFIX și picior de sprijin. Huse lavabile, nu a fost implicat în accidente.",
                'price': 1100.00,
                'condition': "good",
                'category_name': "Produse pentru Bebeluși",
                'negotiable': True,
                'city': "Timișoara",
                'county': "Timiș",
                'contact_phone': "0754111222",
                'owner_username': "elena_nistor"
            },
            {
                'title': "Sapiens. Scurtă istorie a omenirii - Yuval Noah Harari",
                'description': "Carte bestseller 'Sapiens. Scurtă istorie a omenirii' de Yuval Noah Harari, editura Polirom. Ediție broșată, stare perfectă, citită o singură dată cu mare grijă. Nu are pagini îndoite sau adnotări.",
                'price': 30.00,
                'condition': "good",
                'category_name': "Cărți Non-Fiction",
                'negotiable': False,
                'city': "Brașov",
                'county': "Brașov",
                'contact_phone': "0765999888",
                'owner_username': "andrei_gabor"
            },
            {
                'title': "Chitară Acustică Yamaha F310 + Husă cadou",
                'description': "Chitară acustică Yamaha F310, ideală pentru începători dar și avansați datorită sunetului cald și acțiunii joase a strunelor. Lemn de molid și meranti. Vine echipată cu corzi D'Addario proaspăt schimbate. Cadou husă de transport impermeabilă și 3 pene.",
                'price': 480.00,
                'condition': "good",
                'category_name': "Instrumente Muzicale",
                'negotiable': True,
                'city': "Brașov",
                'county': "Brașov",
                'contact_phone': "0765999888",
                'owner_username': "andrei_gabor"
            },
            {
                'title': "Hrană Uscată Câini Royal Canin Maxi Adult 15kg",
                'description': "Sac sigilat de 15kg hrană uscată Royal Canin Maxi Adult, special formulată pentru câini de talie mare (26 - 44 kg) cu vârsta peste 15 luni. Ajută la menținerea sănătății oaselor și articulațiilor. Termen de valabilitate până în 2027.",
                'price': 240.00,
                'condition': "new",
                'category_name': "Hrană Animale",
                'negotiable': False,
                'city': "Timișoara",
                'county': "Timiș",
                'contact_phone': "0754111222",
                'owner_username': "elena_nistor"
            },
            {
                'title': "Joc Monopoly Clasic în limba română",
                'description': "Ediția clasică a jocului de societate Monopoly, complet în limba română. Jocul conține tabla de joc, 8 pioni metalici, 28 titluri de proprietate, 16 carduri Șansă, 16 carduri Cufărul Comunității, pachet de bani Monopoly, 32 case, 12 hoteluri și 2 zaruri. Utilizat o singură dată.",
                'price': 60.00,
                'condition': "like_new",
                'category_name': "Diverse",
                'negotiable': True,
                'city': "Timișoara",
                'county': "Timiș",
                'contact_phone': "0754111222",
                'owner_username': "elena_nistor"
            }
        ]

        count_created = 0
        for item in listings_data:
            # Find the category
            try:
                category = Category.objects.get(name=item['category_name'])
            except Category.DoesNotExist:
                # Fall back to the main category if the subcategory does not exist
                self.stdout.write(self.style.WARNING(f"   ⚠️  Categoria {item['category_name']} nu există. Folosim fallback 'Altele'."))
                category, _ = Category.objects.get_or_create(name='Diverse', defaults={'slug': 'diverse'})

            owner = user_objects.get(item['owner_username'], User.objects.first())

            # Check whether the listing already exists to avoid duplicates on repeated runs
            if Listing.objects.filter(title=item['title'], owner=owner).exists():
                self.stdout.write(f"   ~ Anunțul '{item['title']}' există deja.")
                continue

            # Create the listing
            listing = Listing.objects.create(
                title=item['title'],
                description=item['description'],
                price=item['price'],
                condition=item['condition'],
                negotiable=item['negotiable'],
                category=category,
                owner=owner,
                city=item['city'],
                county=item['county'],
                contact_phone=item['contact_phone'],
                status='active',
                views_count=random.randint(10, 250),  # nosec B311
            )

            # Download a real image or fall back to a text placeholder
            try:
                keyword = get_image_keyword_for_listing(listing.title, category.name)
                self.stdout.write(f"   📥 Descărcăm imagine reală pentru '{listing.title}' (keyword: {keyword})...")
                img_data = download_real_image_bytes(keyword)
                filename = f"{slugify(listing.title)[:40]}_{listing.pk}.jpg"
                is_placeholder = False
            except Exception as dl_err:
                self.stdout.write(self.style.WARNING(f"   ⚠️ Nu s-a putut descărca imaginea ({dl_err}). Folosim fallback pe text placeholder."))
                subtitle = f"#{category.name}"
                img_data = make_img_bytes(listing.title[:48], subtitle)
                filename = f"{slugify(listing.title)[:40]}_{listing.pk}_placeholder.jpg"
                is_placeholder = True

            try:
                listing_img = ListingImage(listing=listing, alt_text=f"Imagine {listing.title}")
                listing_img.image.save(filename, ContentFile(img_data), save=True)
            except Exception as img_err:
                self.stdout.write(self.style.ERROR(f"   ❌ Eroare salvare imagine în baza de date / stocare: {img_err}"))

            msg_type = "imagine placeholder" if is_placeholder else "imagine reală"
            self.stdout.write(self.style.SUCCESS(f"   + Creat anunțul '{listing.title}' (ID: {listing.pk}) cu {msg_type}."))
            count_created += 1

        # Update statistics for all users at the end
        for user in User.objects.all():
            try:
                if hasattr(user, 'profile'):
                    user.profile.update_statistics()
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"⚠️  Eroare la actualizarea statisticilor pentru {user.username}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"\n🎉 POPULAREA A FOST FINALIZATĂ CU SUCCES! Am creat {count_created} anunțuri noi."))
