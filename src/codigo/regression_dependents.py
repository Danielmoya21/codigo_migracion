import polars as pl, polars.selectors as cs
from polars import col as c
import pyfixest as pf
from codigo.costa_rica import filters_cr 
from definitions import bases, results
from codigo import display_results as dis_res
from ucr_tools.core import data_analysis as da

#Definitions
file = bases.joinpath(r'cr\limpio\cr_region_processed.sav')
tables_path = results.joinpath('cr/regresiones_dependientes')
general_output = tables_path.joinpath('regresion_dependientes.docx')
xl_employment = tables_path.joinpath('employment.xlsx')
xl_wages = tables_path.joinpath('wages.xlsx')

df, var_labels, col_labels = da.read_sav(file)
df:pl.DataFrame
dis_res.var_labels = var_labels

endogena_emp = 'Employment'
endogena_wage = 'Wages'

min_skill = 1
#Empleo
reg_df_emp = (
    df
    .filter(filters_cr.employment_filters(), filters_cr.filter_exogenas(min_skill=min_skill))
    .with_columns(
        c.condact.replace({2:0, 3:0}),
        )
    .rename({'condact':endogena_emp})
    ).clone()

#Salario
reg_df_wage = (
    df
    .filter(filters_cr.wage_filters(), filters_cr.filter_exogenas(min_skill=min_skill))
    .rename({'w_real_log':endogena_wage})
    ).clone()

#Diccionario de variable dependiente y dataframe
dfs = {
    endogena_emp:reg_df_emp,
    endogena_wage:reg_df_wage
}


fixed_effects = 'habilidad + anno'
cluster='habilidad'
results={}
dependents = {
    0:'No_Dependents',
    1:'Dependents'
}

print(f'DataBase -> {file.name}')
for var, _df in dfs.items():
    for i in [1,0]:
        print(f'\nRunning regressions\nVariable -> {var}\nGroup -> {dependents.get(i)}')
        reg_df = _df.filter(c.id_dependientes.eq(i))
        results[f'{var}_{dependents.get(i)}'] = pf.feols(f'{var} ~ {filters_cr.exogenas} | {fixed_effects}', data=reg_df, vcov={'CRV1': cluster})
        print(f'\nDone!\n{"*"*20}')

dis_res.generate_observations_tables([reg_df_emp, reg_df_wage], [xl_employment, xl_wages])
dis_res.great_table_to_word(pf.etable(results.values(), model_heads=['Dependents', 'Non Dependents', 'Dependents', 'Non Dependents'], **dis_res.table_args), output_path=general_output)

print(f'Files are avialable in {tables_path}')
print(f'Fixed Effects -> {fixed_effects}')
print(f'Exogenas -> {filters_cr.exogenas}')

#--------------------------------------
# REGRESION PROBABILIDAD DE TRABAJAR PARA UN HOGAR
# COSTARRICENSES VS NICARAGUENSES
#--------------------------------------

