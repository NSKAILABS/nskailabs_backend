# Generated migration for auth overhaul

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0002_subscription_payment_licensekey'),
    ]

    operations = [
        # Remove old payment models
        migrations.RemoveField(
            model_name='payment',
            name='subscription',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='user',
        ),
        migrations.RemoveField(
            model_name='licensekey',
            name='subscription',
        ),
        migrations.DeleteModel(
            name='Payment',
        ),
        migrations.DeleteModel(
            name='Subscription',
        ),
        
        # Add external_reference to LicenseKey
        migrations.AddField(
            model_name='licensekey',
            name='external_reference',
            field=models.CharField(blank=True, help_text='Reference ID from MetaOptics platform', max_length=200, null=True),
        ),
        
        # Create UserProfile model
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('google_id', models.CharField(blank=True, max_length=100, null=True, unique=True)),
                ('phone_number', models.CharField(blank=True, max_length=15, null=True)),
                ('is_phone_verified', models.BooleanField(default=False)),
                ('is_google_user', models.BooleanField(default=False)),
                ('avatar_url', models.URLField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        
        # Create OTPVerification model
        migrations.CreateModel(
            name='OTPVerification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('phone', models.CharField(blank=True, max_length=15, null=True)),
                ('otp_code', models.CharField(max_length=6)),
                ('otp_type', models.CharField(choices=[('registration', 'Registration'), ('login', 'Login'), ('password_reset', 'Password Reset')], default='registration', max_length=20)),
                ('is_verified', models.BooleanField(default=False)),
                ('attempts', models.IntegerField(default=0)),
                ('max_attempts', models.IntegerField(default=3)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='otp_codes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
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