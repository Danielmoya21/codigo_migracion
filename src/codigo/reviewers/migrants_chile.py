import importlib
from pathlib import Path
from numpy import var
import polars as pl, polars.selectors as cs
from polars import col as c
import pandas as pd
from definitions import bases
from ucr_tools.core import data_analysis as da
from codigo.transformations import recode_region, region_lbls_chile
from codigo import display_results as dis_res
from codigo.chile import filters_chile

importlib.reload(da)
importlib.reload(filters_chile)

###!!! importante las proporciones y recuentos se calculo con la base original (chile_all.sav), las estadísticas descriptivas con la base procesada
df, var_labels, col_labels = da.read_file(bases.joinpath(r'chile\limpio\chile_region_processed.sav'), output_format='polars')
df:pl.DataFrame
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
# TABLA PROPORCIONES NACIONALIDADES
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
# DESCRIPTIVAS VENEZOLANOS Y HAITIANOS
#--------------------------------------

nacionalidades=[0,3,4]
df_descriptives = df.filter(c.nacionalidad.is_in(nacionalidades), c.sexo.eq(2), c.anno.eq(2022)).clone()

def order_cols():
    return [cs.ends_with(var_labels['nacionalidad'].get(i)) for i in nacionalidades]

def to_decimal():
    return cs.contains('proportion').truediv(100).round(2)

#Logro academico
proportions_logro = da.tab(df_descriptives, col='logro', groups='nacionalidad', factor='expr')
proportions_logro = da.apply_labels(proportions_logro, 'nacionalidad logro'.split()).pivot(on='nacionalidad', index='logro')
proportions_logro.with_columns(to_decimal()).select(~cs.contains('_'), *order_cols()).write_clipboard()

#Edad
mean_edad = da.compute_stat(df_descriptives, col='edad', groups='nacionalidad', factor='expr')
mean_edad = da.apply_labels(mean_edad, 'nacionalidad').with_columns(cs.numeric().round(2)).with_columns(pl.concat_str('mean', pl.lit('\n'), *dis_res.wrap_word('std')).alias('columna'))
mean_edad.write_clipboard()

#Participacion Fuerza de Trabajo
labor_force = da.tab(df_descriptives, col='activ', groups='nacionalidad', factor='expr')
labor_force = da.apply_labels(labor_force, 'nacionalidad activ'.split())
labor_force.pivot(on='nacionalidad', index='activ').with_columns(to_decimal()).select(~cs.contains('_'), *order_cols()).write_clipboard()

#Salarios
wages = da.compute_stat(df_descriptives.filter(filters_chile.wage_filters()), col='w_hora', groups='nacionalidad logro'.split(), factor='expr')
wages = da.apply_labels(wages, 'nacionalidad logro'.split()).with_columns(cs.numeric().round(2)).with_columns(pl.concat_str('mean', pl.lit('\n'), *dis_res.wrap_word('std')).alias('columna'))
wages.pivot(on='nacionalidad', index='logro').select(~cs.contains('_'), *order_cols()).write_clipboard()

#Formalidad
formalidad = da.tab(df_descriptives.filter(c.cotiza.ne(-88), c.activ.eq(1)), col='cotiza', groups='nacionalidad', factor='expr')
formalidad = da.apply_labels(formalidad, 'cotiza nacionalidad'.split())
formalidad.pivot(on='nacionalidad', index='cotiza').with_columns(to_decimal()).select(~cs.contains('_'), *order_cols()).write_clipboard()

[print(i) for i in filters_chile.wage_filters()]