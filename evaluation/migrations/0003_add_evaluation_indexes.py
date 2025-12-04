# Generated migration for database optimization
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluation', '0002_evaluation_details'),
    ]

    operations = [
        # Add db_index to existing fields
        migrations.AlterField(
            model_name='evaluation',
            name='interview',
            field=models.OneToOneField(
                on_delete=models.CASCADE,
                related_name='evaluation',
                to='interviews.interview',
                db_index=True
            ),
        ),
        migrations.AlterField(
            model_name='evaluation',
            name='overall_score',
            field=models.FloatField(db_index=True),
        ),
        migrations.AlterField(
            model_name='evaluation',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        # Add composite indexes
        migrations.AddIndex(
            model_name='evaluation',
            index=models.Index(fields=['interview', 'created_at'], name='evaluation_interview_created_idx'),
        ),
        migrations.AddIndex(
            model_name='evaluation',
            index=models.Index(fields=['overall_score', 'created_at'], name='evaluation_score_created_idx'),
        ),
    ]







