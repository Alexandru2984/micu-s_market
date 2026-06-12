# Make slug field unique for SEO URLs

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('listings', '0002_advanced_features'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listing',
            name='slug',
            field=models.SlugField(blank=True, max_length=220, unique=True),
        ),
    ]
