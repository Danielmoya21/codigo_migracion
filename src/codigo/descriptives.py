import polars as pl, polars.selectors as cs
from polars import col as c
from ucr_tools.core import data_analysis as da
from definitions import bases, results
from codigo import display_results as dis_res
from codigo.costa_rica import filters_cr

# file = bases.joinpath('cr/limpio/cr_region_grouped_processed.sav')
file = bases.joinpath('cr/limpio/cr_region_processed.sav')
output = results.joinpath('descriptives/descriptivas.xlsx')
df, var_labels, col_labels = da.read_file(file)
da.set_var_labels(var_labels)
df:pl.DataFrame

#--------------------------------------
# ESTADISTICAS DESCRIPTIVAS
#--------------------------------------
asegurados_list = [1, 8, 9, 12, 14]
df = (
    df.with_columns(
        pl.when(c.a11.is_in(asegurados_list)).then(1).when(c.a11.eq(99)).then(None).otherwise(0).alias('asegurado')
    )
)
df_descriptives = df.filter(c.nacionalidad.is_in([0,1]), c.a4.eq(1))

educacion = da.tab(df_restringido, col='logro', groups='nacionalidad')
educacion = da.apply_labels(educacion, cols='nacionalidad logro'.split())
educacion.pivot(on='nacionalidad', index='logro').select('logro', cs.ends_with('costarricense'),  cs.ends_with('nicaraguense'))#.write_clipboard()

ocupacion = da.tab(df_restringido, col='condact', groups='nacionalidad')
ocupacion = da.apply_labels(ocupacion, cols='nacionalidad condact'.split())
ocupacion.pivot(on='nacionalidad', index='condact').select('condact', cs.ends_with('costarricense'),  cs.ends_with('nicaraguense'))#.write_clipboard()


#--------------------------------------
# FILTROS PARA SALARIOS
#--------------------------------------
df_descriptives_salarios = df_descriptives.filter(
    c.posiemppri.is_in([11,12]), #Asalariados
    c.condact.eq(1),  #Ocupados
    c.hortotnorm.is_between(0,168,closed='none'), #Quitar horas no reportadas
    c.w_real.gt(0) #Mantener salarios positivos
    )

salarios = da.compute_stat(df_descriptives_salarios, col='w_real', groups='nacionalidad logro'.split()).with_columns(cs.numeric().round(2))
salarios = da.apply_labels(salarios, cols='nacionalidad logro'.split())
(
salarios
    .with_columns(pl.concat_str('mean', pl.lit('\n'), *dis_res.wrap_word('std')).alias('paste_col'))
    .pivot(on='nacionalidad', index='logro')
    .select('logro', cs.ends_with('costarricense'), cs.ends_with('nicaraguense'))#.write_clipboard()
)

#Formalidad
formalidad = da.tab(df_descriptives.filter(c.condact.eq(1), c.asegurado.is_not_null()), col='asegurado', groups='nacionalidad')
formalidad = da.apply_labels(formalidad, cols='nacionalidad')
formalidad.pivot(on='nacionalidad', index='asegurado').select('asegurado', cs.ends_with('costarricense'),  cs.ends_with('nicaraguense'))#.write_clipboard()

#-------------- esta es para muestra restringida
df_restringido = df_descriptives_salarios.filter(
    c.exp.lt(40),
    c.w_real.is_between(0, 40_000, closed='none'),
    c.hortotnorm.is_between(0, 72, closed='none'),
)

#--------------------------------------
# OCUPACIONES
#--------------------------------------

df_region= da.tab(
    df_descriptives
    .filter(
        filters_cr.employment_filters(sex=1),
    ),
    groups='nacionalidad',
    col='region',
)
df_region.pivot(on='nacionalidad', index='region').write_clipboard()

ocupaciones_hombres = [1,3,6,7,14]
ocupaciones_mujeres = [3,7,9,16,20]
for i in df_ocupaciones['nacionalidad'].unique().to_list():
    _df = (
        df_ocupaciones
        .filter(c.nacionalidad.eq(i))
        .filter(c.ramaemppri.is_in(list(map(lambda x: var_labels['ramaemppri'][x], ocupaciones_mujeres))))
    ).write_clipboard()
    input('>')
    
df_ocupaciones = (
    df_descriptives.filter(
        c.condact.eq(1), 
        c.ramaemppri.is_not_null(), 
        c.logro.eq(4),
        c.anno.eq(2023),
        )
    )
ocupaciones = da.tab(
    df_ocupaciones,
    col='ramaemppri', 
    groups='nacionalidad',
    factor='factor'
    )
(
    ocupaciones
    .pivot(on='nacionalidad', index='ramaemppri')
    .sort('proportion_costarricense', descending=True)
    .write_clipboard()
)

# REGION
#--------------------------------------
#--------------------------------------
regiones = da.tab(df_descriptives_salarios, col='region', groups='nacionalidad')
regiones = da.apply_labels(regiones, cols='nacionalidad region'.split())
regiones.pivot(on='nacionalidad', index='region').write_clipboard()


#--------------------------------------
# CHILE
#--------------------------------------

file = bases.joinpath('chile/limpio/chile_region_processed.sav')
output = results.joinpath('descriptives/descriptivas.xlsx')
df, var_labels, col_labels = da.read_file(file)
da.var_labels = var_labels
df:pl.DataFrame

