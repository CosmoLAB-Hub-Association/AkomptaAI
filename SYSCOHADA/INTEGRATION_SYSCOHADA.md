# Intégration SYSCOHADA (Bilan + Compte de résultat) — Note de conception

Contexte: le dépôt **AkomptaAI** contient déjà des gabarits SYSCOHADA (CSV/XLSX) + des structures JSON décrivant les lignes et les formules.
Objectif: concevoir un **système intégré** (backend + frontend) permettant de générer **uniquement 2 fichiers** exportables par l’utilisateur:

1. **Compte de résultat SYSCOHADA**
2. **Bilan SYSCOHADA (Actif/Passif)**

Ce document ne code rien: il décrit les choix d’architecture, le modèle de données requis, et une stratégie MVP → conforme progressivement.

---

## 1) Sources SYSCOHADA déjà présentes dans le repo

### 1.1 Compte de résultat (structure + formules)

- Structure des lignes et formules:
  - `SYSCOHADA/Compte_Resultat_SYSCOHADA/compte_resultat_structure.json`
  - Champs clés: `ref`, `libelle`, `compte` (n° comptes OHADA), `type` (produit/charge/mixte), `formula` (pour les totaux), `bg_color` (formatting XLSX).
- Interprétation “backend” (structure + nomenclature):
  - `SYSCOHADA/Compte_Resultat_SYSCOHADA/syscohada_cr_backend.json`
- Gabarits:
  - `SYSCOHADA/Compte_Resultat_SYSCOHADA/Compte_Resultat_SYSCOHADA.xlsx`
  - `SYSCOHADA/Compte_Resultat_SYSCOHADA/Compte_Resultat_SYSCOHADA.csv`
- Script de génération statique (zéros + formules Excel):
  - `SYSCOHADA/Compte_Resultat_SYSCOHADA/generate_compte_resultat.py`

### 1.2 Bilan (structure + formules)

- Structure des lignes (Actif/Passif, en “refs” AD…DZ):
  - `SYSCOHADA/Comment créer un bilan comptable conforme à SYSCOHADA/bilan_structure.json`
- Interprétation “backend” (regroupements + formules clés FR/BFG/TN):
  - `SYSCOHADA/Comment créer un bilan comptable conforme à SYSCOHADA/syscohada_bilan_backend.json`
- Gabarits:
  - `SYSCOHADA/Comment créer un bilan comptable conforme à SYSCOHADA/Bilan_SYSCOHADA_Complet.xlsx`
    - contient 4 feuilles: `ACTIF`, `PASSIF`, `Mapping API`, `JSON_Export`
  - `SYSCOHADA/Comment créer un bilan comptable conforme à SYSCOHADA/Bilan_ACTIF_SYSCOHADA.csv`
  - `SYSCOHADA/Comment créer un bilan comptable conforme à SYSCOHADA/Bilan_PASSIF_SYSCOHADA.csv`
- Script de génération statique (zéros + formules Excel):
  - `SYSCOHADA/Comment créer un bilan comptable conforme à SYSCOHADA/generate_bilan.py`

> Remarque importante: les scripts présents génèrent des fichiers “structurels” (tout à 0 + formules). L’intégration Akompta doit **remplir les montants** à partir des données réelles.

---

## 2) État actuel d’AkomptaAI (données disponibles) et limites

### 2.1 Données disponibles (aujourd’hui)

Backend (modèles existants):
- `Transaction`: `amount`, `type` (`income|expense`), `category` (string), `date`, `currency`
- `Product`: prix / catégorie / stock_status (mais pas de quantité / valorisation de stock)
- `User`: `initial_balance` (solde initial, utile pour la trésorerie)

Frontend:
- Les écrans manipulent surtout des transactions “cash-like”.
- Il n’existe pas de **journal comptable**, ni de **plan de comptes**, ni de **pièces comptables**.

### 2.2 Ce qui manque pour être SYSCOHADA “pleinement” conforme

SYSCOHADA suppose une comptabilité en partie double et des soldes par comptes:
- Plan de comptes (classes 1 à 8), comptes auxiliaires (clients/fournisseurs), journaux.
- Immobilisations: acquisition, amortissements, cessions.
- Stocks: quantités, CUMP/FIFO selon politique, variations de stocks (603x).
- Créances/dettes: ventes/achats à crédit, règlements partiels.
- Fiscalité/social: TVA, impôts, charges sociales.

Conclusion:
- **Le compte de résultat** peut être produit en **MVP** en se basant sur les transactions, à condition d’avoir une **table de mapping** vers les “lignes SYSCOHADA”.
- **Le bilan** ne peut pas être complet sans un modèle de “soldes” (ou saisie d’Ouverture/Clôture) car Akompta n’enregistre pas (encore) toutes les catégories nécessaires (clients, fournisseurs, immobilisations, dettes…).

Stratégie recommandée: implémenter une conformité **progressive**, en commençant par un bilan minimal + saisies d’ajustement, puis enrichir le modèle.

---

## 3) Cible produit: génération de 2 fichiers

