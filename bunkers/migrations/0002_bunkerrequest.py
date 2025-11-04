# Generated migration for BunkerRequest model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bunkers', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BunkerRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference_number', models.CharField(help_text='Proposed reference code for the bunker (e.g., B/SP-0246)', max_length=50, verbose_name='Reference Number')),
                ('name', models.CharField(help_text='Bunker name', max_length=200, verbose_name='Name')),
                ('description', models.TextField(blank=True, help_text='Description of the bunker', verbose_name='Description')),
                ('bunker_type', models.CharField(blank=True, help_text='Type of bunker (e.g., WW2 Battle Bunker)', max_length=200, verbose_name='Type')),
                ('latitude', models.DecimalField(decimal_places=6, help_text='GPS latitude coordinate', max_digits=9, verbose_name='Latitude')),
                ('longitude', models.DecimalField(decimal_places=6, help_text='GPS longitude coordinate', max_digits=9, verbose_name='Longitude')),
                ('locator', models.CharField(blank=True, help_text='Maidenhead locator (optional)', max_length=10, verbose_name='Locator')),
                ('photo_url', models.URLField(blank=True, help_text='Link to photo (optional)', verbose_name='Photo URL')),
                ('additional_info', models.TextField(blank=True, help_text='Any additional information', verbose_name='Additional Info')),
                ('status', models.CharField(choices=[('pending', 'Pending Review'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=20, verbose_name='Status')),
                ('rejection_reason', models.TextField(blank=True, verbose_name='Rejection Reason')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('requested_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bunker_requests', to=settings.AUTH_USER_MODEL, verbose_name='Requested By')),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_bunker_requests', to=settings.AUTH_USER_MODEL, verbose_name='Reviewed By')),
                ('bunker', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='creation_request', to='bunkers.bunker', verbose_name='Created Bunker')),
            ],
            options={
                'verbose_name': 'Bunker Request',
                'verbose_name_plural': 'Bunker Requests',
                'ordering': ['-created_at'],
            },
        ),
    ]