df_descriptives = df.filter(c.nacionalidad.is_in([0,1]), c.sexo.eq(2), c.ecivil.is_between(1,8, closed='both'))

educacion = da.tab(df_restringido, col='logro', groups='nacionalidad')
educacion = da.apply_labels(educacion, cols='nacionalidad logro'.split())
educacion.pivot(on='nacionalidad', index='logro').select('logro', cs.ends_with('chileno'),  cs.ends_with('venezolano'))#.write_clipboard()

ocupacion = da.tab(df_restringido, col='activ', groups='nacionalidad')
ocupacion = da.apply_labels(ocupacion, cols='nacionalidad activ'.split())
ocupacion.pivot(on='nacionalidad', index='activ').select('activ', cs.ends_with('chileno'),  cs.ends_with('venezolano'))#.write_clipboard()

edad = da.compute_stat(df_restringido, col='edad', groups='nacionalidad').with_columns(cs.numeric().round(2))
edad = da.apply_labels(edad, cols='nacionalidad'.split())
edad.with_columns(pl.concat_str('mean', pl.lit('\n'), *dis_res.wrap_word('std')).alias('paste_col'))#.write_clipboard()

#--------------------------------------
# FILTROS PARA SALARIOS
#--------------------------------------
df_descriptives_salarios = df_descriptives.filter(
    c.activ.eq(1),
    c.asal.eq(1), #Keep wage earners
    c.w_hora.gt(0),
    c.o10.is_between(0,168, closed='none'),
    
    #-------------- esta es para muestra restringida
    # c.o10.is_between(0,72, closed='none'),
    # c.exp.lt(40),
)

ipc_2020 = df_descriptives.filter(c.anno.eq(2020)).select(c.ipc.unique()).item()
df_descriptives_salarios = df_descriptives_salarios.with_columns(c.ipc.truediv(ipc_2020).alias('ipc_2020')).with_columns(c.w_hora.truediv(c.ipc_2020).alias('w_real_2020'))

salarios = da.compute_stat(df_descriptives_salarios, col='w_real_2020', groups='nacionalidad logro'.split()).with_columns(cs.numeric().round(2))
salarios = da.apply_labels(salarios, cols='nacionalidad logro'.split())
(
salarios
    .with_columns(pl.concat_str('mean', pl.lit('\n'), *dis_res.wrap_word('std')).alias('paste_col'))
    .pivot(on='nacionalidad', index='logro')
    .select('logro', cs.ends_with('chileno'), cs.ends_with('venezolano')).write_clipboard()
)

formalidad = da.tab(df_descriptives.filter(c.anno.eq(2022), c.activ.eq(1), c.cotiza.is_not_null()), col='cotiza', groups='nacionalidad')
formalidad = da.apply_labels(formalidad, cols='cotiza nacionalidad'.split())
formalidad.pivot(on='nacionalidad', index='cotiza').select('cotiza', cs.ends_with('chileno'),  cs.ends_with('venezolano')).write_clipboard()


#-------------- esta es para muestra restringida
mean = 4846.5451
std = 6827.127169

df_restringido = df_descriptives_salarios.filter(
    c.w_real.is_between(mean-4*std, mean+4*std, closed='both'),
    c.o10.is_between(0,72, closed='none'),
    c.exp.lt(40),
    )

#--------------------------------------
# FORMALIDAD
#--------------------------------------
da.apply_labels(
    da.tab(df_descriptives
           .filter(
               c.cotiza.is_not_null() & c.cotiza.ne(-88),
               c.anno.eq(2022),
               c.activ.eq(1),
               c.sexo.eq(2)),
           col='cotiza', groups='nacionalidad'),
    cols='cotiza nacionalidad'.split()
    ).pivot(on='nacionalidad', index='cotiza')#.write_clipboard()

mapping_ramas = {
    2: 1,
    3: 2,
    4: 3,
    5: 4,
    9: 8,
    8: 9,
    10: 11,
    11: 12,
    12: 15,
    13: 16,
    14: 17,
    15: 19,
    16: 20,
    17: 21,
}
df_descriptives_salarios = df_descriptives_salarios.with_columns(pl.when(c.anno.is_in([2015,2017])).then(c.rama1.replace(mapping_ramas)).otherwise(c.rama1).alias('rama1'))
df_descriptives_salarios = df_descriptives_salarios.filter(c.rama1.is_between(1,21))

#--------------------------------------
# OCUPACIONES
#--------------------------------------
ocupaciones = da.tab(df_descriptives_salarios, col='rama1', groups='nacionalidad')
ocupaciones = da.apply_labels(ocupaciones, cols='nacionalidad rama1'.split()).pivot(on='nacionalidad', index='rama1').sort('proportion_chileno', descending=True)
ocupaciones.write_clipboard()


#--------------------------------------
# REGIONES
#--------------------------------------
regiones = da.tab(df_descriptives_salarios, col='region', groups='nacionalidad')
regiones = da.apply_labels(regiones, cols='nacionalidad region'.split())
regiones.pivot(on='nacionalidad', index='region').write_clipboard()

for i in [2015,2017,2020,2022]:
    file = bases.joinpath(f'chile/casen_cleaned_{i}.sav')
    df, var_labels, col_labels = da.read_file(file, metadata_only=True)

