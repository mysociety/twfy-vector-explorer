
from django.db import migrations, models
import pgvector.django.vector
from pgvector.django import VectorExtension


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        VectorExtension(),
        migrations.CreateModel(
            name='ParagraphVector',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('speech_id', models.CharField()),
                ('paragraph_id', models.CharField()),
                ('text', models.TextField()),
                ('embedding', pgvector.django.vector.VectorField(dimensions=384)),
            ],
        ),
    ]