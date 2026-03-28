# Generated migration for user profile and announcements

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0002_licensekey'),
    ]

    operations = [
        # Add external_reference to LicenseKey
        migrations.AddField(
            model_name='licensekey',
            name='external_reference',
            field=models.CharField(blank=True, help_text='Reference ID from MetaOptics platform', max_length=200, null=True),
        ),
        
        # Create UserProfile model (minimal version for migration chain)
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('avatar_url', models.URLField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        
        # Create Announcement model
        migrations.CreateModel(
            name='Announcement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('category', models.CharField(choices=[('general', 'General'), ('hail_prediction', 'Hail Prediction'), ('quantum_research', 'Quantum Research'), ('photonics', 'Photonics'), ('product', 'Product Update')], default='general', max_length=20)),
                ('link', models.URLField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_featured', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('published_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-published_at', '-created_at'],
            },
        ),
    ]
