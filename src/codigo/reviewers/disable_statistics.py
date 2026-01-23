from statsmodels.stats.weightstats import DescrStatsW as ws
from ucr_tools.core import data_analysis as da
import polars as pl, polars.selectors as cs
from polars import col as c
import pyreadstat
from pathlib import Path
from codigo import transformations as trans
from ucr_tools.core import data_analysis as da
import os
from definitions import bases

#------------------------------
# Load files
#------------------------------
file_path = bases.joinpath('cr/ece_cr_final.dta')

path_results = Path(__file__).parent.joinpath('results')

df, meta = pyreadstat.read_dta(file_path, output_format='polars', encoding='utf-8')
var_labels = meta.variable_value_labels
col_labels = meta.column_names_to_labels
da.var_labels = var_labels
df:pl.DataFrame

#------------------------------
# Filters
#------------------------------
edad = c.edad.is_between(15,65, closed='both')
asalariado = c.posicion_empleo.eq(1)
nacionalidad = c.pais_nacimiento.is_in([1, 4])   #1: Costa RIca,  4: Nicaragua 
w_real_outliers = c.w_real.le(40_000).gt(0)
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
ipc_values = {
    2015: 93.00390934,
    2016: 93.44616814,
    2017: 94.53304812,
    2018: 96.50343843,
    2019: 99.29164281,
    2022: 112.0987,
    2023: 109.537132,
}
df = trans.add_real_wages(df, 'ingreso_bruto_total_trabajo_hora', ipc_values=ipc_values)

#------------------------------
# Tables
#------------------------------
# Weighted mean salary
group_cols = ['pais_nacimiento', 'logro']
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
            w_promedio=pl.lit((stat:=da.w_stat(gp, col='w_real', factor='factor_ponderacion')).mean),
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


