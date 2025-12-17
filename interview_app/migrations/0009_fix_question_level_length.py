# Generated manually to fix question_level field length

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('interview_app', '0008_add_database_storage_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interviewquestion',
            name='question_level',
            field=models.CharField(default='MAIN', max_length=30),
        ),
    ]

