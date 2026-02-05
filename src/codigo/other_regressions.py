import importlib
import polars as pl, polars.selectors as cs
from polars import col as c
import pyfixest as pf
from codigo.costa_rica import filters_cr 
from definitions import bases, results
from codigo import display_results as dis_res
from pathlib import Path
from ucr_tools.core import data_analysis as da

#Definitions
file = bases.joinpath(r'cr\limpio\cr_region_grouped_processed.sav')
tables_path = results.joinpath('cr/regresiones_dependientes')
general_output = tables_path.joinpath('regresion_dependientes.docx')
xl_employment = tables_path.joinpath('employment.xlsx')
xl_wages = tables_path.joinpath('wages.xlsx')

df, var_labels, col_labels = da.read_file(file)
df:pl.DataFrame
dis_res.var_labels = var_labels

endogena_emp = 'Employment'
endogena_wage = 'Wages'

#--------------------------------------
# REGRESIONES PERSONAS DEPENDIENTES
#--------------------------------------
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


fixed_effects = 'region + anno'
cluster = 'region'
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

#Crear identificador de ocupacion
df_2023 = (
    df.filter(c.anno.eq(2023))
    .with_columns(
        pl.when(c.ramafuerzatrab.eq(20)).then(1) #20 Hogar 99 no se puede clasificar (se incluye con el resto)
        .when(c.ramafuerzatrab.is_null()).then(None) #NA se mantiene nulo
        .otherwise(0)
        .alias('id_trabajo_hogar'),
    )
    .filter(
        ~c.a5.is_in([98,99]), #Filtrar valores no reportados
        c.nivinst.ne(99),
        c.a6.ne(9),
        c.a4.eq(2), # Mantener mujeres
        c.nacionalidad.is_in([0,1])
    )
)

exogenas = 'nacionalidad nivinst a5 a6 id_dependientes'.split()
exogenas_formula = f'nacionalidad + C(nivinst) + a5 + pow(a5, 2) + C(a6) + id_dependientes + C(region)'
fixed_effects = f'region'
cluster = 'region'

model = pf.feols(f'id_trabajo_hogar~{exogenas_formula}', data=df_2023, vcov='hetero')
table_args = {
    'type':'gt',
    'keep':'nacionalidad',
    'fe_present':'YES', 
    'thousands_sep':True,
    }

dis_res.great_table_to_word(pf.etable(model, **table_args), tables_path.joinpath('househould_employees.docx'))


#--------------------------------------
# REGRESION FORMALIDAD COSTA RICA
#--------------------------------------
file = bases.joinpath(r'cr\limpio\cr_region_grouped_processed.sav')
df, var_labels, col_labels = da.read_file(file, output_format='polars')
df_2023 = df.filter(c.anno.eq(2023))
df = (
    df
    .with_columns(
        pl.when(c.ramaemppri.is_in([9,7,20,3])).then('ramaemppri')
        .when(c.ramaemppri.is_null() | c.ramaemppri.eq(99)).then(None)
        .otherwise(-1)
        .alias('rama_2')
    )
)

asegurados_list = [1, 8, 9, 12, 14]
df_2023 = df_2023.with_columns(
    pl.when(c.a11.is_in(asegurados_list))
    .then(0)
    .when(c.a11.eq(99) | c.a11.is_null())
    .then(None)
    .otherwise(1)
    .alias('informal_flag')
    )

#Filters
nacionalidad = c.nacionalidad.is_in([0,1])
educacion = c.nivinst.ne(99)
edad = ~c.a5.is_in([98,99]) #Filtrar valores no reportados
estado_civil = c.a6.ne(9) #a6 estado conyugal
sexo = c.a4.eq(2), # Mantener mujeres
rama = c.ramaemppri.ne(99)
activos = c.condact.eq(1)
# wage_earners = c.posiemppri.is_in([11,12])

df_2023 = df_2023.filter(nacionalidad, educacion, edad, estado_civil, sexo, rama, activos)
df_2023 = df_2023.with_columns(c.a5.pow(2).alias('edad2'))

