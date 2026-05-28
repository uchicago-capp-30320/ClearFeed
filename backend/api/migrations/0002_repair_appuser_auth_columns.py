from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE app_user
                ADD COLUMN IF NOT EXISTS password varchar(128) NOT NULL DEFAULT '!unusable-password',
                ADD COLUMN IF NOT EXISTS last_login timestamp with time zone NULL,
                ADD COLUMN IF NOT EXISTS is_superuser boolean NOT NULL DEFAULT false,
                ADD COLUMN IF NOT EXISTS is_active boolean NOT NULL DEFAULT true,
                ADD COLUMN IF NOT EXISTS is_staff boolean NOT NULL DEFAULT false;
            """,
            reverse_sql="""
                ALTER TABLE app_user
                DROP COLUMN IF EXISTS password,
                DROP COLUMN IF EXISTS last_login,
                DROP COLUMN IF EXISTS is_superuser,
                DROP COLUMN IF EXISTS is_active,
                DROP COLUMN IF EXISTS is_staff;
            """,
        ),
    ]
