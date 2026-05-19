from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from django.utils import timezone

from .models import Transaction, User


TEMPLATES_DIR = Path(__file__).resolve().parent / "syscohada_templates"


def _load_template_json(filename: str) -> Any:
    with (TEMPLATES_DIR / filename).open("r", encoding="utf-8") as f:
        return json.load(f)


def _year_bounds(year: int) -> tuple[datetime, datetime]:
    start = timezone.make_aware(datetime(year, 1, 1, 0, 0, 0))
    end = timezone.make_aware(datetime(year + 1, 1, 1, 0, 0, 0))
    return start, end


def _normalize_text(value: str | None) -> str:
    return (value or "").strip().lower()


def _map_transaction_to_cr_ref(tx: Transaction) -> str:
    """
    MVP mapping: map Akompta Transaction -> SYSCOHADA Compte de Résultat ref.
    This is intentionally heuristic and can be replaced later by a user-configurable mapping table.
    """
    category = _normalize_text(getattr(tx, "category", ""))
    name = _normalize_text(getattr(tx, "name", ""))
    haystack = f"{category} {name}".strip()

    if tx.type == "income":
        if any(k in haystack for k in ["service", "prestation", "consult"]):
            return "TC"  # travaux, services vendus
        if any(k in haystack for k in ["produit accessoire", "accessoire"]):
            return "TD"
        return "TA"  # ventes de marchandises

    # expense
    if any(k in haystack for k in ["achat", "marchandise", "appro", "approvisionnement"]):
        return "RA"
    if any(k in haystack for k in ["transport", "taxi", "bus", "essence", "carburant", "livraison"]):
        return "RG"
    if any(k in haystack for k in ["loyer", "internet", "eau", "electric", "électric", "telephone", "téléphone", "prestataire", "maintenance", "marketing", "publicit", "pub"]):
        return "RH"
    if any(k in haystack for k in ["impot", "impôt", "taxe", "douane", "etat", "état"]):
        return "RI"
    if any(k in haystack for k in ["salaire", "salaires", "personnel", "paie", "payroll"]):
        return "RK"
    return "RJ"


_CR_TOKEN_RE = re.compile(r"([A-Z]{1,2})|([+-])")


def _eval_cr_formula(formula: str, values: dict[str, Decimal]) -> Decimal:
    """
    Evaluate formulas like: "XB-RA+RB+TE-RE" using Decimal arithmetic.
    Supports only refs (A-Z, 1-2 chars) and + / -.
    """
    tokens = [m.group(0) for m in _CR_TOKEN_RE.finditer(formula.replace(" ", ""))]
    if not tokens:
        return Decimal("0")

    total = Decimal("0")
    op = "+"
    for tok in tokens:
        if tok in {"+", "-"}:
            op = tok
            continue
        value = values.get(tok, Decimal("0"))
        total = total + value if op == "+" else total - value
    return total


@dataclass(frozen=True)
class CompteResultatComputed:
    year: int
    values_n: dict[str, Decimal]
    values_n_1: dict[str, Decimal]
    resultat_net_n: Decimal
    total_income_n: Decimal
    total_expense_n: Decimal
    total_income_n_1: Decimal
    total_expense_n_1: Decimal