### 3.1 Exigence fonctionnelle (minimum)

Pour un utilisateur authentifié:
- Choisir une période (ex: exercice fiscal N = 2026, ou date de début/fin)
- Générer:
  - `Compte_Resultat_SYSCOHADA_<N>.xlsx` (avec colonnes N et N-1 si demandé)
  - `Bilan_SYSCOHADA_<N>.xlsx` (ACTIF/PASSIF, colonnes N et N-1 si demandé)

Formats:
- XLSX prioritaire (car les gabarits utilisent des formules + mise en forme).
- CSV en option (mais moins “présentation”).

### 3.2 Exigence de qualité

- Reproductible: mêmes données → mêmes montants.
- Traçable: chaque montant d’une ligne peut être expliqué (“d’où ça vient”).
- Cohérent: le bilan doit respecter **TOTAL ACTIF (BZ) = TOTAL PASSIF (DZ)**.
- Robuste: si un mapping est incomplet, le système doit:
  - produire un rapport partiel,
  - afficher des warnings,
  - lister les transactions non mappées.

---

## 4) Conception: données à ajouter (sans casser l’existant)

Deux options possibles. La recommandation est **Option B** (plus propre), mais **Option A** permet un MVP rapide.

### Option A — MVP “mapping simple” (rapide, mais limité)

Ajouter une table de configuration:

1) `SyscohadaCategoryMapping`
- `user` (ou global par tenant)
- `direction`: `income|expense`
- `category_pattern` (string / regex / exact match)
- `syscohada_ref` (ex: `TA`, `RG`, `RH`… pour CR)
- `syscohada_compte` (ex: `701`, `61`… pour audit)
- `priority` (si plusieurs patterns matchent)

2) `SyscohadaOpeningBalances` (pour le bilan MVP)
- `user`
- `exercise_year`
- `ref` (ex: `CA`, `BS`, `BI`… ou directement les “refs” du gabarit bilan)
- `net_n` / `net_n_1` (ou “opening/closing”)

Avantage: rapide à intégrer sans refactor profond.
Limite: pas de partie double, pas de vrais soldes par comptes; bilan = “saisie + trésorerie + résultat”.

### Option B — “couche comptable” (conforme, extensible)

Ajouter une app `accounting/` (ou `compta/`) avec:

1) `Account` (Plan de comptes SYSCOHADA)
- `code` (ex: `701`, `601`, `571`, `411`, `401`…)
- `label`
- `class` (1..8)
- `normal_balance` (`debit|credit`)
- `is_active`

2) `JournalEntry` (pièce)
- `user`
- `date`
- `description`
- `source_type` / `source_id` (ex: lien vers `Transaction`)
- `status` (draft/posted)

3) `JournalLine` (ligne d’écriture)
- `entry`
- `account`
- `debit`
- `credit`
- `partner` (optionnel)

4) `FiscalYear` / `Period` (verrouillage)
- bornes, statut “closed”, etc.

Principe: chaque action métier (transaction) génère 2 lignes (débit/crédit).
Ensuite, CR et Bilan deviennent:
- des **agrégations** de soldes de comptes sur une période (CR)
- des **soldes à date** (Bilan)

Avantage: conformité réelle, bilan complet possible.
Inconvénient: plus long, nécessite UI & migration conceptuelle.

---

## 5) Calcul du Compte de Résultat (MVP)

### 5.1 Périmètre MVP recommandé

Supporter correctement au moins:
- `TA` (701) Ventes de marchandises
- `RA` (601) Achats de marchandises
- Charges “courantes”:
  - `RG` (61) Transports
  - `RH` (62-63) Services extérieurs
  - `RI` (64) Impôts et taxes
  - `RJ` (65) Autres charges

Et laisser 0 pour le reste tant que non mappé (603x variations stock, amortissements, financier, HAO, impôt résultat…).

### 5.2 Règle d’agrégation (simple)

Sur un exercice N:
- Pour chaque `Transaction`:
  - déterminer une **ligne SYSCOHADA** (ref) via mapping (ex: “Ventes” → `TA`)
  - sommer `amount` dans `MONTANT_N` pour la ref

Même chose pour N-1, si l’utilisateur demande la comparaison.

Notes:
- Les lignes `mixte` (ex: RB, RD, RF) exigent des données de stock; en MVP → 0 (ou saisie manuelle).
- Les formules (XA, XB, XC, … XI) doivent être recalculées côté serveur **ou** laissées en formules Excel.
  - Recommandation: remplir les lignes “de base”, garder les totaux en formules Excel (comme les scripts).

### 5.3 Sortie fichier

Utiliser le gabarit/structure JSON `compte_resultat_structure.json` comme source de vérité:
- ordre des lignes
- formules (totaux)
- numéros de comptes attendus (pour audit)

Production:
- XLSX: valeurs + formules pour totaux
- CSV: valeurs (totaux calculés côté backend si CSV)

### 5.4 “Explainabilité”

En plus du fichier, le backend peut retourner:
- la liste des transactions non mappées (pour corriger le paramétrage)
- un breakdown: “ref → somme + liste d’IDs de transactions”

