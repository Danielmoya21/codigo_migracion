from polars import col as c
from dataclasses import dataclass

def filtro_nac(col, values):
    if not isinstance(values, list):
        values = [values]
    return c(col).is_in(values)

def filtro_edad(col, min=15, max=64):
    return c(col).is_between(min, max, closed='both')

def filtro_sexo(col, value):
    return c(col).eq(value)

def filtro_educacion(col, values:list):
    if not isinstance(values, list):
        values=[values]
    return c(col).is_in(values)



nacional_cr = filtro_nac('lugnac', [0,1])
extranjero_cr = filtro_nac('lugnac', 2)
mujer_cr = filtro_sexo('a4', 2)
edad_fuerza_cr = filtro_edad('a5')
bachillerato_cr = filtro_educacion('nivinst', [4,6,7,8])

nacional_ch = filtro_nac('nacionalidad', 1)
extranjero_ch = filtro_nac('nacionalidad', 0)
mujer_ch = filtro_sexo('sexo', 2)
edad_fuerza_ch = filtro_edad('edad')
bachillerato_ch = filtro_educacion('educ', [5, 6, 7, 8, 9, 10, 11, 12])
