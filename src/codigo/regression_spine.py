import polars as pl
from polars import col as c
import pyfixest as pf
from datetime import datetime
import pandas as pd
import argparse
from codigo import display_results as dis_res
from definitions import root

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--pais', type=str, default='cr')
args = parser.parse_known_args()[0]

if args.pais=='cr':
    from codigo.costa_rica import regressions as pais
else:
    from codigo.chile import regressions as pais

outputs_folder = root.joinpath(f'results/{args.pais}')
vif_file = outputs_folder.joinpath('VIF_results.txt') #VIF results
cross_tab_employment = outputs_folder.joinpath('cross_tab_employment.xlsx')
cross_tab_wage = outputs_folder.joinpath('cross_tab_wage.xlsx')
cross_tab_employment.unlink(missing_ok=True)
cross_tab_wage.unlink(missing_ok=True)

if not vif_file.exists():
    vif_file.touch()

#--------------------------------------
# MODEL
#--------------------------------------
fixed_effects = f'anno + {pais.args.var}' #Modify fix effects if needed
cluster = pais.args.var
skill_groups = {
    'high_skill': {'range':(7,10), 'closed':'left'},
    'low_skill': {'range':(pais.df['habilidad'].min(),6), 'closed':'right'},
}
txt_vifs = '' #Store vif results for all regressions

#--------------------------------------
# RUN REGRESSIONS LOOP
#--------------------------------------
general_results={}
skill_resulsts={}
for df, endogena in zip([pais.reg_df_emp, pais.reg_df_wage], [pais.endogena_emp, pais.endogena_wage]):
    print(f'running regressions for {endogena}')
    #Regresion General
    general_results[f'{endogena}_general'] = pf.feols(f'{endogena} ~ {pais.exogenas} | {fixed_effects}', data=df, vcov={'CRV1': cluster})
    vif = dis_res.compute_vif(df, pais.cols_exogenas, cat=pais.categoricals)
    txt_vifs += dis_res.write_df_txt(vif, f'general_{endogena}')
    counter=1
    #Loop - Regresiones por grupos de habilidad
    for label, confg in skill_groups.items():
        print(counter)
        subset = df.filter(c.habilidad.is_between(*confg['range'], closed=confg['closed']))
        
        skill_resulsts[f'{endogena}_fit{counter}'] = pf.feols(f'{endogena} ~ {pais.exogenas} | {fixed_effects}', data=subset, vcov={'CRV1': cluster})
        vif = dis_res.compute_vif(subset, pais.cols_exogenas, cat=pais.categoricals)
        txt_vifs += dis_res.write_df_txt(vif, f'{endogena} - {label}')
        counter+=1
    
#--------------------------------------
# RESULTS TABLE
#--------------------------------------
with vif_file.open('wt') as f:
    f.write(txt_vifs)
results = pf.etable([*skill_resulsts.values()], model_heads=['High Skill', 'Low Skill', 'High Skill', 'Low Skill'], **dis_res.table_args)
dis_res.great_table_to_word(results, output_path=outputs_folder.joinpath('results_skill.docx'))
results = pf.etable([*general_results.values()], **dis_res.table_args)
dis_res.great_table_to_word(results, output_path=outputs_folder.joinpath('results_general.docx'))

#Crosstabs with observations per cell
for df, path in zip([pais.reg_df_emp, pais.reg_df_wage], [cross_tab_employment, cross_tab_wage]):
    path.unlink(missing_ok=True)
    dis_res.create_xl_wb(path)
    row=1
    with pd.ExcelWriter(path, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
        #Create a table for each year
        for year, gp_df in df.sort('anno').group_by('anno', maintain_order=True):
            year=year[0]
            
            gp_df = gp_df.to_pandas().reset_index()
            gp_df = dis_res.cross_tab(gp_df, ['habilidad', pais.args.var], args={'dropna':False})
            (
                dis_res.fmt_low_people_cells(gp_df)
                .to_excel(writer, sheet_name='years', startrow=row, index=False)
            )
            writer.book['years'].cell(row, column=1, value=year)
            row += gp_df.shape[0] + 3
        #All years combined
        df = df.to_pandas()
        df = dis_res.cross_tab(df, ['habilidad', pais.args.var], args={'dropna':False})
        (
        dis_res.fmt_low_people_cells(df)
        .to_excel(writer, sheet_name='allyears', index=False)
        )

sex_dict = {1:'Hombres', 2:'Mujeres'}
print(f'\nCountry -> {args.pais}\nGroups variable -> {pais.args.var}\nSex -> {sex_dict.get(pais.args.sexo)} \n\nFixed effects: {fixed_effects} \nClusters: {cluster} \n\nResults are available in {outputs_folder.as_posix()}')
print(datetime.now(),'\n')
