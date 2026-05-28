from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0002_repair_appuser_auth_columns"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE app_user
                ADD COLUMN IF NOT EXISTS email varchar(254) NULL;
                CREATE UNIQUE INDEX IF NOT EXISTS app_user_email_unique
                ON app_user (email)
                WHERE email IS NOT NULL;
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS app_user_email_unique;
                ALTER TABLE app_user DROP COLUMN IF EXISTS email;
            """,
        ),
    ]
