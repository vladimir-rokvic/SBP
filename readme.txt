SBP upiti - opis query6 - query10, Marko


6. Koja kategorija hrane (branded_food_category) ima najpovoljniji odnos proteina i masti? Za svaku kategoriju izračunati prosečan odnos Protein-G prema Total lipid (fat)-G. Rangirati kategorije silazno po tom odnosu i prikazati top 15 — ovo praktično pokazuje koje kategorije nude najviše proteina uz najmanje masti, što je korisno za procenu nutritivne vrednosti jela po tipu.

7. Izveštaj o vlaknima (Fiber, total dietary-G) po kategorijama hrane
Za svaku branded_food_category ispisati: koji proizvod (description) ima najviše vlakana, koji ima najveći udeo vlakana u ugljenim hidratima (Carbohydrate, by difference-G), i koja kategorija ima najveći prosek vlakana. Posebno istaći kategorije gde je prosek vlakana izuzetno nizak (ispod 0.5g), što ukazuje na visoko prerađene namirnice.

8. Raspodela kategorija hrane po omeru zasićenih i nezasićenih masnih kiselina
Za svaki branded_food_category izračunati prosečan odnos Fatty acids, total saturated-G prema zbiru Fatty acids, total monounsaturated-G i Fatty acids, total polyunsaturated-G. Grupisati kategorije u tri opsega (povoljno / neutralno / nepovoljno) i prikazati koliko kategorija pada u svaki opseg.

9. Analiza natrijuma (Sodium, Na-MG) u odnosu na kalorije po kategorijama
Za svaku kategoriju izračunati prosečan sadržaj natrijuma na 100 kcal. Rangirati kategorije od najslanijih do najmanje slanih i identifikovati koje kategorije jela (npr. supe, sosevi, grickalice) konzistentno prelaze preporučenu dnevnu vrednost ako se konzumiraju u uobičajenim porcijama (serving_size).

10. "Nutritivni skor" za kategorije jela — kombinovana ocena mikronutrijenata
Definisati skor kao normalizovani zbir ključnih mikronutrijenata: Iron, Fe-MG, Calcium, Ca-MG, Potassium, K-MG, Vitamin C, total ascorbic acid-MG i Fiber, total dietary-G — sve na 100 kcal. Rangirati branded_food_category po ovom skoru i prikazati top 20 i bottom 20, zajedno sa prosečnim kalorijama kategorije.
