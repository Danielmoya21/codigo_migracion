from polars import col as c
import polars as pl

exogenas = 'p + p_bajo + p_alto + C(ecivil)'
cols_exogenas = 'p p_bajo p_alto ecivil'.split()
categoricals = 'ecivil'

def filter_exogenas(min_skill=1):
    return (
        pl.all_horizontal(c(cols_exogenas).is_not_null())
        | c.habilidad.is_in([min_skill,10])
    )

def employment_filters(nac=1, sex=2):
    return (
    c.nacionalidad.eq(nac),
    c.a4.eq(sex),
    )


mean = 4846.5451
std = 6827.127169
def wage_filters(nac=1, sex=2):
    return (
    # c.nacionalidad.eq(nac), #Keep natives
    c.sexo.eq(sex), #keep men/women
    c.activ.eq(1),
    c.asal.eq(1), #Keep wage earners
    # c.ecivil.is_between(1,8, closed='both'),
    c.o10.is_between(0,168,closed='none'),
    c.w_real.gt(0)
    
    #----------- outliers
    # c.exp.lt(40),
    # c.o10.is_between(0,72, closed='none'),
    # c.w_real.is_between(mean-4*std, mean+4*std, closed='none'),
    )
