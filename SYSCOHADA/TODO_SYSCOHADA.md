# TODO — Intégration SYSCOHADA (Compte de résultat + Bilan)

Objectif final: l’utilisateur peut générer **uniquement 2 exports**:
- Compte de résultat SYSCOHADA
- Bilan SYSCOHADA (Actif/Passif)

---

## P0 — Cadrage (bloquants)

- Définir la période “Exercice” (annuelle uniquement au début, ex: 2026) et la règle de comparaison N-1.
- Décider le format de sortie prioritaire: `xlsx` (recommandé) + `csv` optionnel.
- Valider la stratégie de conformité:
  - MVP: mapping transactions → lignes SYSCOHADA + bilan minimal + saisie soldes
  - ou “couche comptable” immédiate (plus long).

---

## P1 — Compte de résultat (MVP)

- Créer un écran “Mapping SYSCOHADA (CR)”:
  - associer `Transaction.type + Transaction.category` → `ref` (TA, RG, RH, …)
  - presets (vente/transport/services/taxes/autres).
- Implémenter une logique “matching” (priorité, contains, regex).
- Implémenter le calcul CR:
  - agrégation par `ref` sur exercice N (+ N-1 si demandé)
  - garder les lignes non couvertes à 0
  - produire aussi la liste des transactions non mappées
- Générer le fichier:
  - XLSX: valeurs dans les lignes de base + formules pour totaux (XA..XI)
  - CSV: totaux calculés côté backend
- Ajouter un endpoint `preview` pour debug (montants + unmapped).

Tests:
- Cas minimal: 2 revenus + 2 dépenses → vérifier TA/RG/RH/RJ + XI.
- Cas “unmapped”: transaction sans mapping → warning + non incluse (ou incluse dans RJ selon fallback choisi).

---

## P2 — Bilan (MVP “minimal + saisie”)

- Créer une table de “soldes d’ouverture / ajustements”:
  - par utilisateur
  - par exercice
  - par `ref` du bilan (CA, BS, BI, DJ, …) et/ou par groupe.
- UI:
  - écran “Soldes SYSCOHADA” (import CSV + édition manuelle)
  - affichage de l’équilibre Actif/Passif (delta)
- Auto-calcul:
  - `BS` (trésorerie actif) depuis `initial_balance + revenus - dépenses` à la clôture
  - `CJ` (résultat net) depuis `XI` du compte de résultat
- Génération fichier:
  - XLSX: remplir les lignes élémentaires, garder totaux en formules (AZ/BK/BT/BZ etc.)
  - CSV: totaux calculés côté backend
- Ajouter endpoint `preview`:
  - valeurs auto vs saisies
  - delta bilan (BZ - DZ)

Tests:
- Cas minimal: uniquement trésorerie + capital + résultat → BZ == DZ.

---

## P3 — Cohérence & gouvernance

- Verrouillage d’exercice (optionnel):
  - empêcher la modification des soldes après clôture
- Historique / audit:
  - conserver l’export généré (ou hash) pour traçabilité
- Gestion multi-devises:
  - préciser la devise du report (XOF) et la conversion si nécessaire

---

## P4 — Conformité avancée (après MVP)

- Ajouter une “couche comptable” (plan de comptes + écritures en partie double).
- Ajouter:
  - clients/fournisseurs (créances/dettes),
  - immobilisations + amortissements,
  - stocks (quantités + valorisation) pour alimenter 603x,
  - impôt sur résultat / HAO / financier.
- Faire correspondre les lignes SYSCOHADA au solde des comptes (agrégation par plages 60..69 / 70..79 etc.).

