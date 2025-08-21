# Generated manually to fix interview_link field length

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('interviews', '0002_interviewconflict_interviewslot_interviewschedule_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interview',
            name='interview_link',
            field=models.CharField(blank=True, help_text='Secure link for candidate to join interview', max_length=255),
        ),
    ]


