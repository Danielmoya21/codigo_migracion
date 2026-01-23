import polars as pl, polars.selectors as cs
from polars import col as c
import pyreadstat
from pathlib import Path
from definitions import bases
from ucr_tools.core import data_analysis as da

from codigo.costa_rica import filters_cr as filters
import importlib
importlib.reload(filters)

df, meta = pyreadstat.read_sav(bases.joinpath('cr/limpio/cr_region_processed.sav'), output_format='polars')
df = df.rename(str.lower)
df:pl.DataFrame
var_labels = {k.lower(): v for k, v in meta.variable_value_labels.items()}
col_labels = {k.lower(): v for k, v in meta.column_names_to_labels.items()}
da.var_labels=var_labels

sex=2
nac=1

(
da.tab(
    (test:=df.filter(filters.wage_filters(nac=nac))), 
    col='logro',
    factor='factor'
    )
    .with_columns(c.logro.replace_strict(var_labels['logro']))
    .style.fmt_number(cs.numeric()).tab_header(var_labels['nacionalidad'].get(nac)).show()
)


df.filter(filters.wage_filters()).shape

test = (
    df
    .filter(filters.wage_filters())
    .group_by('nacionalidad logro'.split())
    .agg(
        c.w_real.mean().alias('mean'),
        c.w_real.std().alias('std'))
    .sort('logro nacionalidad'.split())
    .with_columns(
        c.logro.replace_strict(var_labels['logro']),
        c.nacionalidad.replace_strict(var_labels['nacionalidad']),
    )
    .with_columns(cs.numeric().round(2))
    .pivot(on='nacionalidad', index='logro')
)
def wrap_word(col):
    return pl.lit('('), c(col), pl.lit(')')

test.select(
    'logro',
    pl.concat_str(c.mean_costarricense, pl.lit('\n'), *wrap_word('std_costarricense')),
    pl.concat_str(c.mean_nicaraguense, pl.lit('\n'), *wrap_word('std_nicaraguense')),
).write_clipboard()

(
    df
    .filter(filters.wage_filters())
    .group_by()
)