#Hacerlo mas bien con una lista
exogenas = 'nacionalidad nivinst a5 a6 id_dependientes ramaemppri region'.split()
exogenas_formula = 'nacionalidad + C(nivinst) + a5 + pow(a5,2) + C(a6) + C(region) + id_dependientes + C(ramaemppri)'
# exogenas_formula = 'nacionalidad + nivinst + a5 + edad2 + a6 + region + id_dependientes + ramaemppri'
endogena = 'informal_flag'


csw_model = ','.join(exogenas_formula.split('+'))
controls = [
    "nacionalidad",
    "C(nivinst)",
    "a5",
    "edad2",          # better than pow(a5,2) in statsmodels
    "C(a6)",
    "C(region)",
    "id_dependientes",
    "C(ramaemppri)"
]

model = pf.feols(f'{endogena}~csw({controls})', data=df_2023, vcov='hetero')
model = pf.feols(f'{endogena}~{exogenas_formula}', data=df_2023, vcov='hetero')
tables_path = results.joinpath('cr/other_regressions')
dis_res.great_table_to_word(pf.etable(model, **table_args), tables_path.joinpath('formalidad_cr.docx'))



#--------------------------------------
# REGRESION FORMALIDAD CHILE
#--------------------------------------
file = bases.joinpath(r'chile\limpio\chile_region_processed.sav')
df, var_labels, col_labels = da.read_file(file, output_format='polars')

df_2022 = df.filter(c.anno.eq(2022))

#Filters
educacion = c.educ.is_between(0,12)
nacionalidad = c.nacionalidad.is_in([0,1])
edad = c.edad.is_between(15,65, closed='both')
estado_civil = c.ecivil.is_between(1,8)
rama = c.rama1.is_between(1,21)
activos = c.activ.eq(1)
sexo = c.sexo.eq(2)
cotiza = c.cotiza.is_in([0,1])

df_2022 = df_2022.filter(sexo, educacion, nacionalidad, edad, estado_civil, rama, activos, cotiza)
df_2022 = df_2022.with_columns(c.cotiza.replace({0:1, 1:0}))

exogenas = 'nacionalidad educ edad ecivil id_dependientes rama1'
exogenas_formula = 'nacionalidad + C(educ) + edad + pow(edad, 2) + C(ecivil) + C(rama1) + id_dependientes + C(region)'
endogena = 'cotiza'

model = pf.feols(f'{endogena}~{exogenas_formula}', data=df_2022, vcov='hetero')

tables_path = results.joinpath('chile/other_regressions')
dis_res.great_table_to_word(pf.etable(model, **table_args), tables_path.joinpath('formalidad_chile.docx'))



#--------------------------------------
# REGRESION OCUPACIONES - CHILE
#--------------------------------------
file = bases.joinpath('chile/limpio/chile_region_processed.sav')
df, var_labels, col_labels = da.read_file(file)
da.var_labels=var_labels
from codigo.chile import filters_chile
import importlib
importlib.reload(filters_chile)
admin, elementary = [1,2,3,4], [9]
filters = (
    c.oficio1_08.is_between(1,9) #0 no porque es de las fuerzas armadas
)
df=df.with_columns(
    pl.when(c.oficio1_08.is_in(admin)).then(1)
    .when(c.oficio1_08.is_in(elementary)).then(0)
    .otherwise(None)
    .alias('recode_ocupacion')
    )

temp_df=df.filter(filters, filters_chile.wage_filters())
fixed_effects='anno+habilidad'
cluster='habilidad'
ocupations = {1:'Admin', 0:'Elementary'}
outputs={}
print(f'DataBase -> {file.name}')
for i in [1,0]:
    print(f'\nRunning regressions \nGroup -> {ocupations.get(i)}')
    reg_df = temp_df.filter(c.recode_ocupacion.eq(i))
    outputs[ocupations.get(i)] = pf.feols(f'w_real_log ~ {filters_chile.exogenas} | {fixed_effects}', data=reg_df, vcov={'CRV1': cluster})
    print(f'\nDone!\n{"*"*20}')

dis_res.great_table_to_word(pf.etable(outputs.values(), model_heads=['Admin', 'Elementary'], **dis_res.table_args), output_path=results.joinpath('chile/regresiones_ocupaciones.docx'))

