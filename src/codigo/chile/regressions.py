import polars as pl
from polars import col as c
import pyreadstat
from codigo import display_results as dis_res
from definitions import bases
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--var', type=str, default='region')
parser.add_argument('--sexo', type=int, default=2) #1 men #2 women
args = parser.parse_known_args()[0]

#--------------------------------------
grouping = input('Do you want to group skills? y/n\n>')
group_txt = '_grouped' if grouping=='y' else ''
db_name = bases.joinpath(f'chile/limpio/chile_{args.var}{group_txt}_processed.sav')
df, meta = pyreadstat.read_sav(db_name, output_format='polars')
print(f'Loaded {db_name.name}')
var_labels = meta.variable_value_labels
col_labels = meta.column_names_to_labels
df:pl.DataFrame
dis_res.var_labels=var_labels

if grouping=='y':
    var_labels['habilidad'].update({2:'P Inc'}) #Change habilidad labels if grouping

#Scale proportions
df = df.with_columns(c('p p_bajo p_alto'.split()).mul(10))

#--------------------------------------
# EMPLOYMENT FILTERS
#--------------------------------------
employment_filters = (
    c.nacionalidad.eq(1),   #Chilenos
    c.sexo.eq(args.sexo),   #Mujeres
    c.ecivil.is_between(1,8, closed='both'),
    # c.o10.is_null() | c.o10.is_between(0,72, closed='left'),   #eliminar horas atipicas
    # c.exp.lt(40),
    )
#--------------------------------------
# MODEL SPECIFICATION - EMPLOYMENT
#--------------------------------------
exogenas = 'p + p_bajo + p_alto + C(ecivil)'
cols_exogenas = 'p p_bajo p_alto ecivil'.split()
categoricals = 'ecivil'

filter_exogenas = (
        pl.all_horizontal(c(cols_exogenas).is_not_null()) |
        c.habilidad.is_in([df['habilidad'].min(),df['habilidad'].max()])
    )

reg_df_emp = (
    df
    .filter(employment_filters, filter_exogenas)
    .with_columns(
        c.activ.replace({2:0, 3:0}),
        )
    .rename({'activ':'Employment'})
    )
endogena_emp = 'Employment'

#--------------------------------------
# WAGE FILTERS
#--------------------------------------
wage_filters = (
    c.nacionalidad.eq(1),
    c.sexo.eq(args.sexo),
    c.activ.eq(1),
    c.asal.eq(1), #Keep wage earners
    c.ecivil.is_between(1,8, closed='both'),
    c.exp.lt(40),
    c.o10.is_between(0,72, closed='none'),
    # c.o10.is_between(0,120, closed='right'),
    c.w_real.gt(0), #Additioanl filter for deviations added below
    )
#--------------------------------------
# MODEL SPECIFICATION - WAGES
#--------------------------------------
endogena_wage = 'Wages'
reg_df_wage = (
    df
    .filter(wage_filters, filter_exogenas)
    .filter((w:=c.w_real).is_between(w.mean()-4*w.std(), w.mean()+4*w.std(), closed='both'))
    .rename({'w_real_log':'Wages'})
    )

