import spss "C:\Users\dmoya\OneDrive\Desktop\UCR\bases_de_datos\ENAHO\sav\ENAHO 2023.sav", clear

recode LugNac (0/1=1) (3/4=3), gen(nacionalidad)

label define nacionalidad 1 "Tico" 2 "Nica" 3 "Otro"
label values nacionalidad nacionalidad
keep if inlist(nacionalidad, 1,2)

global f_edad inrange(A5, 15,64)

*Poblacion en edad de trabajar
gen byte work_age = inrange(A5, 15, 64)
bysort A4: tab work_age nacionalidad [fw=FACTOR], col

*Poblacion Economicamente Activa
gen byte pea = inlist(CondAct, 1, 2)
bysort A4: tab pea nacionalidad [fw=FACTOR] if $f_edad, col

*Desempleo
bysort A4: tab CondAct nacionalidad [fw=FACTOR] if pea==1 & $f_edad, col

*Secundaria
recode NivInst (0/3 5=0) (4 6/8=1) (99=.), gen(bachillerato)
bysort A4: tab bachillerato nacionalidad [fw=FACTOR] if inrange(A5, 24,64), col

*Asegurados
gen byte asegurado = inlist(A11, 1, 8, 9, 12, 14)
replace A11 = . if A11 == 99
bysort A4: tab asegurado nacionalidad [fw=FACTOR] if inrange(A5, 15,65) & (CondAct==1), col

