from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from api.models import User
from api.syscohada_reports import (
    compute_compte_resultat,
    generate_bilan_csv,
    generate_compte_resultat_csv,
)


def _to_decimal(value: str | None) -> Decimal:
    s = (value or "").strip()
    if s == "":
        return Decimal("0")
    # CSV exports are produced with Decimal -> str, so '.' is expected.
    try:
        return Decimal(s)
    except InvalidOperation:
        # tolerate commas in pasted files
        return Decimal(s.replace(",", "."))


@dataclass(frozen=True)
class DiffItem:
    ref: str
    field: str
    expected: Decimal
    actual: Decimal


class Command(BaseCommand):
    help = "Audit SYSCOHADA exports vs DB calculations (CR + Bilan) for one user and year."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True, help="User email to audit (ex: gini@gmail.com)")
        parser.add_argument("--year", type=int, default=timezone.now().year, help="Exercise year (default: current year)")
        parser.add_argument("--cr-csv", default="", help="Path to compte_resultat_syscohada_<year>.csv to compare")
        parser.add_argument("--bilan-csv", default="", help="Path to bilan_syscohada_<year>.csv to compare")
        parser.add_argument(
            "--out-md",
            default="",
            help="Optional output markdown path. Default: backend/Documentation/syscohada_audit_<year>_<email>.md",
        )

    def handle(self, *args, **options):
        email: str = options["email"]
        year: int = options["year"]
        cr_csv_path = (options["cr_csv"] or "").strip()
        bilan_csv_path = (options["bilan_csv"] or "").strip()
        out_md_path = (options["out_md"] or "").strip()

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist as e:
            raise CommandError(f"User not found: {email}") from e

        compte = compute_compte_resultat(user, year)

        expected_cr_bytes = generate_compte_resultat_csv(compte)
        expected_bilan_bytes = generate_bilan_csv(user, compte)

        expected_cr = self._parse_cr_bytes(expected_cr_bytes)
        expected_bilan = self._parse_bilan_bytes(expected_bilan_bytes)

        diffs: list[DiffItem] = []

        actual_cr = None
        if cr_csv_path:
            actual_cr = self._parse_cr_file(Path(cr_csv_path))
            diffs.extend(self._diff_maps(expected_cr, actual_cr, fields=["MONTANT_N", "MONTANT_N_1"]))

        actual_bilan = None
        if bilan_csv_path:
            actual_bilan = self._parse_bilan_file(Path(bilan_csv_path))
            diffs.extend(
                self._diff_bilan(expected_bilan, actual_bilan)
            )

        if not out_md_path:
            safe_email = email.replace("@", "_at_").replace(".", "_")
            out_md_path = str(Path("backend/Documentation") / f"syscohada_audit_{year}_{safe_email}.md")

        out_path = Path(out_md_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            self._render_md(
                email=email,
                year=year,
                user_id=user.id,
                initial_balance=user.initial_balance,
                compte=compte,
                cr_csv_path=cr_csv_path,
                bilan_csv_path=bilan_csv_path,
                diffs=diffs,
                compared_cr=bool(actual_cr),
                compared_bilan=bool(actual_bilan),
            ),
            encoding="utf-8",
        )

        if diffs:
            self.stdout.write(self.style.ERROR(f"Mismatch: {len(diffs)} difference(s). Report: {out_path}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"OK: exports match calculations. Report: {out_path}"))

    def _parse_cr_bytes(self, data: bytes) -> dict[str, dict[str, Decimal]]:
        text = data.decode("utf-8")
        return self._parse_cr_rows(csv.DictReader(text.splitlines()))

    def _parse_cr_file(self, path: Path) -> dict[str, dict[str, Decimal]]:
        if not path.exists():
            raise CommandError(f"File not found: {path}")
        with path.open("r", encoding="utf-8", newline="") as f:
            return self._parse_cr_rows(csv.DictReader(f))

    def _parse_cr_rows(self, reader: csv.DictReader) -> dict[str, dict[str, Decimal]]:
        out: dict[str, dict[str, Decimal]] = {}
        for row in reader:
            ref = (row.get("REF") or "").strip()
            if not ref:
                continue
            out[ref] = {
                "MONTANT_N": _to_decimal(row.get("MONTANT_N")),
                "MONTANT_N_1": _to_decimal(row.get("MONTANT_N_1")),
            }
        return out

    def _parse_bilan_bytes(self, data: bytes) -> dict[tuple[str, str], dict[str, Decimal]]:
        text = data.decode("utf-8")
        return self._parse_bilan_rows(csv.DictReader(text.splitlines()))

    def _parse_bilan_file(self, path: Path) -> dict[tuple[str, str], dict[str, Decimal]]:
        if not path.exists():
            raise CommandError(f"File not found: {path}")
        with path.open("r", encoding="utf-8", newline="") as f:
            return self._parse_bilan_rows(csv.DictReader(f))

    def _parse_bilan_rows(self, reader: csv.DictReader) -> dict[tuple[str, str], dict[str, Decimal]]:
        out: dict[tuple[str, str], dict[str, Decimal]] = {}
        for row in reader:
            section = (row.get("SECTION") or "").strip().upper()
            ref = (row.get("REF") or "").strip()
            if not section or not ref:
                continue
            out[(section, ref)] = {
                "BRUT": _to_decimal(row.get("BRUT")),
                "AMORT/DEPREC": _to_decimal(row.get("AMORT/DEPREC")),
                "NET_N": _to_decimal(row.get("NET_N")),
                "NET_N_1": _to_decimal(row.get("NET_N_1")),
            }
        return out

    def _diff_maps(
        self,
        expected: dict[str, dict[str, Decimal]],
        actual: dict[str, dict[str, Decimal]],
        *,
        fields: list[str],
    ) -> list[DiffItem]:
        diffs: list[DiffItem] = []
        all_refs = sorted(set(expected.keys()) | set(actual.keys()))
        for ref in all_refs:
            e = expected.get(ref, {})
            a = actual.get(ref, {})
            for field in fields:
                ev = e.get(field, Decimal("0"))
                av = a.get(field, Decimal("0"))
                if ev != av:
                    diffs.append(DiffItem(ref=ref, field=field, expected=ev, actual=av))
        return diffs

    def _diff_bilan(
        self,
        expected: dict[tuple[str, str], dict[str, Decimal]],
        actual: dict[tuple[str, str], dict[str, Decimal]],
    ) -> list[DiffItem]:
        diffs: list[DiffItem] = []
        keys = sorted(set(expected.keys()) | set(actual.keys()))
        for key in keys:
            e = expected.get(key, {})
            a = actual.get(key, {})
            section, ref = key
            for field in ["BRUT", "AMORT/DEPREC", "NET_N", "NET_N_1"]:
                ev = e.get(field, Decimal("0"))
                av = a.get(field, Decimal("0"))
                if ev != av:
                    diffs.append(DiffItem(ref=f"{section}:{ref}", field=field, expected=ev, actual=av))
        return diffs

    def _render_md(
        self,
        *,
        email: str,
        year: int,
        user_id: int,
        initial_balance: Decimal,
        compte,
        cr_csv_path: str,
        bilan_csv_path: str,
        diffs: list[DiffItem],
        compared_cr: bool,
        compared_bilan: bool,
    ) -> str:
        lines: list[str] = []
        lines.append(f"# SYSCOHADA Audit — {email} — {year}")
        lines.append("")
        lines.append("## Contexte")
        lines.append(f"- User id: `{user_id}`")
        lines.append(f"- Solde initial (`initial_balance`): `{initial_balance}`")
        lines.append(f"- Transactions non mappées N: `{len(compte.unmapped_tx_ids_n)}`")
        lines.append(f"- Transactions non mappées N-1: `{len(compte.unmapped_tx_ids_n_1)}`")
        lines.append("")
        lines.append("## Sources comparées")
        lines.append(f"- CR CSV fourni: `{cr_csv_path or '—'}`")
        lines.append(f"- Bilan CSV fourni: `{bilan_csv_path or '—'}`")
        lines.append("")
        lines.append("## Résultat")
        if not compared_cr and not compared_bilan:
            lines.append("- Aucun fichier fourni pour comparaison. Le rapport décrit uniquement les calculs attendus.")
        elif diffs:
            lines.append(f"- Statut: **Mismatch** ({len(diffs)} différence(s))")
        else:
            lines.append("- Statut: **Match** (les exports correspondent aux calculs DB)")
        lines.append("")

        lines.append("## Calculs (DB)")
        lines.append(f"- Total revenus N: `{compte.total_income_n}`")
        lines.append(f"- Total dépenses N: `{compte.total_expense_n}`")
        lines.append(f"- Résultat net N (XI): `{compte.resultat_net_n}`")
        lines.append("")

        if diffs:
            lines.append("## Détails des différences")
            lines.append("")
            lines.append("| Ref | Champ | Attendu | Généré |")
            lines.append("|---|---:|---:|---:|")
            for d in diffs[:300]:
                lines.append(f"| `{d.ref}` | `{d.field}` | `{d.expected}` | `{d.actual}` |")
            if len(diffs) > 300:
                lines.append("")
                lines.append(f"_Diffs tronquées: {len(diffs) - 300} lignes supplémentaires._")
            lines.append("")

        lines.append("## Notes")
        lines.append("- Les montants attendus sont calculés via `compute_compte_resultat()` + `generate_bilan_csv()`.")
        lines.append("- Si les exports fournis sont à zéro, vérifier: année des transactions, `initial_balance`, et règles de mapping CR.")
        lines.append("")
        return "\n".join(lines)