---

## 6) Calcul du Bilan (MVP “bilan minimal + ajustements”)

### 6.1 Pourquoi un bilan MVP est nécessairement “partiel”

Le gabarit bilan attend des postes (créances clients `BI`, dettes fournisseurs `DJ`, stocks `BB`, immobilisations `AD/AI/AQ`, etc.).
Aujourd’hui Akompta n’a pas de tables pour:
- factures clients/fournisseurs,
- immobilisations,
- emprunts,
- stock valorisé.

Donc, pour un bilan “propre” il faut **au moins**:
- des soldes d’ouverture (au 01/01/N)
- des ajustements/clôture (au 31/12/N)

### 6.2 Proposition MVP pragmatique

1) Remplir automatiquement:
- `BS` (Banques/caisse) = solde calculé (initial_balance + revenus - dépenses) à la date de clôture
- `CJ` (Résultat net) = `XI` du compte de résultat (même exercice)

2) Demander à l’utilisateur (ou comptable) de saisir / importer:
- `CA` capital, réserves, dettes, créances, stocks, immobilisations, etc.
  - soit via un écran “Soldes d’ouverture / ajustements”
  - soit via import CSV

3) Vérifier l’équilibre:
- Actif total `BZ` doit = Passif total `DZ`
- si non: indiquer l’écart et proposer des pistes (ex: capital / compte d’attente) selon règles métier.

### 6.3 Formules et totaux

Le fichier `bilan_structure.json` contient:
- des headers (ex: `AD` “IMMOBILISATIONS INCORPORELLES”)
- des totaux (ex: `AZ`, `BK`, `BT`, `BZ`, `CP`, `DD`, `DF`, `DP`, `DT`, `DZ`)
avec des formules.

Recommandation:
- remplir les lignes “élémentaires”
- conserver les totaux en formules Excel dans le XLSX
- pour CSV, calculer les totaux côté backend en appliquant la formule.

---

## 7) Intégration dans l’UI/UX existante

### 7.1 Emplacement produit

Ajouter un menu “Rapports” (ex: depuis `MenuOverlay`):
- “Compte de résultat (SYSCOHADA)”
- “Bilan (SYSCOHADA)”

Chaque écran:
- sélection de période (exercice)
- bouton “Générer”
- téléchargement du fichier
- section “Mapping” / “Paramétrage” (au moins pour le compte de résultat)

### 7.2 Paramétrage du mapping (MVP)

Écran “Mapping SYSCOHADA”:
- associer des catégories Akompta à des refs SYSCOHADA (TA, RG, RH, …)
- fournir des presets:
  - `income` + catégorie contient “vente” → `TA`
  - `expense` + catégorie contient “transport” → `RG`
  - `expense` + catégorie contient “loyer|eau|électricité|internet|prestataire” → `RH`
  - `expense` + catégorie contient “taxe|impôt|douane” → `RI`
  - `expense` + catégorie contient “divers|autre” → `RJ`

Résultat: 80% des utilisateurs obtiennent un CR exploitable rapidement.

---

## 8) Endpoints backend proposés (design API)

### 8.1 Génération fichiers

- `GET /api/reports/syscohada/compte-resultat/?year=2026&compare=1&format=xlsx`
  - réponse: fichier binaire (attachment)
- `GET /api/reports/syscohada/bilan/?year=2026&compare=1&format=xlsx`
  - réponse: fichier binaire (attachment)

Option: `POST` avec un body plus riche (périodes non annuelles, options, arrondis, etc.).

### 8.2 Vérification / preview (utile UX)

- `GET /api/reports/syscohada/compte-resultat/preview/?year=2026`
  - renvoie les montants par `ref` + erreurs de mapping
- `GET /api/reports/syscohada/bilan/preview/?year=2026`
  - renvoie les refs du bilan + valeurs auto + valeurs saisies + équilibre (delta)

---

## 9) Recommandation de trajectoire (phases)

### Phase 1 — Compte de résultat “mapping simple”

- Mapping catégories → refs du CR
- Export CR (XLSX/CSV)
- Warnings “non mappé”

### Phase 2 — Bilan minimal + saisie d’ouverture

- Table “soldes d’ouverture / ajustements”
- Auto: trésorerie + résultat net
- Export bilan (XLSX/CSV)
- Contrôle d’équilibre

### Phase 3 — Couche comptable (option B)

- Plan de comptes SYSCOHADA
- Écritures automatiques à partir des transactions
- Bilan/CR par agrégation de soldes
- Stock / immobilisations / créances/dettes

---

## 10) Ce que “générer seulement 2 fichiers” implique

Même si la sortie se limite à 2 exports, pour être exploitable il faut:
- des règles de mapping et/ou un plan de comptes
- des règles de période (exercice)
- des contrôles de cohérence

Le repo fournit déjà la **structure et les formules**.
Le travail d’intégration consiste surtout à:
- produire des **données comptables structurées** (même minimalement)
- remplir les cellules correspondantes dans les gabarits

