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

from django.db import models
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


def _pick_effective_datetime(tx: Transaction) -> datetime:
    """
    Choisit la date "effective" d'une transaction pour les rapports.

    Contexte: certains clients envoient une `date` incorrecte (ex: horloge appareil en 2024)
    alors que `created_at` (serveur) est correcte (2026).

    Règle:
    - si l'écart absolu entre `date` et `created_at` dépasse 180 jours,
      on utilise `created_at` comme date effective.
    - sinon on conserve `date`.
    """
    try:
        created_at = tx.created_at
        tx_date = tx.date
        if created_at and tx_date:
            delta_days = abs((tx_date - created_at).days)
            if delta_days > 180:
                return created_at
        return tx_date
    except Exception:
        return tx.date


def _in_year_bounds(tx: Transaction, start: datetime, end: datetime) -> bool:
    eff = _pick_effective_datetime(tx)
    return start <= eff < end


def _map_transaction_to_cr_ref_from_user_rules(user: User, tx: Transaction) -> tuple[str | None, bool]:
    """
    Map via règles utilisateur (priorité) si disponibles.
    Retourne: (ref|None, matched_via_rule)
    """
    from .models import SyscohadaCRMappingRule

    try:
        rules = SyscohadaCRMappingRule.objects.filter(user=user, is_active=True).order_by("priority", "-updated_at", "-id")
    except Exception:
        # Si les migrations ne sont pas appliquées ou table absente, ignorer les règles
        return None, False
    if not rules.exists():
        return None, False

    category = _normalize_text(getattr(tx, "category", ""))
    name = _normalize_text(getattr(tx, "name", ""))

    for rule in rules:
        if rule.tx_type and rule.tx_type != tx.type:
            continue

        cat_pat = (rule.category_pattern or "").strip()
        name_pat = (rule.name_pattern or "").strip()

        # Wildcard rule (no patterns) is allowed for explicit fallbacks
        if rule.match_mode == "contains":
            ok_cat = True if not cat_pat else _normalize_text(cat_pat) in category
            ok_name = True if not name_pat else _normalize_text(name_pat) in name
            if ok_cat and ok_name:
                return rule.ref, True
        else:  # regex
            ok_cat = True
            ok_name = True
            try:
                if cat_pat:
                    ok_cat = re.search(cat_pat, category, flags=re.IGNORECASE) is not None
                if name_pat:
                    ok_name = re.search(name_pat, name, flags=re.IGNORECASE) is not None
            except re.error:
                # Si regex invalide: ignorer la règle (robustesse)
                continue

            if ok_cat and ok_name:
                return rule.ref, True

    return None, False


def _map_transaction_to_cr_ref_default(tx: Transaction) -> str | None:
    """
    Mapping "par défaut" (sans règles utilisateur) basé sur mots-clés.
    Retourne None si aucune catégorie n'est reconnue (=> transaction non mappée).
    """
    category = _normalize_text(getattr(tx, "category", ""))
    name = _normalize_text(getattr(tx, "name", ""))
    haystack = f"{category} {name}".strip()

    if tx.type == "income":
        if any(k in haystack for k in ["service", "prestation", "consult", "honoraire"]):
            return "TC"  # travaux / services vendus
        if any(k in haystack for k in ["accessoire"]):
            return "TD"
        if any(k in haystack for k in ["vente", "ventes", "marchandise", "produit", "produits"]):
            return "TA"
        return None

    # expense
    if any(k in haystack for k in ["achat", "achats", "marchandise", "appro", "approvisionnement", "fournisseur"]):
        return "RA"
    if any(k in haystack for k in ["transport", "taxi", "bus", "essence", "carburant", "livraison", "deplacement", "déplacement"]):
        return "RG"
    if any(
        k in haystack
        for k in [
            "loyer",
            "internet",
            "eau",
            "electric",
            "électric",
            "telephone",
            "téléphone",
            "prestataire",
            "maintenance",
            "marketing",
            "publicit",
            "publicité",
            "pub",
            "assurance",
        ]
    ):
        return "RH"
    if any(k in haystack for k in ["impot", "impôt", "taxe", "douane", "etat", "état", "tva"]):
        return "RI"
    if any(k in haystack for k in ["salaire", "salaires", "personnel", "paie", "payroll", "prime"]):
        return "RK"
    return None


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
    unmapped_tx_ids_n: list[int]
    unmapped_tx_ids_n_1: list[int]


