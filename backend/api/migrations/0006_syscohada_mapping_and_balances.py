from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0005_user_initial_balance"),
    ]

    operations = [
        migrations.CreateModel(
            name="SyscohadaCRMappingRule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ref", models.CharField(max_length=4)),
                ("tx_type", models.CharField(blank=True, choices=[("income", "Revenu"), ("expense", "Dépense")], max_length=10, null=True)),
                ("category_pattern", models.CharField(blank=True, default="", max_length=255)),
                ("name_pattern", models.CharField(blank=True, default="", max_length=255)),
                ("match_mode", models.CharField(choices=[("contains", "Contient"), ("regex", "Regex")], default="contains", max_length=20)),
                ("priority", models.PositiveIntegerField(default=100)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="syscohada_cr_rules", to="api.user")),
            ],
            options={
                "verbose_name": "Règle SYSCOHADA (CR)",
                "verbose_name_plural": "Règles SYSCOHADA (CR)",
                "ordering": ["priority", "-updated_at", "-id"],
            },
        ),
        migrations.CreateModel(
            name="SyscohadaBilanBalance",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("year", models.PositiveIntegerField()),
                ("section", models.CharField(choices=[("ACTIF", "Actif"), ("PASSIF", "Passif")], max_length=10)),
                ("ref", models.CharField(max_length=4)),
                ("brut", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ("amort", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ("net", models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ("note", models.CharField(blank=True, default="", max_length=50)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="syscohada_bilan_balances", to="api.user")),
            ],
            options={
                "verbose_name": "Solde SYSCOHADA (Bilan)",
                "verbose_name_plural": "Soldes SYSCOHADA (Bilan)",
                "ordering": ["year", "section", "ref"],
                "unique_together": {("user", "year", "section", "ref")},
            },
        ),
        migrations.AddIndex(
            model_name="syscohadacrmappingrule",
            index=models.Index(fields=["user", "is_active", "priority"], name="api_syscoh_user_id_ea86a0_idx"),
        ),
        migrations.AddIndex(
            model_name="syscohadacrmappingrule",
            index=models.Index(fields=["user", "tx_type"], name="api_syscoh_user_id_83c3af_idx"),
        ),
        migrations.AddIndex(
            model_name="syscohadacrmappingrule",
            index=models.Index(fields=["user", "ref"], name="api_syscoh_user_id_03664d_idx"),
        ),
        migrations.AddIndex(
            model_name="syscohadabilanbalance",
            index=models.Index(fields=["user", "year", "section"], name="api_syscoh_user_id_8bc49d_idx"),
        ),
        migrations.AddIndex(
            model_name="syscohadabilanbalance",
            index=models.Index(fields=["user", "year", "ref"], name="api_syscoh_user_id_824e07_idx"),
        ),
    ]

