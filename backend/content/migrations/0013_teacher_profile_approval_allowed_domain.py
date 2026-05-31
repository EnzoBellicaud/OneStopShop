import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0012_offer_link_check_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="profile",
            field=models.CharField(
                choices=[
                    ("Student", "Student"),
                    ("Academic staff", "Academic staff"),
                    ("Teacher", "Teacher"),
                    ("Company", "Company"),
                    ("Admin", "Admin"),
                ],
                default="Student",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="approval_status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("approved", "Approved"),
                    ("rejected", "Rejected"),
                ],
                default="approved",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="email_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="user",
            name="approved_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="approved_users",
                to="content.user",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="approval_notes",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.CreateModel(
            name="AllowedDomain",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("domain", models.CharField(max_length=255, unique=True)),
                ("description", models.CharField(blank=True, max_length=255)),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="allowed_domains",
                        to="content.organization",
                    ),
                ),
            ],
            options={
                "db_table": "allowed_domain",
                "ordering": ["domain"],
            },
        ),
    ]