def compute_compte_resultat(user: User, year: int) -> CompteResultatComputed:
    structure = _load_template_json("compte_resultat_structure.json")
    lignes: list[dict[str, Any]] = structure["lignes"]

    start_n, end_n = _year_bounds(year)
    start_n_1, end_n_1 = _year_bounds(year - 1)

    # Important: include both date- and created_at-based windows, then decide per-row
    # to handle device clock issues (date far from created_at).
    tx_candidates_n = Transaction.objects.filter(
        user=user,
    ).filter(
        (models.Q(date__gte=start_n, date__lt=end_n))
        | (models.Q(created_at__gte=start_n, created_at__lt=end_n))
    ).only("id", "amount", "type", "category", "name", "date", "created_at")

    tx_candidates_n_1 = Transaction.objects.filter(
        user=user,
    ).filter(
        (models.Q(date__gte=start_n_1, date__lt=end_n_1))
        | (models.Q(created_at__gte=start_n_1, created_at__lt=end_n_1))
    ).only("id", "amount", "type", "category", "name", "date", "created_at")

    tx_n = [tx for tx in tx_candidates_n if _in_year_bounds(tx, start_n, end_n)]
    tx_n_1 = [tx for tx in tx_candidates_n_1 if _in_year_bounds(tx, start_n_1, end_n_1)]

    values_n: dict[str, Decimal] = {item["ref"]: Decimal("0") for item in lignes}
    values_n_1: dict[str, Decimal] = {item["ref"]: Decimal("0") for item in lignes}
    unmapped_tx_ids_n: list[int] = []
    unmapped_tx_ids_n_1: list[int] = []

    total_income_n = Decimal("0")
    total_expense_n = Decimal("0")
    for tx in tx_n:
        ref, matched_via_rule = _map_transaction_to_cr_ref_from_user_rules(user, tx)
        if not ref:
            ref = _map_transaction_to_cr_ref_default(tx)
            if not ref:
                unmapped_tx_ids_n.append(tx.id)
                ref = "RJ"  # Divers / fallback (si présent dans le template)
        if ref not in values_n:
            # ref inconnue => fallback RJ + marquer unmapped
            unmapped_tx_ids_n.append(tx.id)
            ref = "RJ"
        amount = Decimal(tx.amount)
        values_n[ref] = values_n.get(ref, Decimal("0")) + amount
        if tx.type == "income":
            total_income_n += amount
        else:
            total_expense_n += amount

    total_income_n_1 = Decimal("0")
    total_expense_n_1 = Decimal("0")
    for tx in tx_n_1:
        ref, matched_via_rule = _map_transaction_to_cr_ref_from_user_rules(user, tx)
        if not ref:
            ref = _map_transaction_to_cr_ref_default(tx)
            if not ref:
                unmapped_tx_ids_n_1.append(tx.id)
                ref = "RJ"
        if ref not in values_n_1:
            unmapped_tx_ids_n_1.append(tx.id)
            ref = "RJ"
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
        unmapped_tx_ids_n=unmapped_tx_ids_n,
        unmapped_tx_ids_n_1=unmapped_tx_ids_n_1,
    )


