import pandas as pd
import json

# Charger la structure
with open('bilan_structure.json', 'r') as f:
    structure = json.load(f)

# Création du DataFrame pour l'Actif
actif_data = []
for item in structure['actif']:
    row = {
        "REF": item['ref'],
        "ACTIF": item['libelle'],
        "Note": item['note'],
        "BRUT": 0,
        "AMORT/DEPREC": 0,
        "NET_N": 0,
        "NET_N_1": 0
    }
    actif_data.append(row)

df_actif = pd.DataFrame(actif_data)

# Création du DataFrame pour le Passif
passif_data = []
for item in structure['passif']:
    row = {
        "REF": item['ref'],
        "PASSIF": item['libelle'],
        "Note": item['note'],
        "NET_N": 0,
        "NET_N_1": 0
    }
    passif_data.append(row)

df_passif = pd.DataFrame(passif_data)

# Export Excel avec xlsxwriter pour les formules
with pd.ExcelWriter('Bilan_SYSCOHADA_Complet.xlsx', engine='xlsxwriter') as writer:
    df_actif.to_excel(writer, sheet_name='ACTIF', index=False)
    df_passif.to_excel(writer, sheet_name='PASSIF', index=False)
    
    workbook = writer.book
    sheet_actif = writer.sheets['ACTIF']
    sheet_passif = writer.sheets['PASSIF']
    
    # Formats
    header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1})
    total_format = workbook.add_format({'bold': True, 'bg_color': '#F2F2F2', 'border': 1})
    
    # Appliquer les formules pour l'Actif (Colonnes: A=REF, B=ACTIF, C=Note, D=BRUT, E=AMORT, F=NET_N, G=NET_N_1)
    # Ligne 1 est le header (index 0), donc les données commencent à la ligne 2 (index 1)
    for i, item in enumerate(structure['actif']):
        row_idx = i + 1
        # NET_N = BRUT - AMORT
        sheet_actif.write_formula(row_idx, 5, f'=D{row_idx+1}-E{row_idx+1}')
        
        if item.get('is_total'):
            sheet_actif.set_row(row_idx, None, total_format)
            if item['ref'] == 'AZ': # TOTAL ACTIF IMMOBILISE = AD + AI + AQ
                # Trouver les indices des lignes AD, AI, AQ
                ad_idx = next(idx for idx, x in enumerate(structure['actif']) if x['ref'] == 'AD') + 2
                ai_idx = next(idx for idx, x in enumerate(structure['actif']) if x['ref'] == 'AI') + 2
                aq_idx = next(idx for idx, x in enumerate(structure['actif']) if x['ref'] == 'AQ') + 2
                sheet_actif.write_formula(row_idx, 3, f'=D{ad_idx}+D{ai_idx}+D{aq_idx}')
                sheet_actif.write_formula(row_idx, 4, f'=E{ad_idx}+E{ai_idx}+E{aq_idx}')
                sheet_actif.write_formula(row_idx, 6, f'=G{ad_idx}+G{ai_idx}+G{aq_idx}')
            elif item['ref'] == 'BK': # TOTAL ACTIF CIRCULANT = BA + BB + BG
                ba_idx = next(idx for idx, x in enumerate(structure['actif']) if x['ref'] == 'BA') + 2
                bb_idx = next(idx for idx, x in enumerate(structure['actif']) if x['ref'] == 'BB') + 2
                bg_idx = next(idx for idx, x in enumerate(structure['actif']) if x['ref'] == 'BG') + 2
                sheet_actif.write_formula(row_idx, 3, f'=D{ba_idx}+D{bb_idx}+D{bg_idx}')
                sheet_actif.write_formula(row_idx, 4, f'=E{ba_idx}+E{bb_idx}+E{bg_idx}')
                sheet_actif.write_formula(row_idx, 6, f'=G{ba_idx}+G{bb_idx}+G{bg_idx}')
            elif item['ref'] == 'BT': # TOTAL TRESORERIE-ACTIF = BQ + BR + BS
                bq_idx = next(idx for idx, x in enumerate(structure['actif']) if x['ref'] == 'BQ') + 2
                br_idx = next(idx for idx, x in enumerate(structure['actif']) if x['ref'] == 'BR') + 2
                bs_idx = next(idx for idx, x in enumerate(structure['actif']) if x['ref'] == 'BS') + 2
                sheet_actif.write_formula(row_idx, 3, f'=D{bq_idx}+D{br_idx}+D{bs_idx}')
                sheet_actif.write_formula(row_idx, 4, f'=E{bq_idx}+E{br_idx}+E{bs_idx}')
                sheet_actif.write_formula(row_idx, 6, f'=G{bq_idx}+G{br_idx}+G{bs_idx}')
            elif item['ref'] == 'BZ': # TOTAL GENERAL = AZ + BK + BT + BU
                az_idx = next(idx for idx, x in enumerate(structure['actif']) if x['ref'] == 'AZ') + 2
                bk_idx = next(idx for idx, x in enumerate(structure['actif']) if x['ref'] == 'BK') + 2
                bt_idx = next(idx for idx, x in enumerate(structure['actif']) if x['ref'] == 'BT') + 2
                bu_idx = next(idx for idx, x in enumerate(structure['actif']) if x['ref'] == 'BU') + 2
                sheet_actif.write_formula(row_idx, 3, f'=D{az_idx}+D{bk_idx}+D{bt_idx}+D{bu_idx}')
                sheet_actif.write_formula(row_idx, 4, f'=E{az_idx}+E{bk_idx}+E{bt_idx}+E{bu_idx}')
                sheet_actif.write_formula(row_idx, 6, f'=G{az_idx}+G{bk_idx}+G{bt_idx}+G{bu_idx}')
        
        # Sommes intermédiaires pour les headers (AD, AI, AQ, BG)
        if item.get('is_header'):
            sheet_actif.set_row(row_idx, None, workbook.add_format({'italic': True, 'bold': True}))
            if item['ref'] == 'AD': # IMMOB. INCORPORELLES = AE to AH
                sheet_actif.write_formula(row_idx, 3, '=SUM(D3:D6)')
                sheet_actif.write_formula(row_idx, 4, '=SUM(E3:E6)')
                sheet_actif.write_formula(row_idx, 6, '=SUM(G3:G6)')
            elif item['ref'] == 'AI': # IMMOB. CORPORELLES = AJ to AP
                sheet_actif.write_formula(row_idx, 3, '=SUM(D8:D13)')
                sheet_actif.write_formula(row_idx, 4, '=SUM(E8:E13)')
                sheet_actif.write_formula(row_idx, 6, '=SUM(G8:G13)')
            elif item['ref'] == 'AQ': # IMMOB. FINANCIERES = AR to AS
                sheet_actif.write_formula(row_idx, 3, '=SUM(D15:D16)')
                sheet_actif.write_formula(row_idx, 4, '=SUM(E15:E16)')
                sheet_actif.write_formula(row_idx, 6, '=SUM(G15:G16)')
            elif item['ref'] == 'BG': # CREANCES = BH to BJ
                sheet_actif.write_formula(row_idx, 3, '=SUM(D20:D22)')
                sheet_actif.write_formula(row_idx, 4, '=SUM(E20:E22)')
                sheet_actif.write_formula(row_idx, 6, '=SUM(G20:G22)')

    # Appliquer les formules pour le Passif (A=REF, B=PASSIF, C=Note, D=NET_N, E=NET_N_1)
    for i, item in enumerate(structure['passif']):
        row_idx = i + 1
        if item.get('is_total'):
            sheet_passif.set_row(row_idx, None, total_format)
            if item['ref'] == 'CP': # TOTAL CAPITAUX PROPRES = CA - CB + CD + CE + CF + CG + CH + CJ + CL + CM
                sheet_passif.write_formula(row_idx, 3, '=D2-D3+D4+D5+D6+D7+D8+D9+D10+D11')
                sheet_passif.write_formula(row_idx, 4, '=E2-E3+E4+E5+E6+E7+E8+E9+E10+E11')
            elif item['ref'] == 'DD': # TOTAL DETTES FINANCIERES = DA + DB + DC
                sheet_passif.write_formula(row_idx, 3, '=SUM(D13:D15)')
                sheet_passif.write_formula(row_idx, 4, '=SUM(E13:E15)')
            elif item['ref'] == 'DF': # TOTAL RESSOURCES STABLES = CP + DD
                cp_idx = next(idx for idx, x in enumerate(structure['passif']) if x['ref'] == 'CP') + 2
                dd_idx = next(idx for idx, x in enumerate(structure['passif']) if x['ref'] == 'DD') + 2
                sheet_passif.write_formula(row_idx, 3, f'=D{cp_idx}+D{dd_idx}')
                sheet_passif.write_formula(row_idx, 4, f'=E{cp_idx}+E{dd_idx}')
            elif item['ref'] == 'DP': # TOTAL PASSIF CIRCULANT = DH to DN
                sheet_passif.write_formula(row_idx, 3, '=SUM(D18:D23)')
                sheet_passif.write_formula(row_idx, 4, '=SUM(E18:E23)')
            elif item['ref'] == 'DT': # TOTAL TRESORERIE-PASSIF = DQ + DR
                sheet_passif.write_formula(row_idx, 3, '=SUM(D25:D26)')
                sheet_passif.write_formula(row_idx, 4, '=SUM(E25:E26)')
            elif item['ref'] == 'DZ': # TOTAL GENERAL = DF + DP + DT + DV
                df_idx = next(idx for idx, x in enumerate(structure['passif']) if x['ref'] == 'DF') + 2
                dp_idx = next(idx for idx, x in enumerate(structure['passif']) if x['ref'] == 'DP') + 2
                dt_idx = next(idx for idx, x in enumerate(structure['passif']) if x['ref'] == 'DT') + 2
                dv_idx = next(idx for idx, x in enumerate(structure['passif']) if x['ref'] == 'DV') + 2
                sheet_passif.write_formula(row_idx, 3, f'=D{df_idx}+D{dp_idx}+D{dt_idx}+D{dv_idx}')
                sheet_passif.write_formula(row_idx, 4, f'=E{df_idx}+E{dp_idx}+E{dt_idx}+E{dv_idx}')

# Export CSV (un pour Actif, un pour Passif)
df_actif.to_csv('Bilan_ACTIF_SYSCOHADA.csv', index=False)
df_passif.to_csv('Bilan_PASSIF_SYSCOHADA.csv', index=False)
