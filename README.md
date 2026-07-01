# Facility location

## Formulazione problema

Una azionda ha **n** sedi, il costo di apertura di una sede *i* è **f~i~** ed è costante.
L'azienda ha **m** acquirenti, ogni acquirente *j* vuole acquistare **d~j~** unità.  
Il costo di spedizione dalla sede *i* al cliente *j* è **c~ij~**.  
Ipotizziamo inoltre che ogni sede *i* abbia una capacità di produzione massima *u~i~*.

Ogni sede *i* può essere aperta o chiusa, introduciamo le variabili binarie: *x~i~* il cui valore è *0* se i è chiusa, *1* altrimenti. Inoltre *y~ij~* indica la frazione della domanda *d~j~* soddisfatta dalla sede *i*.

## Funzione obiettivo

La funzione f da **minimizzare** è:

![Facility Location Problem formulation](images/facility-location-formulation.svg)


Σᵢ Σⱼ cᵢⱼ dⱼ yᵢⱼ + Σᵢ fᵢ xᵢ

Subject to:

Σᵢ yᵢⱼ = 1                     ∀ j = 1,...,m

Σⱼ dⱼ yᵢⱼ ≤ uᵢ xᵢ              ∀ i = 1,...,n

yᵢⱼ ≥ 0                        ∀ i = 1,...,n, j = 1,...,m

xᵢ ∈ {0,1}                     ∀ i = 1,...,n

## Scelta linguaggio
Per ora il linguaggio scelto è OCaml, eventualmente vedrò di passare a python se le librerie esistenti si rivelano essere troppo utili

# [TODO]
praticamente tutto
