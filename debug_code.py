import polars as pl
from polars import col as c
import pyfixest as pf
import numpy as np
import numpy as np

df:pl.DataFrame
df = df.drop_nulls(subset='p_bajo')
df = df.drop_nulls(subset='p_alto')
df = df.filter(c(endogena).gt(0))

model = general_results['Wages_general']
model:pf.feols
df_changed = df.with_columns(c.p_alto.add(1))

resultado1 = model.predict(df.to_pandas())
resultado2 = model.predict(df_changed.to_pandas())

print('Diferencias con logaritmos')
print(model.predict(df_changed.to_pandas()) - model.predict(df.to_pandas()))

print('Calculo cambio porcentual usando valores absolutos')
print(np.exp(resultado1), np.exp(resultado2))

print('Diferencia estiamada')
print((np.exp(resultado2) - np.exp(resultado1))/np.exp(resultado1)*100)

print('Cambio porcentual usando lograitmos difiere porque el coeificiente es grande')

