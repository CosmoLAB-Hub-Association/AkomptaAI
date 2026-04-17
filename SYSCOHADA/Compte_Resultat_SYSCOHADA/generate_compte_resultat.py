import pandas as pd
import json

# Charger la structure
with open('compte_resultat_structure.json', 'r') as f:
    structure = json.load(f)

# Préparation des données pour le DataFrame
data = []
for item in structure['lignes']:
    row = {
        "REF": item['ref'],
        "LIBELLES": item['libelle'],
        "NUMERO DE COMPTES": item.get('compte', ''),
        "MONTANT_N": 0,
        "MONTANT_N_1": 0
    }
    data.append(row)

df = pd.DataFrame(data)

# Export Excel avec xlsxwriter
with pd.ExcelWriter('Compte_Resultat_SYSCOHADA.xlsx', engine='xlsxwriter') as writer:
    df.to_excel(writer, sheet_name='COMPTE_RESULTAT', index=False)
    
    workbook = writer.book
    sheet = writer.sheets['COMPTE_RESULTAT']
    
    # Formats
    header_format = workbook.add_format({'bold': True, 'bg_color': '#4472C4', 'font_color': 'white', 'border': 1})
    total_format = workbook.add_format({'bold': True, 'border': 1})
    
    # Dictionnaire pour mapper les REF aux numéros de ligne Excel (1-indexed)
    ref_to_row = {item['ref']: i + 2 for i, item in enumerate(structure['lignes'])}
    
    # Appliquer les formats et les formules
    for i, item in enumerate(structure['lignes']):
        row_idx = i + 1 # 0-indexed for set_row
        
        if item.get('is_total'):
            # Créer un format spécifique pour cette ligne de total
            fmt = workbook.add_format({'bold': True, 'bg_color': item.get('bg_color', '#FFFFFF'), 'border': 1})
            sheet.set_row(row_idx, None, fmt)
            
            # Construire la formule Excel basée sur les REF
            formula_n = item['formula']
            formula_n_1 = item['formula']
            
            # Remplacer les REF par les adresses de cellules (D pour N, E pour N-1)
            # On trie par longueur décroissante pour éviter de remplacer "XA" dans "XAA" par erreur
            sorted_refs = sorted(ref_to_row.keys(), key=len, reverse=True)
            for ref in sorted_refs:
                formula_n = formula_n.replace(ref, f'D{ref_to_row[ref]}')
                formula_n_1 = formula_n_1.replace(ref, f'E{ref_to_row[ref]}')
            
            sheet.write_formula(row_idx, 3, f'={formula_n}')
            sheet.write_formula(row_idx, 4, f'={formula_n_1}')
        else:
            # Ligne normale
            pass

    # Ajuster la largeur des colonnes
    sheet.set_column('A:A', 10)
    sheet.set_column('B:B', 60)
    sheet.set_column('C:C', 25)
    sheet.set_column('D:E', 15)

# Export CSV
df.to_csv('Compte_Resultat_SYSCOHADA.csv', index=False)
