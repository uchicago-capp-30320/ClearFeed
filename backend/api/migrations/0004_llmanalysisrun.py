import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0003_repair_appuser_email_column"),
    ]

    operations = [
        migrations.CreateModel(
            name="LLMAnalysisRun",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "status",
                    models.TextField(
                        choices=[
                            ("queued", "Queued"),
                            ("processing", "Processing"),
                            ("complete", "Complete"),
                            ("failed", "Failed"),
                        ],
                        default="queued",
                    ),
                ),
                ("sample_size", models.IntegerField()),
                ("sample_seed", models.BigIntegerField(null=True)),
                ("model_name", models.TextField()),
                ("prompt_version", models.TextField()),
                ("sample_metadata", models.JSONField(null=True)),
                ("result", models.JSONField(null=True)),
                ("raw_output", models.TextField(null=True)),
                ("error_message", models.TextField(null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="api.appuser",
                    ),
                ),
            ],
            options={
                "db_table": "llm_analysis_run",
                "indexes": [
                    models.Index(fields=["user"], name="llm_run_user_idx"),
                    models.Index(fields=["status"], name="llm_run_status_idx"),
                    models.Index(fields=["created_at"], name="llm_run_created_idx"),
                ],
            },
        ),
    ]
