from datetime import date, timedelta
from unicodedata import numeric
import pyreadstat
import polars as pl, polars.selectors as cs
from polars import col as c
from ucr_tools.core import data_analysis as da
from definitions import bases
from codigo import display_results as dis_res

df, meta = pyreadstat.read_sav(bases.joinpath(r'cr\limpio\cr_region_processed.sav'), output_format='polars')
df:pl.DataFrame
var_labels = meta.variable_value_labels
col_labels = meta.column_names_to_labels
dis_res.var_labels=var_labels

cols_exogenas = 'p p_bajo p_alto a6'.split()
filter_exogenas = ( # Get observations with no null values for all regressors
        pl.all_horizontal(c(cols_exogenas).is_not_null()) |
        c.habilidad.is_in([df['habilidad'].min(),df['habilidad'].max()])
    )
wage_filters = (
    c.posiemppri.is_in([11,12]), #Keep wage earners
    # c.nacionalidad.eq(1),
    # c.a4.eq(),
    c.hortotnorm.lt(72),
    c.exp.lt(40),
    c.condact.eq(1),
    c.w_real.is_between(0,40_000, closed='none'),
    )
employment_filters = (
    # c.nacionalidad.eq(1),
    # c.a4.eq(args.sexo),
    c.hortotnorm.is_null() | c.hortotnorm.lt(72),
    c.exp.lt(40)
    )

df_wage = df.filter(filter_exogenas, wage_filters).clone()
df_emp = df.filter(filter_exogenas, employment_filters).clone()

#Proporciones
summary = pl.from_pandas(
    dis_res.cross_tab(
        df_emp.filter(c.nacionalidad.is_in([0,1]), c.a4.eq(2)), 
        ['logro','nacionalidad'])
    )
summary.with_columns((cols:=cs.numeric()).truediv(cols.sum()))\
    .select(
    c.row_0.append(pl.lit('Total')),
    cols.append(cols.sum())
    ).with_columns(cols.round(2)).write_clipboard()

#Salarios
test = (
    df_wage
    .filter(c.a4.eq(2))
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

df_emp.group_by('nacionalidad a4'.split()).agg(c.a5.mean()).pivot(on='a4', index='nacionalidad').filter(c.nacionalidad.is_in([1,0])).write_clipboard()
