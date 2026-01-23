from numpy import var
import polars as pl, polars.selectors as cs
from polars import col as c
import pyreadstat
from pathlib import Path
from definitions import bases
from ucr_tools.core import data_analysis as da
import general as gen


df, meta = pyreadstat.read_sav(bases.joinpath('cr/ENAHO_2023.SAV'), output_format='polars')
df = df.rename(str.lower)
df:pl.DataFrame
var_labels = {k.lower(): v for k, v in meta.variable_value_labels.items()}
col_labels = {k.lower(): v for k, v in meta.column_names_to_labels.items()}
da.var_labels=var_labels



#--------------------------------------
# DEFINE FILTERS
#--------------------------------------
nacional = gen.filtro_nac('lugnac', [0,1])
extranjero = gen.filtro_nac('lugnac', 2)
mujer = gen.filtro_sexo('a4', 2)
edad_fuerza = gen.filtro_edad('a5')
bachillerato = c.nivinst.is_in([4,6,7,8])

df = (
    df
    .with_columns(
        pl.when(
            edad_fuerza
        )
        .then(1)
        .otherwise(0)
        .alias('edad_dummy')
    )
)

df = (
    df
    .with_columns(
        pl.when(bachillerato)
        .then(1)
        .when(c.nivinst.eq(99))
        .then(None)
        .otherwise(0)
        .alias('bachillerato')
    )
)

#Fuerza laboral
da.tab(df.filter(nacional, mujer), 'edad_dummy', 'expr').style.fmt_number().show()
da.tab(df.filter(extranjero, mujer), 'edad_dummy', 'expr').style.fmt_number().show()

#Desempleo
da.tab(df.filter(nacional, mujer, c.activ.is_not_null()), 'activ', 'expr').with_columns(c.activ.replace_strict(var_labels['activ'])).style.fmt_number(cs.float()).show()

#Participacion
da.tab(df.filter(nacional, mujer, edad_fuerza, c.activ.is_not_null()), 'activ', 'expr').with_columns(c.activ.replace_strict(var_labels['activ'])).style.fmt_number(cs.float()).show()

#Bachillerato
da.tab(df.filter(extranjero, mujer, c.bachillerato.is_not_null(), filtro_edad('edad', 24)), 'bachillerato', 'expr').style.fmt_number(cs.float()).show()

#--------------------------------------
# CHILE
#--------------------------------------
df, meta = pyreadstat.read_sav(bases.joinpath('chile/casen_cleaned_2022.sav'), output_format='polars')
df:pl.DataFrame
df = df.rename(str.lower)
var_labels = {k.lower(): v for k, v in meta.variable_value_labels.items()}
col_labels = {k.lower(): v for k, v in meta.column_names_to_labels.items()}
da.var_labels=var_labels

#--------------------------------------
# DEFINE FILTERS
#--------------------------------------
nacional = gen.filtro_nac('nacionalidad', 1)
extranjero = gen.filtro_nac('nacionalidad', 0)
mujer = gen.filtro_sexo('sexo', 2)
edad_fuerza = gen.filtro_edad('edad')
bachillerato = c.educ.is_in([5, 6, 7, 8, 9, 10, 11, 12])

df = (
    df
    .with_columns(
        pl.when(
            edad_fuerza
        )
        .then(1)
        .otherwise(0)
        .alias('edad_dummy')
    )
)

df = (
    df
    .with_columns(
        pl.when(bachillerato)
        .then(1)
        .when(c.educ.eq(-88))
        .then(None)
        .otherwise(0)
        .alias('bachillerato')
    )
)


da.check_label(var_labels, 'ocupado')