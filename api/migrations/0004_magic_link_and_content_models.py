# Generated migration for Magic Link auth and content models

import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0003_userprofile_announcement'),
    ]

    operations = [
        # =====================================================================
        # Update UserProfile with new research-focused fields
        # =====================================================================
        migrations.AddField(
            model_name='userprofile',
            name='bio',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='institution',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='department',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='research_interests',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='website',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='google_scholar',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='orcid',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='twitter',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='linkedin',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='is_contributor',
            field=models.BooleanField(default=False),
        ),
        
        # =====================================================================
        # Create MagicLink model
        # =====================================================================
        migrations.CreateModel(
            name='MagicLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254)),
                ('token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('is_used', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        
        # =====================================================================
        # Create ResearchPaper model
        # =====================================================================
        migrations.CreateModel(
            name='ResearchPaper',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=300)),
                ('slug', models.SlugField(blank=True, max_length=350, unique=True)),
                ('subtitle', models.CharField(blank=True, max_length=500, null=True)),
                ('abstract', models.TextField()),
                ('content', models.TextField(help_text='Markdown content')),
                ('category', models.CharField(choices=[('fundamentals', 'Fundamentals'), ('tutorial', 'Tutorial'), ('research', 'Research'), ('news', 'News'), ('review', 'Review')], default='research', max_length=20)),
                ('tags', models.JSONField(blank=True, default=list)),
                ('featured_image', models.URLField(blank=True, null=True)),
                ('pdf_url', models.URLField(blank=True, null=True)),
                ('github_url', models.URLField(blank=True, null=True)),
                ('doi', models.CharField(blank=True, max_length=100, null=True)),
                ('original_paper_title', models.CharField(blank=True, max_length=500, null=True)),
                ('original_paper_authors', models.TextField(blank=True, null=True)),
                ('original_paper_journal', models.CharField(blank=True, max_length=300, null=True)),
                ('original_paper_year', models.IntegerField(blank=True, null=True)),
                ('original_paper_doi', models.CharField(blank=True, max_length=100, null=True)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('review', 'Under Review'), ('published', 'Published')], default='draft', max_length=20)),
                ('is_featured', models.BooleanField(default=False)),
                ('views', models.PositiveIntegerField(default=0)),
                ('reading_time', models.PositiveIntegerField(default=5, help_text='Estimated reading time in minutes')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='papers', to=settings.AUTH_USER_MODEL)),
                ('co_authors', models.ManyToManyField(blank=True, related_name='co_authored_papers', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-published_at', '-created_at'],
            },
        ),
        
        # =====================================================================
        # Create Comment model
        # =====================================================================
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('is_approved', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to=settings.AUTH_USER_MODEL)),
                ('paper', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='api.researchpaper')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='api.comment')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        
        # =====================================================================
        # Create Like model
        # =====================================================================
        migrations.CreateModel(
            name='Like',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('paper', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='api.researchpaper')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('paper', 'user')},
            },
        ),
        
        # =====================================================================
        # Create NewsletterSubscriber model
        # =====================================================================
        migrations.CreateModel(
            name='NewsletterSubscriber',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('name', models.CharField(blank=True, max_length=200, null=True)),
                ('interests', models.JSONField(blank=True, default=list)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        
        # =====================================================================
        # Create Tool model
        # =====================================================================
        migrations.CreateModel(
            name='Tool',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(blank=True, max_length=250, unique=True)),
                ('short_description', models.CharField(max_length=300)),
                ('description', models.TextField()),
                ('github_url', models.URLField()),
                ('demo_url', models.URLField(blank=True, null=True)),
                ('documentation_url', models.URLField(blank=True, null=True)),
                ('tags', models.JSONField(blank=True, default=list)),
                ('stars', models.PositiveIntegerField(default=0)),
                ('is_featured', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tools', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-is_featured', '-stars', '-created_at'],
            },
        ),
    ]
