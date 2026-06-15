#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append('/home/micu/Desktop/micu\'s_market/Micu_market')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Micu_market.settings')
django.setup()

from categories.models import Category
from django.utils.text import slugify
from django.db import transaction

def populate_categories(clear_existing=False):
    
    if clear_existing:
        print('🗑️  Ștergem categoriile existente...')
        Category.objects.all().delete()
        print('✅ Categoriile au fost șterse.')

    # Categoriile principale cu subcategoriile lor
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

    print('🚀 Începem popularea categoriilor...\n')

    with transaction.atomic():
        order = 0
        
        for category_name, category_data in categories_data.items():
            # Create the main category
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
            
            if created:
                print(f'✅ Categoria "{category_name}" a fost creată')
            else:
                print(f'⚠️  Categoria "{category_name}" există deja')
            
            # Create the subcategories
            sub_order = 0
            for sub_name in category_data['subcategories']:
                sub_category, sub_created = Category.objects.get_or_create(
                    name=sub_name,
                    defaults={
                        'slug': slugify(sub_name),
                        'parent': main_category,
                        'order': sub_order,
                        'is_active': True,
                    }
                )
                
                if sub_created:
                    print(f'   ✅ Subcategoria "{sub_name}" a fost creată')
                else:
                    print(f'   ⚠️  Subcategoria "{sub_name}" există deja')
                
                sub_order += 1
            
            print()  # Linie goală pentru separare
            order += 1

    # Statistici finale
    total_categories = Category.objects.filter(parent=None).count()
    total_subcategories = Category.objects.filter(parent__isnull=False).count()
    
    print('='*60)
    print('🎉 POPULAREA CATEGORIILOR A FOST FINALIZATĂ!')
    print(f'📊 Total categorii principale: {total_categories}')
    print(f'📊 Total subcategorii: {total_subcategories}')
    print(f'📊 Total general: {total_categories + total_subcategories}')
    print('='*60)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Populează categoriile pentru Micu\'s Market')
    parser.add_argument('--clear', action='store_true', help='Șterge categoriile existente')
    
    args = parser.parse_args()
    
    try:
        populate_categories(clear_existing=args.clear)
    except Exception as e:
        print(f'❌ Eroare: {e}')
        sys.exit(1)
