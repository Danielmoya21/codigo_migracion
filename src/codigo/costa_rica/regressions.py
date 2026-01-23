import polars as pl
from polars import col as c
import pyreadstat
from codigo import display_results as dis_res
import argparse
from definitions import bases

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--var', type=str, default='region')
parser.add_argument('--sexo', type=int, default=2) #1 men #2 women
args = parser.parse_known_args()[0]

#--------------------------------------
group_skills = input('Do you want to group skills? y/n\n>')
skill_gp = '_grouped' if group_skills=='y' else ''

group_regions = input('Do you want to group regions? y/n\n>')
region_gp = '_v2' if group_regions=='y' else ''

db_name = bases.joinpath(f'cr/limpio/cr_{args.var}{region_gp}{skill_gp}_processed.sav')
df, meta = pyreadstat.read_sav(db_name, output_format='polars')
print(f'Loaded {db_name.name}')
var_labels = meta.variable_value_labels
col_labels = meta.column_names_to_labels
df:pl.DataFrame

if group_skills=='y':
    var_labels['habilidad'].update({3:'P Inc', 4:'P Comp'}) #Change habilidad labels if grouping
    
dis_res.var_labels=var_labels


#Scale proportions
df = df.with_columns(c('p p_bajo p_alto'.split()).mul(10))

#--------------------------------------
# EMPLOYMENT FILTERS
#--------------------------------------
employment_filters = (
    c.nacionalidad.eq(1),
    c.a4.eq(args.sexo),
    # c.exp.lt(40),
    # c.hortotnorm.is_null() | c.hortotnorm.is_between(0,72, closed='left')
    )

#--------------------------------------
# MODEL SPECIFICATION - EMPLOYMENT
#--------------------------------------
exogenas = 'p + p_bajo + p_alto + C(a6)'
cols_exogenas = 'p p_bajo p_alto a6'.split()
categoricals = 'a6' # Exogenous variables classified as categorical

filter_exogenas = ( # Get observations with no null values for all regressors
        pl.all_horizontal(c(cols_exogenas).is_not_null()) |
        c.habilidad.is_in([df['habilidad'].min(),df['habilidad'].max()])
    )

reg_df_emp = (  # Generate df for employment regression
    df
    .filter(
        employment_filters,
        filter_exogenas
    )
    .with_columns(
        c.condact.replace({2:0, 3:0}),
        )
    .rename({'condact':'Employment'})
    )
endogena_emp = 'Employment'

#--------------------------------------
# WAGE FILTERS
#--------------------------------------
wage_filters = (
    c.posiemppri.is_in([11,12]), #Keep wage earners
    c.nacionalidad.eq(1), #Keep natives
    c.a4.eq(args.sexo), #keep men/women
    c.exp.lt(40),
    c.condact.eq(1),
    # c.hortotnorm.is_between(0,999,closed='none'),
    # c.w_real.gt(0)
    c.hortotnorm.is_between(0,72, closed='none'),
    c.w_real.is_between(0,40_000, closed='none'),
    )

#--------------------------------------
# MODEL SPECIFICATION - WAGES
#--------------------------------------
endogena_wage = 'Wages'
reg_df_wage = (
    df
    .filter(
        wage_filters,
        filter_exogenas
    )
    .rename({'w_real_log':'Wages'})
    )

