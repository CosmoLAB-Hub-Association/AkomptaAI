"""
Commande Django pour corriger les dates de transaction erronées.
Usage: python manage.py fix_dates

Corrige toutes les transactions dont le champ `date` (envoyé par le client)
est décalé de plus de 180 jours par rapport à `created_at` (serveur).
Cela arrive quand l'horloge de l'appareil client est incorrecte.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from api.models import Transaction


class Command(BaseCommand):
    help = "Corrige les dates de transaction client erronées (horloge appareil décalée)"

    def handle(self, *args, **options):
        fixed_count = 0
        now = timezone.now()

        transactions = Transaction.objects.all()

        for tx in transactions:
            try:
                created_at = tx.created_at
                tx_date = tx.date
                if not created_at or not tx_date:
                    continue

                delta_days = abs((tx_date - created_at).days)
                if delta_days > 180:
                    old_date = tx.date
                    tx.date = created_at
                    tx.save(update_fields=["date"])
                    fixed_count += 1
                    self.stdout.write(
                        f"  CORRIGÉ  Transaction #{tx.id} "
                        f"'({tx.name})': {old_date.strftime('%Y-%m-%d')} -> "
                        f"{created_at.strftime('%Y-%m-%d')}"
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"  ERREUR Transaction #{tx.id}: {e}")
                )

        self.stdout.write("")
        if fixed_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"{fixed_count} transaction(s) corrigée(s). "
                    "Les dates client ont été remplacées par les dates serveur (created_at)."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("Aucune transaction à corriger.")
            )
