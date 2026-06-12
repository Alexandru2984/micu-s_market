# Add advanced listing features
from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0001_initial'),
        ('listings', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Update model settings
        migrations.AlterModelOptions(
            name='listing',
            options={'ordering': ['-created_at'], 'verbose_name': 'Anunț', 'verbose_name_plural': 'Anunțuri'},
        ),
        
        # Remove old fields
        migrations.RemoveField(model_name='listing', name='image'),
        migrations.RemoveField(model_name='listing', name='is_active'),
        
        # Add location
        migrations.AddField(
            model_name='listing',
            name='city',
            field=models.CharField(default='București', max_length=100, verbose_name='Oraș'),
        ),
        migrations.AddField(
            model_name='listing',
            name='county',
            field=models.CharField(default='București', max_length=100, verbose_name='Județ'),
        ),
        
        # Add item details
        migrations.AddField(
            model_name='listing',
            name='condition',
            field=models.CharField(choices=[('new', 'Nou'), ('like_new', 'Ca nou'), ('good', 'Bună stare'), ('fair', 'Stare acceptabilă'), ('poor', 'Stare proastă')], default='good', max_length=20, verbose_name='Stare'),
        ),
        migrations.AddField(
            model_name='listing',
            name='negotiable',
            field=models.BooleanField(default=True, verbose_name='Negociabil'),
        ),
        
        # Add management features
        migrations.AddField(
            model_name='listing',
            name='slug',
            field=models.SlugField(blank=True, max_length=220),
        ),
        migrations.AddField(
            model_name='listing',
            name='status',
            field=models.CharField(choices=[('active', 'Activ'), ('sold', 'Vândut'), ('reserved', 'Rezervat'), ('inactive', 'Inactiv')], default='active', max_length=20, verbose_name='Status'),
        ),
        migrations.AddField(
            model_name='listing',
            name='is_featured',
            field=models.BooleanField(default=False, verbose_name='Promovat'),
        ),
        migrations.AddField(
            model_name='listing',
            name='views_count',
            field=models.IntegerField(default=0, verbose_name='Număr vizualizări'),
        ),
        migrations.AddField(
            model_name='listing',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Actualizat la'),
        ),
        migrations.AddField(
            model_name='listing',
            name='expires_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Expiră la'),
        ),
        
        # Add category support
        migrations.AddField(
            model_name='listing',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='listings', to='categories.category', verbose_name='Categorie'),
        ),
        
        # Update existing fields
        migrations.AlterField(
            model_name='listing',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Creat la'),
        ),
        migrations.AlterField(
            model_name='listing',
            name='description',
            field=models.TextField(verbose_name='Descriere'),
        ),
        migrations.AlterField(
            model_name='listing',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='listings', to=settings.AUTH_USER_MODEL, verbose_name='Proprietar'),
        ),
        migrations.AlterField(
            model_name='listing',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Preț'),
        ),
        migrations.AlterField(
            model_name='listing',
            name='title',
            field=models.CharField(max_length=200, verbose_name='Titlu'),
        ),
        
        # Create image gallery
        migrations.CreateModel(
            name='ListingImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='listings/', verbose_name='Imagine')),
                ('alt_text', models.CharField(blank=True, max_length=200, verbose_name='Text alternativ')),
                ('order', models.IntegerField(default=0, verbose_name='Ordine')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('listing', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='listings.listing', verbose_name='Anunț')),
            ],
            options={
                'verbose_name': 'Imagine anunț',
                'verbose_name_plural': 'Imagini anunțuri',
                'ordering': ['order'],
            },
        ),
    ]
