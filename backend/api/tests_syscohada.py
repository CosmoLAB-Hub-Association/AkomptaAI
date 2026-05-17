from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from .models import (
    Transaction,
    User,
    SyscohadaCRMappingRule,
    SyscohadaBilanBalance,
)
from .syscohada_reports import compute_compte_resultat, generate_bilan_csv, generate_compte_resultat_csv
from .serializers import TransactionSerializer


class SyscohadaComputationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="syscohada@test.com",
            password="pass12345",
            first_name="Sys",
            last_name="Coha",
            account_type="personal",
            initial_balance=Decimal("1000.00"),
            agreed_terms=True,
        )

    def _dt(self, year: int, month: int, day: int):
        return timezone.make_aware(datetime(year, month, day, 12, 0, 0))

    def test_compte_resultat_marks_unmapped_transactions(self):
        # Year N
        tx_income = Transaction.objects.create(
            user=self.user,
            name="Vente marchandises",
            amount=Decimal("5000.00"),
            type="income",
            category="Ventes",
            date=self._dt(2026, 2, 2),
            currency="XOF",
        )
        tx_transport = Transaction.objects.create(
            user=self.user,
            name="Taxi",
            amount=Decimal("200.00"),
            type="expense",
            category="Transport",
            date=self._dt(2026, 2, 3),
            currency="XOF",
        )
        tx_unknown = Transaction.objects.create(
            user=self.user,
            name="Dépense inconnue",
            amount=Decimal("50.00"),
            type="expense",
            category="Inconnu",
            date=self._dt(2026, 2, 4),
            currency="XOF",
        )

        compte = compute_compte_resultat(self.user, 2026)

        # TA should include the income (default mapping sees "ventes")
        self.assertGreaterEqual(compte.values_n.get("TA", Decimal("0")), Decimal("5000.00"))

        # RG should include transport
        self.assertGreaterEqual(compte.values_n.get("RG", Decimal("0")), Decimal("200.00"))

        # Unknown should be marked as unmapped (and goes to RJ fallback)
        self.assertIn(tx_unknown.id, compte.unmapped_tx_ids_n)
        self.assertGreaterEqual(compte.values_n.get("RJ", Decimal("0")), Decimal("50.00"))

        # If we add an explicit rule, it should stop being "unmapped"
        SyscohadaCRMappingRule.objects.create(
            user=self.user,
            ref="RH",
            tx_type="expense",
            category_pattern="Inconnu",
            match_mode="contains",
            priority=1,
            is_active=True,
        )
        compte2 = compute_compte_resultat(self.user, 2026)
        self.assertNotIn(tx_unknown.id, compte2.unmapped_tx_ids_n)
        self.assertGreaterEqual(compte2.values_n.get("RH", Decimal("0")), Decimal("50.00"))

    def test_bilan_can_balance_with_user_inputs(self):
        # Create a simple year with net profit
        Transaction.objects.create(
            user=self.user,
            name="Vente",
            amount=Decimal("1000.00"),
            type="income",
            category="Ventes",
            date=self._dt(2026, 1, 10),
            currency="XOF",
        )
        Transaction.objects.create(
            user=self.user,
            name="Transport",
            amount=Decimal("100.00"),
            type="expense",
            category="Transport",
            date=self._dt(2026, 1, 11),
            currency="XOF",
        )

        compte = compute_compte_resultat(self.user, 2026)
        cash = self.user.initial_balance + compte.total_income_n - compte.total_expense_n
        resultat = compte.resultat_net_n

        # Provide capital so that: CA + CJ == BS (minimal bilan)
        SyscohadaBilanBalance.objects.create(
            user=self.user,
            year=2026,
            section="PASSIF",
            ref="CA",
            net=(cash - resultat),
            note="Capital (test)",
        )

        bilan_csv = generate_bilan_csv(self.user, compte).decode("utf-8")
        # Sanity: contains key refs
        self.assertIn("ACTIF,BS", bilan_csv)
        self.assertIn("PASSIF,CA", bilan_csv)
        self.assertIn("PASSIF,CJ", bilan_csv)

    def test_exports_generate_csv_bytes(self):
        Transaction.objects.create(
            user=self.user,
            name="Vente",
            amount=Decimal("100.00"),
            type="income",
            category="Ventes",
            date=self._dt(2026, 3, 1),
            currency="XOF",
        )
        compte = compute_compte_resultat(self.user, 2026)
        cr_csv = generate_compte_resultat_csv(compte)
        bilan_csv = generate_bilan_csv(self.user, compte)
        self.assertIsInstance(cr_csv, (bytes, bytearray))
        self.assertIsInstance(bilan_csv, (bytes, bytearray))
        self.assertGreater(len(cr_csv), 50)
        self.assertGreater(len(bilan_csv), 50)

    def test_uses_created_at_when_transaction_date_is_way_off(self):
        """
        If client sends a wrong `date` (ex: device clock in 2024) but the server-side
        `created_at` is in 2026, SYSCOHADA calculations should include it in 2026.
        """
        tx = Transaction.objects.create(
            user=self.user,
            name="Vente (bad date)",
            amount=Decimal("100.00"),
            type="income",
            category="Ventes",
            date=self._dt(2024, 3, 16),  # wrong
            currency="XOF",
        )
        # Force created_at to 2026 (simulate real server record time)
        Transaction.objects.filter(id=tx.id).update(created_at=self._dt(2026, 5, 17))

        compte = compute_compte_resultat(self.user, 2026)
        self.assertGreaterEqual(compte.values_n.get("TA", Decimal("0")), Decimal("100.00"))

    def test_transaction_serializer_clamps_bad_client_dates(self):
        # Date far away (client clock wrong) should be clamped to "now" by default.
        payload = {
            "name": "Bad date tx",
            "amount": "100.00",
            "type": "income",
            "category": "Ventes",
            "currency": "XOF",
            "date": self._dt(2024, 3, 16).isoformat().replace("+00:00", "Z"),
        }

        class _Req:
            query_params = {}
            user = self.user

        serializer = TransactionSerializer(data=payload, context={"request": _Req()})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        value = serializer.validated_data["date"]
        now = timezone.now()
        self.assertLessEqual(abs((value - now).days), 1)
