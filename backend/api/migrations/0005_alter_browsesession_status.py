from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0004_llmanalysisrun"),
    ]

    operations = [
        migrations.AlterField(
            model_name="browsesession",
            name="status",
            field=models.TextField(
                choices=[
                    ("queued", "Queued"),
                    ("analyzing", "Analyzing"),
                    ("complete", "Complete"),
                    ("failed", "Failed"),
                ],
                default="queued",
            ),
        ),
    ]
