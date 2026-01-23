from pathlib import Path
import polars as pl, polars.selectors as cs
from polars import col as c
import pandas as pd
import pyreadstat
from definitions import bases
from ucr_tools.core import data_analysis as da
from codigo.transformations import recode_region, region_lbls_chile
from codigo import display_results as dis_res

df, meta = pyreadstat.read_sav(bases.joinpath(r'chile\limpio\chile_all.sav'), output_format='polars')
df:pl.DataFrame
df = df.rename(str.casefold)
col_labels = meta.column_names_to_labels = {k.casefold():v for k, v in meta.column_names_to_labels.items()}
var_labels = meta.variable_value_labels = {k.casefold():v for k, v in meta.variable_value_labels.items()}
da.var_labels = var_labels

output = Path(__file__).parent.joinpath('results/nacionalidad_count_chile.xlsx')

#Limpiar nacionalidades
df = (
    df
    .with_columns(
        pl.when(~c.r1b.is_in([1,2,3])) #Eliminate people who did not answer
        .then(None)
        .otherwise(c.nacionalidad)
        .alias('nacionalidad')
    )
    .with_columns(
        pl.when(
            c.country_code.eq(505) #Colombia
        )
        .then(3)
        .when(c.country_code.eq(413)) #Haiti
        .then(4)
        .otherwise(c.nacionalidad)
        .alias('nacionalidad')
    )
    .with_columns(c.region.replace(recode_region).replace({5:4}))
    
)
var_labels['nacionalidad'].update({3:'Colombianos', 4:'Haitianos'})

#-----------------------------
# Con factor de expansion
#-----------------------------
df_expansor = (
    df
    .filter(c.sexo.eq(2), c.edad.is_between(14, 65, closed='none'))
    .group_by('region anno nacionalidad'.split())
    .agg(c.expr.sum())
    .sort('region anno nacionalidad'.split())
    .with_columns(
        c.nacionalidad.replace_strict(var_labels['nacionalidad']),
        c.region.replace_strict(region_lbls_chile)
    )
    .with_columns(
        c.nacionalidad.fill_null('N/A'),
        c.expr.truediv(c.expr.sum().over('region anno'.split())).alias('pct'),
        c.anno.cast(pl.Int32)
    )
    .pivot(on='nacionalidad', values='expr pct'.split())
    .with_columns(cs.starts_with('expr', 'pct').fill_null(0))
)

cols1 = 'expr_chileno expr_venezolano expr_Haitianos expr_Colombianos expr_otro expr_N/A'.split()
cols2 ='pct_chileno pct_venezolano pct_Haitianos pct_Colombianos pct_otro pct_N/A'.split()

df_expansor = df_expansor.select(*'region anno'.split(), *cols1, *cols2)

df_expansor = df_expansor.to_pandas()
float_cols = df_expansor.select_dtypes('float').columns
# df_expansor = df_expansor.set_index('region anno'.split()).style.format(precision=2, subset=float_cols)
df_expansor = df_expansor.set_index('anno'.split()).style.format(precision=2, subset=float_cols)

for temp in [df_expansor]:
    with pd.ExcelWriter(output, mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
        temp.to_excel(writer, sheet_name={df_expansor:'con_factor'}.get(temp))

#--------------------------------------
# AGREGADO
#--------------------------------------
df_expansor = (
    df
    .filter(c.sexo.eq(2), c.edad.is_between(14, 65, closed='none'))
    .group_by('anno nacionalidad'.split())
    .agg(c.expr.sum())
    .sort('anno nacionalidad'.split())
    .with_columns(
        c.nacionalidad.replace_strict(var_labels['nacionalidad']),
        # c.region.replace_strict(region_lbls_chile)
    )
    .with_columns(
        c.nacionalidad.fill_null('N/A'),
        c.expr.truediv(c.expr.sum().over('anno'.split())).alias('pct'),
        c.anno.cast(pl.Int32)
    )
    .pivot(on='nacionalidad', values='expr pct'.split())
    .with_columns(cs.starts_with('expr', 'pct').fill_null(0))
)
df_expansor = df_expansor.select(*'anno'.split(), *cols1, *cols2)

df.filter(c.anno.eq(2022), c.edad.is_between(14,65, closed='none')).group_by(c.sexo).agg(c.expr.sum())