def compute_compte_resultat(user: User, year: int) -> CompteResultatComputed:
    structure = _load_template_json("compte_resultat_structure.json")
    lignes: list[dict[str, Any]] = structure["lignes"]

    start_n, end_n = _year_bounds(year)
    start_n_1, end_n_1 = _year_bounds(year - 1)

    tx_n = Transaction.objects.filter(user=user, date__gte=start_n, date__lt=end_n).only(
        "amount",
        "type",
        "category",
        "name",
    )
    tx_n_1 = Transaction.objects.filter(user=user, date__gte=start_n_1, date__lt=end_n_1).only(
        "amount",
        "type",
        "category",
        "name",
    )

    values_n: dict[str, Decimal] = {item["ref"]: Decimal("0") for item in lignes}
    values_n_1: dict[str, Decimal] = {item["ref"]: Decimal("0") for item in lignes}

    total_income_n = Decimal("0")
    total_expense_n = Decimal("0")
    for tx in tx_n:
        ref = _map_transaction_to_cr_ref(tx)
        amount = Decimal(tx.amount)
        values_n[ref] = values_n.get(ref, Decimal("0")) + amount
        if tx.type == "income":
            total_income_n += amount
        else:
            total_expense_n += amount

    total_income_n_1 = Decimal("0")
    total_expense_n_1 = Decimal("0")
    for tx in tx_n_1:
        ref = _map_transaction_to_cr_ref(tx)
        amount = Decimal(tx.amount)
        values_n_1[ref] = values_n_1.get(ref, Decimal("0")) + amount
        if tx.type == "income":
            total_income_n_1 += amount
        else:
            total_expense_n_1 += amount

    # Compute total lines in order (formulas reference previous totals, order in structure matters)
    for item in lignes:
        if not item.get("is_total"):
            continue
        formula = item.get("formula") or ""
        values_n[item["ref"]] = _eval_cr_formula(formula, values_n)
        values_n_1[item["ref"]] = _eval_cr_formula(formula, values_n_1)

    # For MVP, use the computed XI if available; fallback to income-expense.
    resultat_net_n = values_n.get("XI")
    if resultat_net_n is None:
        resultat_net_n = total_income_n - total_expense_n

    return CompteResultatComputed(
        year=year,
        values_n=values_n,
        values_n_1=values_n_1,
        resultat_net_n=resultat_net_n,
        total_income_n=total_income_n,
        total_expense_n=total_expense_n,
        total_income_n_1=total_income_n_1,
        total_expense_n_1=total_expense_n_1,
    )


def generate_compte_resultat_csv(compte: CompteResultatComputed) -> bytes:
    structure = _load_template_json("compte_resultat_structure.json")
    lignes: list[dict[str, Any]] = structure["lignes"]

    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["REF", "LIBELLES", "NUMERO DE COMPTES", "MONTANT_N", "MONTANT_N_1"])
    for item in lignes:
        ref = item["ref"]
        writer.writerow(
            [
                ref,
                item.get("libelle", ""),
                item.get("compte", ""),
                str(compte.values_n.get(ref, Decimal("0"))),
                str(compte.values_n_1.get(ref, Decimal("0"))),
            ]
        )
    return out.getvalue().encode("utf-8")


