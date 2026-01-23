import polars as pl, polars.selectors as cs
from polars import col as c
import pyreadstat
from definitions import bases
from codigo.reviewers.set_up import Vars
import seaborn as sns
sns.set_theme('paper')

def sum_var(df:pl.DataFrame):
    return df.describe().style.fmt_number(decimals=2, columns=cs.numeric())

def obs_lost(df1:pl.DataFrame, df2:pl.DataFrame):
    return df1.__len__() - df2.__len__()

#Country Set Up
path_cr = bases.joinpath('cr/limpio/cr_region_grouped_processed.sav')
path_chile = bases.joinpath('chile/limpio/chile_region_processed.sav')
vars_dict = {
    'cr': ['w_real', 'hortotnorm', path_cr],
    'chile': ['w_real', 'o10', path_chile]
}

country = 'chile'
vars = Vars(*vars_dict.get(country))

df, meta = pyreadstat.read_sav(vars.path, output_format='polars')
var_labels = meta.variable_value_labels
col_labels = meta.column_names_to_labels
df:pl.DataFrame

#-----------------------------
#COSTA RICA
#-----------------------------
from codigo.costa_rica.regressions import reg_df_emp, reg_df_wage
cols_exogenas = 'p p_bajo p_alto a6'.split()
filter_exogenas = ( # Get observations with no null values for all regressors
        pl.all_horizontal(c(cols_exogenas).is_not_null()) #|
        # c.habilidad.is_in([df['habilidad'].min(),df['habilidad'].max()])
    )

reg_df_emp.select(c.exp.ge(40).sum())
sum_var(reg_df_emp['exp'])

filter_hours = c(vars.work_hours).is_between(0, 72, closed='none')
reg_df_emp.filter(filter_exogenas, c(vars.work_hours).ne(999) | c(vars.work_hours).is_null()).shape #filter_hours | c(vars.work_hours).is_null() | c(vars.work_hours).eq(0)
#!!! 523 menos cuando se aplica filtro de horas en regresion de empleo

sum_var(reg_df_wage.filter(c(vars.work_hours).is_between(0, 999, closed='none'), c(vars.hourly_income).is_not_null(), filter_exogenas)['w_real'])
sum_var(reg_df_wage.filter(c(vars.work_hours).is_between(0, 72, closed='none'), c(vars.hourly_income).is_between(0,40_000, closed='none'), filter_exogenas)['w_real'])
#!!! 343 menos con las los filtros de hora en regresion de salarios
#!!! 4 menos con el filtro de salario



#--------------------------------------
# CHILE
#--------------------------------------
from codigo.chile.regressions import reg_df_emp, reg_df_wage

cols_exogenas = 'p p_bajo p_alto ecivil'.split()
filter_exogenas = (
        pl.all_horizontal(c(cols_exogenas).is_not_null()), #|
        # c.habilidad.is_in([df['habilidad'].min(),df['habilidad'].max()])
        c.ecivil.is_between(1,8, closed='both'),
    )

#Regresión de empleo
reg_df_emp = reg_df_emp.filter(filter_exogenas)
reg_df_emp = reg_df_emp.filter(c(vars.work_hours).is_between(0,120, closed='both') | c(vars.work_hours).is_null())
exp_filtered = reg_df_emp.filter(c.exp.lt(40))
obs_lost(exp_filtered, reg_df_emp)
#51268 se filtran con la exp
hours_filtered = exp_filtered.filter(c(vars.work_hours).is_between(0,72, closed='left') | c(vars.work_hours).is_null())
obs_lost(hours_filtered,  exp_filtered)
#1434 se filtran con horas de trabajo
hours_filtered.shape

#Regresión de salario
back_up = reg_df_wage.clone()
reg_df_wage = reg_df_wage.filter(filter_exogenas)
reg_df_wage = reg_df_wage.filter(c(vars.work_hours).is_between(0,120, closed='right'))
exp_filtered = reg_df_wage.filter(c.exp.lt(40))
obs_lost(exp_filtered, reg_df_wage)
#-9681 se filtran con la exp
hours_filtered = exp_filtered.filter(c(vars.work_hours).is_between(0,72, closed='none'))
obs_lost(hours_filtered, exp_filtered)
#-672 se filtran con las horas
#Filtro para salarios a mas de 4 desviaciones estandar
test_df = hours_filtered.filter((w:=c.w_real).is_between(w.mean()-4*w.std(), w.mean()+4*w.std(), closed='both'))
obs_lost(test_df, hours_filtered)
#-518 se filtran con salarios atipicos

