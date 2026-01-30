## Activeaza environment

In windows:
.\venv\Scripts\Activate.ps1

### Remarca

InsCodeVersions -> tine de institutul de statistica - identic peste tot


InsDeclarationHeader -> tine de firma - pt o firma anume toate sunt la fel exceptand RefPeriod - care e data intrarii


InsArrivalItem -> se face unu per item din tabelul excel - reprezinta intrarea 

Chestii idetince aici: 
- NatureOfTransactionACode
- NatureOfTransactionBCode
- DeliveryTermsCode


Ce trebuie mapat:

- ModeOfTransportCode - rutier 
- CountryOfOrigin -  CN - China
- CountryOfConsignment - CZ - Cehia



TODO:
1. Lista cu coduri care necista UMS si care nu
2. Scoate faza cu virgula - o sa fie rotunjite
3. Creeaaza functie de agregare pe cheia n8Code - cu cumulare pe( suma, cantitate, netMass, qtyInSupply)