def compute_bilan_values(user: User, year: int, compte: CompteResultatComputed) -> dict[str, object]:
    """
    Calcule les valeurs du bilan (Actif/Passif) en combinant:
    - soldes saisis/importés (SyscohadaBilanBalance)
    - auto-calc: BS (trésorerie) et CJ (résultat net)

    Retourne une structure JSON-friendly utilisable par preview + export.
    """
    from .models import SyscohadaBilanBalance

    structure = _load_template_json("bilan_structure.json")
    actif: list[dict[str, Any]] = structure["actif"]
    passif: list[dict[str, Any]] = structure["passif"]

    # Load user balances for N and N-1 (support colonnes N et N-1)
    try:
        # Force evaluation inside try: sqlite can raise "no such table" only at iteration time.
        balances_n = list(SyscohadaBilanBalance.objects.filter(user=user, year=year))
        balances_n_1 = list(SyscohadaBilanBalance.objects.filter(user=user, year=year - 1))
    except Exception:
        # Table absente / migrations non appliquées: fallback sans soldes saisis
        balances_n = []
        balances_n_1 = []

    def split_balances(qs):
        actif_bal: dict[str, dict[str, Decimal]] = {}
        passif_bal: dict[str, Decimal] = {}
        for b in qs:
            if b.section == "ACTIF":
                actif_bal[b.ref] = {
                    "brut": Decimal(b.brut or 0),
                    "amort": Decimal(b.amort or 0),
                }
            else:
                passif_bal[b.ref] = Decimal(b.net or 0)
        return actif_bal, passif_bal

    actif_bal_n, passif_bal_n = split_balances(balances_n)
    actif_bal_n_1, passif_bal_n_1 = split_balances(balances_n_1)

    # Auto-calc BS (cash) for N and N-1
    cash_n = user.initial_balance + compte.total_income_n - compte.total_expense_n
    cash_n_1 = user.initial_balance + compte.total_income_n_1 - compte.total_expense_n_1

    actif_bal_n["BS"] = {"brut": Decimal(cash_n), "amort": Decimal("0")}
    actif_bal_n_1["BS"] = {"brut": Decimal(cash_n_1), "amort": Decimal("0")}

    # Auto-calc CJ (resultat net) in passif (if template contains CJ)
    passif_bal_n["CJ"] = Decimal(compte.resultat_net_n)
    # For N-1 we use computed XI if present; otherwise 0
    passif_bal_n_1["CJ"] = Decimal(compte.values_n_1.get("XI", Decimal("0")))

    # Compute totals (validation): TOTAL ACTIF (BZ) vs TOTAL PASSIF (DZ)
    def compute_totals_for(
        actif_bal: dict[str, dict[str, Decimal]],
        passif_bal: dict[str, Decimal],
        cash: Decimal,
        resultat: Decimal,
    ) -> dict[str, str]:
        brut: dict[str, Decimal] = {item["ref"]: Decimal("0") for item in actif}
        amort: dict[str, Decimal] = {item["ref"]: Decimal("0") for item in actif}
        for ref, v in actif_bal.items():
            brut[ref] = Decimal(v.get("brut", 0))
            amort[ref] = Decimal(v.get("amort", 0))

        brut["BS"] = Decimal(cash)
        amort["BS"] = Decimal("0")

        net_passif: dict[str, Decimal] = {item["ref"]: Decimal("0") for item in passif}
        for ref, v in passif_bal.items():
            net_passif[ref] = Decimal(v)
        net_passif["CJ"] = Decimal(resultat)

        def net_for(ref: str) -> Decimal:
            return brut.get(ref, Decimal("0")) - amort.get(ref, Decimal("0"))

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

        # Compute totals based on formulas (only '+' is expected in these bilan totals)
        def parse_sum_formula(formula: str) -> list[str]:
            return [part.strip() for part in formula.split("+") if part.strip()]

        for item in actif:
            if not item.get("is_total"):
                continue
            parts = parse_sum_formula(item.get("formula", ""))
            brut[item["ref"]] = sum((brut.get(p, Decimal("0")) for p in parts), Decimal("0"))
            amort[item["ref"]] = sum((amort.get(p, Decimal("0")) for p in parts), Decimal("0"))

        passif_meta: dict[str, dict[str, Any]] = {item["ref"]: item for item in passif}

        def signed_passif_value(ref: str) -> Decimal:
            val = net_passif.get(ref, Decimal("0"))
            meta = passif_meta.get(ref, {})
            if meta.get("is_negative"):
                return -val
            return val

        for item in passif:
            if not item.get("is_total"):
                continue
            parts = parse_sum_formula(item.get("formula", ""))
            net_passif[item["ref"]] = sum((signed_passif_value(p) for p in parts), Decimal("0"))

        total_actif = net_for("BZ")
        total_passif = signed_passif_value("DZ")
        delta = total_actif - total_passif
        return {
            "total_actif": str(total_actif),
            "total_passif": str(total_passif),
            "delta": str(delta),
        }

    totals_n = compute_totals_for(actif_bal_n, passif_bal_n, cash_n, compte.resultat_net_n)
    totals_n_1 = compute_totals_for(actif_bal_n_1, passif_bal_n_1, cash_n_1, passif_bal_n_1["CJ"])

    return {
        "year": year,
        "auto": {
            "BS": {"net_n": str(cash_n), "net_n_1": str(cash_n_1)},
            "CJ": {"net_n": str(compte.resultat_net_n), "net_n_1": str(passif_bal_n_1["CJ"])},
        },
        "totals": {"n": totals_n, "n_1": totals_n_1},
        "actif": {ref: {"brut": str(v["brut"]), "amort": str(v["amort"])} for ref, v in actif_bal_n.items()},
        "passif": {ref: str(v) for ref, v in passif_bal_n.items()},
        "actif_n_1": {ref: {"brut": str(v["brut"]), "amort": str(v["amort"])} for ref, v in actif_bal_n_1.items()},
        "passif_n_1": {ref: str(v) for ref, v in passif_bal_n_1.items()},
    }


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
    from .models import SyscohadaBilanBalance

    # Actif values stored by ref: BRUT, AMORT, NET_N, NET_N_1
    brut: dict[str, Decimal] = {item["ref"]: Decimal("0") for item in actif}
    amort: dict[str, Decimal] = {item["ref"]: Decimal("0") for item in actif}
    brut_n_1: dict[str, Decimal] = {item["ref"]: Decimal("0") for item in actif}
    amort_n_1: dict[str, Decimal] = {item["ref"]: Decimal("0") for item in actif}

    # Passif values stored by ref: NET_N, NET_N_1
    passif_meta: dict[str, dict[str, Any]] = {item["ref"]: item for item in passif}
    net_passif_n: dict[str, Decimal] = {item["ref"]: Decimal("0") for item in passif}
    net_passif_n_1: dict[str, Decimal] = {item["ref"]: Decimal("0") for item in passif}

    # 1) Load user-provided balances (N and N-1) (optional)
    try:
        # Force evaluation inside try: sqlite can raise "no such table" only at iteration time.
        balances_n = list(SyscohadaBilanBalance.objects.filter(user=user, year=compte.year))
        balances_n_1 = list(SyscohadaBilanBalance.objects.filter(user=user, year=compte.year - 1))
    except Exception:
        balances_n = []
        balances_n_1 = []

    for b in balances_n:
        if b.section == "ACTIF":
            brut[b.ref] = Decimal(b.brut or 0)
            amort[b.ref] = Decimal(b.amort or 0)
        else:
            net_passif_n[b.ref] = Decimal(b.net or 0)

    for b in balances_n_1:
        if b.section == "ACTIF":
            brut_n_1[b.ref] = Decimal(b.brut or 0)
            amort_n_1[b.ref] = Decimal(b.amort or 0)
        else:
            net_passif_n_1[b.ref] = Decimal(b.net or 0)

    # 2) Auto-calc: cash (BS) + result (CJ)
    cash_n = user.initial_balance + compte.total_income_n - compte.total_expense_n
    cash_n_1 = user.initial_balance + compte.total_income_n_1 - compte.total_expense_n_1
    brut["BS"] = Decimal(cash_n)
    amort["BS"] = Decimal("0")
    brut_n_1["BS"] = Decimal(cash_n_1)
    amort_n_1["BS"] = Decimal("0")

    net_passif_n["CJ"] = Decimal(compte.resultat_net_n)
    net_passif_n_1["CJ"] = Decimal(compte.values_n_1.get("XI", Decimal("0")))

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

    # Notes: CA (capital) et autres postes doivent venir des soldes saisis/importés.

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
