from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0004_llmanalysisrun"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="llmanalysisrun",
            name="prompt_version",
        ),
    ]
