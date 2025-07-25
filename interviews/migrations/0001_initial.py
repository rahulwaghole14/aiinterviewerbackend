# Generated by Django 5.1.6 on 2025-07-22 09:39

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('candidates', '__first__'),
        ('jobs', '0003_remove_job_current_team_size_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Interview',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('scheduled', 'Scheduled'), ('completed', 'Completed'), ('error', 'Error')], default='scheduled', max_length=20)),
                ('interview_round', models.CharField(blank=True, max_length=100)),
                ('feedback', models.TextField(blank=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('video_url', models.URLField(blank=True, max_length=500)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('candidate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='interviews', to='candidates.candidate')),
                ('job', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='interviews', to='jobs.job')),
            ],
        ),
    ]