def generate_bilan_csv(user: User, compte: CompteResultatComputed) -> bytes:
    structure = _load_template_json("bilan_structure.json")
    actif: list[dict[str, Any]] = structure["actif"]
    passif: list[dict[str, Any]] = structure["passif"]

    # Minimal model: only cash + equity + result to keep the bilan balanced.
    cash_n = user.initial_balance + compte.total_income_n - compte.total_expense_n
    cash_n_1 = user.initial_balance + compte.total_income_n_1 - compte.total_expense_n_1

    capital_n = user.initial_balance
    capital_n_1 = user.initial_balance

    # Actif values stored by ref: BRUT, AMORT, NET_N, NET_N_1
    brut: dict[str, Decimal] = {item["ref"]: Decimal("0") for item in actif}
    amort: dict[str, Decimal] = {item["ref"]: Decimal("0") for item in actif}

    brut["BS"] = Decimal(cash_n)
    amort["BS"] = Decimal("0")

    brut_n_1: dict[str, Decimal] = {item["ref"]: Decimal("0") for item in actif}
    amort_n_1: dict[str, Decimal] = {item["ref"]: Decimal("0") for item in actif}
    brut_n_1["BS"] = Decimal(cash_n_1)
    amort_n_1["BS"] = Decimal("0")

    def net_for(ref: str) -> Decimal:
        return brut.get(ref, Decimal("0")) - amort.get(ref, Decimal("0"))

    def net_for_n_1(ref: str) -> Decimal:
        return brut_n_1.get(ref, Decimal("0")) - amort_n_1.get(ref, Decimal("0"))

    # Compute header subtotals (stable SYSCOHADA groupings)
    header_groups = {
        "AD": ["AE", "AF", "AG", "AH"],
        "AI": ["AJ", "AK", "AL", "AM", "AN", "AP"],
        "AQ": ["AR", "AS"],
        "BG": ["BH", "BI", "BJ"],
    }
    for header_ref, children in header_groups.items():
        brut[header_ref] = sum((brut.get(c, Decimal("0")) for c in children), Decimal("0"))
        amort[header_ref] = sum((amort.get(c, Decimal("0")) for c in children), Decimal("0"))
        brut_n_1[header_ref] = sum((brut_n_1.get(c, Decimal("0")) for c in children), Decimal("0"))
        amort_n_1[header_ref] = sum((amort_n_1.get(c, Decimal("0")) for c in children), Decimal("0"))

    # Compute totals based on formulas (only '+' is expected in these bilan totals)
    def parse_bilan_sum_formula(formula: str) -> list[str]:
        return [part.strip() for part in formula.split("+") if part.strip()]

    for item in actif:
        if not item.get("is_total"):
            continue
        parts = parse_bilan_sum_formula(item.get("formula", ""))
        brut[item["ref"]] = sum((brut.get(p, Decimal("0")) for p in parts), Decimal("0"))
        amort[item["ref"]] = sum((amort.get(p, Decimal("0")) for p in parts), Decimal("0"))
        brut_n_1[item["ref"]] = sum((brut_n_1.get(p, Decimal("0")) for p in parts), Decimal("0"))
        amort_n_1[item["ref"]] = sum((amort_n_1.get(p, Decimal("0")) for p in parts), Decimal("0"))

    # Passif values: NET only, but handle "negative" lines like CB by applying sign.
    passif_meta: dict[str, dict[str, Any]] = {item["ref"]: item for item in passif}
    net_passif_n: dict[str, Decimal] = {item["ref"]: Decimal("0") for item in passif}
    net_passif_n_1: dict[str, Decimal] = {item["ref"]: Decimal("0") for item in passif}

    net_passif_n["CA"] = Decimal(capital_n)
    net_passif_n_1["CA"] = Decimal(capital_n_1)

    net_passif_n["CJ"] = Decimal(compte.resultat_net_n)
    net_passif_n_1["CJ"] = Decimal("0")  # not computed in this MVP

    def signed_passif_value(values: dict[str, Decimal], ref: str) -> Decimal:
        val = values.get(ref, Decimal("0"))
        meta = passif_meta.get(ref, {})
        if meta.get("is_negative"):
            return -val
        return val

    def eval_passif_formula(values: dict[str, Decimal], formula: str) -> Decimal:
        parts = parse_bilan_sum_formula(formula)
        return sum((signed_passif_value(values, p) for p in parts), Decimal("0"))

    for item in passif:
        if not item.get("is_total"):
            continue
        ref = item["ref"]
        net_passif_n[ref] = eval_passif_formula(net_passif_n, item.get("formula", ""))
        net_passif_n_1[ref] = eval_passif_formula(net_passif_n_1, item.get("formula", ""))

    # Build a single CSV containing both sections.
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["SECTION", "REF", "LIBELLE", "NOTE", "BRUT", "AMORT/DEPREC", "NET_N", "NET_N_1"])

    for item in actif:
        ref = item["ref"]
        writer.writerow(
            [
                "ACTIF",
                ref,
                item.get("libelle", ""),
                item.get("note", ""),
                str(brut.get(ref, Decimal("0"))),
                str(amort.get(ref, Decimal("0"))),
                str(net_for(ref)),
                str(net_for_n_1(ref)),
            ]
        )

    for item in passif:
        ref = item["ref"]
        writer.writerow(
            [
                "PASSIF",
                ref,
                item.get("libelle", ""),
                item.get("note", ""),
                "",
                "",
                str(signed_passif_value(net_passif_n, ref)),
                str(signed_passif_value(net_passif_n_1, ref)),
            ]
        )

    return out.getvalue().encode("utf-8")

