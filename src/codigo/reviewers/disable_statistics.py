from numpy import var
from statsmodels.stats.weightstats import DescrStatsW as ws
from ucr_tools.core import data_analysis as da
import polars as pl, polars.selectors as cs
from polars import col as c
from pathlib import Path
from codigo import transformations as trans
from ucr_tools.core import data_analysis as da
import os
from definitions import bases

#------------------------------
# Load files
#------------------------------
file_path = Path(r"C:\Users\dmoya\OneDrive\Desktop\UCR\bases_de_datos\ECE\III_trimestre\III Trimestre 2023.sav")
path_results = Path(__file__).parent.joinpath('results')

df, var_labels, col_labels = da.read_file(file_path, output_format='polars')
df:pl.DataFrame
da.var_labels = var_labels

#------------------------------
# Filters
#------------------------------
edad = c.edad.is_between(15,65, closed='both')
asalariado = c.posicion_empleo.eq(1)
c.posiemppri.is_in([11,12]) #ENAHO
nacionalidad = c.pais_nacimiento.is_in([1, 4])   #1: Costa RIca,  4: Nicaragua  #ECE
w_real_outliers = c.ingreso_bruto_total_trabajo_hora.gt(0)
sexo = c.sexo.eq(2)
logro = c.logro.is_not_null()

#------------------------------
# Logro academico
#------------------------------
recode_dict = {0: 1, 6: 5, 9: None}
df = trans.add_logro(df, 'nivel_educativo', recode_dict=recode_dict)

#------------------------------
# real_wages
#------------------------------
# ipc_values = {
#     2015: 93.00390934,
#     2016: 93.44616814,
#     2017: 94.53304812,
#     2018: 96.50343843,
#     2019: 99.29164281,
#     2022: 112.0987,
#     2023: 109.537132,
# }
# df = trans.add_real_wages(df, 'ingreso_bruto_total_trabajo_hora', ipc_values=ipc_values)


#------------------------------
# Tables
#------------------------------
# Weighted mean salary
group_cols = ['pais_nacimiento', 'logro']
group_cols = ['nacionalidad', 'logro'] #ENAHO
summary = (
    df
    .filter(
        edad, sexo, logro, asalariado, nacionalidad, w_real_outliers
    )
    .group_by(
        *group_cols
    )
    .map_groups(
        lambda gp:
        gp.select(
            c(group_cols).first(),
            w_promedio=pl.lit((stat:=da.w_stat(gp, col='ingreso_bruto_total_trabajo_hora', factor='factor')).mean),
            N=pl.lit(stat.nobs)
        )
    )
)

#Format
(
    summary
    .sort(
        by=['pais_nacimiento', 'logro']
    ).with_columns(
        c.pais_nacimiento.replace_strict(var_labels['pais_nacimiento']),
        c.logro.replace_strict(trans.logro_lbls),
    ).with_columns(
        cs.float().round(2)
    ).pivot(on='pais_nacimiento', index='logro', values='w_promedio N'.split()
    ).write_excel(path_results.joinpath('salario.xlsx'))
)
os.startfile(path_results.joinpath('salario.xlsx'))

#--------------------------------------
# ENAHO
#--------------------------------------

file_path = bases.joinpath(r'cr\limpio\cr_region_grouped_processed.sav')
df, var_labels, col_labels = da.read_file(file_path, output_format='polars')
df:pl.DataFrame
da.var_labels = var_labels

edad = c.a5.is_between(15,65, closed='both')
sexo = c.a4.eq(2)
logro = c.logro.is_not_null()
activo = c.condact.eq(1)
asalariado = c.posiemppri.is_in([11,12]) #ENAHO
nacionalidad = c.nacionalidad.is_in([1, 0])
w_real_outliers = c.w_hora.gt(0)
horas = c.hortotnorm.is_between(0,168, closed='none')
anno = c.anno.eq(2023)

#------------------------------
# Tables
#------------------------------
# Weighted mean salary
group_cols = ['nacionalidad', 'logro']
summary = (
    df
    .filter(
        edad, sexo, logro, activo, asalariado, nacionalidad, w_real_outliers, horas, anno
    )
    .group_by(
        *group_cols
    )
    .map_groups(
        lambda gp:
        gp.select(
            c(group_cols).first(),
            w_promedio=pl.lit((stat:=da.w_stat(gp, col='w_hora', factor='factor')).mean),
            N=pl.lit(stat.nobs)
        )
    )
)

#Format
(
    summary
    .sort(
        by=group_cols
    ).with_columns(
        c.nacionalidad.replace_strict(var_labels['nacionalidad']),
        c.logro.replace_strict(trans.logro_lbls),
    ).with_columns(
        cs.float().round(2)
    ).pivot(on='nacionalidad', index='logro', values='w_promedio N'.split()
    ).write_excel(path_results.joinpath('salario.xlsx'))
)
os.startfile(path_results.joinpath('salario.xlsx'))


