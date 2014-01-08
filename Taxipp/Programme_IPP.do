*************************************************************************************************************************

* OBJECTIF : 
	*- permettre la création de différents scénarios de cas-types
	*- sortir une base (au niveau du ménage = foyf = foys) présentant :
							* les caractéristiques des scénarios 
							* les résultats des calculs des impôts et prestations
	*- préparer l'utilisation de ces bases par OF et Python

* PRINCIPE :
	*- l'utilisateur remplie les variables de choix proposées au début puis le programme se déroule
	*- à terme, il est envisagé de produire tous les scénarios d'un coup en faisant des boucles sur les globales de choix

* A FAIRE :
	*- finir la prise en compte des enfants dans les foyf
	*- élargir le programme pour prendre en compte d'autres types de revenus (chômage, retraite, capital...)
	*- comprendre pourquoi on ne retombe pas sur sal_irpp pour le public (d'Etat : seule prise en compte dans TAXIPP)
	
* PLAN
	* 0. Préambule
	* 1. Création base pour chaque scénario
	* 2. Simulation
	* 3. Résultats
	
* Rappel : on appelle SCENARIO un ensemble de caractéristiques propre à l'entité menage=foyf=foys, 
		 * seul un certain type de revenu étant décliné pour constituer la base
		 
*************************************************************************************************************************
		 
***********************************
*******    0.   Préambule   *******
***********************************

clear
set more off
global taxipp         "P:\TAXIPP\TAXIPP 0.3"
global taxipp_encours "P:\TAXIPP\TAXIPP 0.3\4-Analyses\Test OF"
global sources_brutes "P:\TAXIPP\TAXIPP 0.3\1-Sources\Sources brutes"
global sources_2006   "$taxipp_encours\1-Sources"
global dofiles        "P:\TAXIPP\TAXIPP 0.3\1-Sources\Dofiles"
global label          "$dofiles\Labels"
global paramdir		  "$taxipp_encours\2-Parametres" 
global progdir		  "$taxipp\3-Programmes\Modèle" 
global label03        "$taxipp\3-Programmes\Labels 0.3"
global repo        	  "U:\IPPython\openfisca-taxipp-comparison\Taxipp"

global incidence 1
global castype 1
global contrefactuel 2
if ${contrefactuel} == 2 { 
         global scenario "" 
		 global reforme ""
	}

global annee_sim = 2011
global annee = ${annee_sim}

* Appel des paramètres : paramètres législatifs stockés pour l'année 2011 sous forme de global
qui do "$progdir\0_appel_parametres0_3.do"

	*^^^^^^^*
	* CHOIX *
	*^^^^^^^*
global scenario "_couple_mar"
global nmen =4
*global nrev= 4 /* Nombre de revenus différents considérés */
global nbh_sal = 1820 /* 1607 Temps plein ?*/
global rev_max = 100000
global couple 1 /* si on veut faire des couples */
	global marie 1 /* 1 si marié */
	global concubin 0 /* 1 si concubin */

global npac 2 /* si on rajouter des pac (inactif pour l'instant) */

global cadre  1
global public 0
global taille_ent 20
global tva 0
	*^^^^^^^^^^^*
	* FIN CHOIX *
	*^^^^^^^^^^^*

*global nmen = ${nrev}*(${nrev}-1)/2 if ${couple}=1 
*global nmen = ${nrev} if ${couple}=0

* ne pas se tromper : is couple = 0, les individus sont célibataires d'office
if $couple ==0{
	global marie 0 /* 1 si marié */
	global concubin 0 /* 1 si concubin */
	global statut_mat "C"
}
global rev 
forvalues i = 1 /$nmen {
	global rev1 =(`i'-1)*${rev_max}/(${nrev}-1)
	global rev ${rev} ${rev1}
	}
global num : list sizeof global(rev)
*TEST*
*if ${num}!=(1+${couple})*${nmen} {
*	disp "Il faut qu'il y ait autant de revenus imposables que d'individus créés : " (1+${couple})*${nmen}
*}

***********************************
*******  1.	Création base 	*******
***********************************

use "$repo\base.dta", clear
* Objectif : créer X foyers fiscaux (avec le bon nombre d'individu dans chaque)

************
** a. On met d'abord les personnes de référence et leur conjoint (s'il y a lieu)
global N_obs = (1+${couple})*${nmen} /* on garde X individus si célib / 2*X si couples */
expand ${N_obs} in 1

replace id_indiv = _n

gen id_con =0 /* "con" deviendra concubin ou conjoint selon le scénario choisi i.e. selon que le couple est marié ou non*/
gen id_concu = 0

if $couple !=0{
	replace id_con = _n-1 if mod(id_indiv,2)==0 
	replace id_con = _n+1 if mod(id_indiv,2)==1
	replace decl=1 if mod(id_indiv,2)==1 
	replace conj=1 if mod(id_indiv,2)==0 
	replace couple =1
	replace id_foy =(_n+1)/2
	replace id_foy =(_n)/2 if mod(id_indiv,2)==0
}
if $couple == 0{
	replace couple =0
	replace id_foy =_n
	replace decl=1
	global statut_mat "C" /* celib*/
}
if $marie == 1{
	gen id_conj =id_con
	global statut_mat "M" /* marié*/

}
if $concubin == 1{
	replace id_concu =id_con
	global statut_mat "C" /* celib*/
}
** a. FIN **********

************
** b.  Rajouter des enfants et les ranger dans les foyers fiscaux
global N_enf = ${npac}*${nmen}
expand ${N_enf}+1 in 1,gen(exp)
replace pac = exp
drop exp
replace id_ind = _n if pac ==1

gen id_foy_pac = (pac==1)
	replace id_foy_pac = _n -${nmen} if pac== 1
	replace id_foy_pac = _n -${nmen}*${npac} if id_foy_pac > ${nmen} & pac ==1
	replace id_foy_pac = _n -${nmen}*${npac} if id_foy_pac > ${nmen} & pac ==1

forvalues i =1/$npac{
	replace id_foy_pac = _n -${nmen}*(`i') if id_foy_pac > ${nmen}*(`i'-1) & pac ==1
}
replace id_foyf = id_foy_pac if pac ==1
drop id_foy_pac

* Les variables des enfants : (A COMPLETER)
replace nenf= $npac
** b. FIN **********

************
** c.  Variables à modifier
replace nadul=1 if pac !=1
replace age = 38 if pac !=1/* Pour qu'il naisse en 1975 */
replace age = 10 if pac ==1
replace marie = ${marie}
gen cadre  = $cadre
replace public = $public 
gen mat = "$statut_mat"

bys id_foyf: replace num_indf=_n 

replace nbh_sal = $nbh_sal

forvalues r = 1/$num{
	global R : word `r' of $rev
	gen id_`r'=1 if id_ind == `r'
	replace sal_irpp = ${R} if id_`r'==1
	drop id_`r'
	}
sort id_indiv
order id_indiv id_foyf id_con couple pac decl conj mat marie sal_irpp
** c. FIN **********
* Eventuellement : Matching des concubins en ménages
	
save "$repo\base1${scenario}.dta", replace
use "$repo\base1${scenario}.dta", replace

************
** d.  Calcul des revenus bruts (sal, nonsal, chom, pension) à partir des revenus imposables */
* VERIFIER car on ne retombe pas sur le sal_irpp...
qui	do "$repo\revbrut.do"
** d. FIN **********

************
** e.  Imputation de variables nécessaires pour la suite */
qui do "$repo\imputations.do"
gen taille_ent = $taille_ent
gen tva = $tva
** e. FIN **********

************
** f.  Il faut gérer certaines variables de revenu financier...
qui	do "$repo\revfin.do"
** f. FIN **********

************
** g. un truc dont a besoin TAXIPP pour tourner : pas d'impact sur les résultats (car pas pris en compte dans OF?)
*egen masse_sal_brut_priv = total(sal_brut*(1-public)*pondv/1000000000)
gen tx_csp_priv_fac =0
*replace tx_csp_priv_fac = ${masse_csp_priv_fac_cn}/masse_sal_brut_priv if masse_sal_brut_priv !=0

*egen masse_sal_brut_pub=total(sal_brut*public*pondv/1000000000)
gen tx_csp_pub_0 = 0
*replace tx_csp_pub_0 = ${masse_csp_pub_cn}/masse_sal_brut_pub if masse_sal_brut_pub!=0

* Supprimer les variables créées mais qui vont être recalculées
drop *_sim salchom_imp-nbp_seul masse_* smic_h_brut_2006 rfon_irpp 
drop reduc_irpp_foy_tot-loyer_fictif_foy credit_div_foy-reduc_double_dec_foy rpp0_foy-irpp_ds_foy decote_irpp_foy irpp_brut_foy
drop sal_irpp_foy nonsal_irpp_foy pension_irpp_foy chom_irpp_foy pens_alim_rec_foy rfr_irpp_concu

*Individualisation de certains revenus fonciers
global liste "rfon_defglo rfon_defcat rfon_defcat_ant defglo_ant reduc_irpp"
foreach var in $liste {
	gen `var'=0
	replace `var' = `var'_foy/(1+marie) if pac~=1
	}
** g. FIN **********

save "$repo\base2${scenario}.dta", replace

****************************************************
*****  2.	Simulation : ne tourne qu'à l'IPP  *****
****************************************************

use "$repo\base2${scenario}.dta", clear

qui	do "$taxipp_encours\3-Programmes\1-cotsoc OF.do"
qui	do "$taxipp_encours\3-Programmes\2-irpp OF.do"
qui do "$progdir\3-revcap.do"
qui do "$progdir\4-prestations.do"
qui do "$progdir\5-isf.do"
qui do "$progdir\6-bouclier_fiscal.do"

save "$repo\base_finale${scenario}.dta", replace


***********************************
*******  3.	Résultats 	 	*******
***********************************
use "$repo\base_finale${scenario}.dta", replace

global var_input_ind "id_foyf id_ind id_conj id_concu age sexe marie mat decl conj pac"
global var_input_travail "cadre public taille_en tva" 
global var_input_logement "zone-loyer_conso_men"
global var_input_revenu "sal_irpp_old"
global var_input $var_input_ind $var_input_travail $var_input_logement $var_input_revenu
global var_output "sal_superbrut css csp sal_brut sal_irpp sal_net "
order $var_input $var_output

save "$repo\base_IPP${scenario}.dta", replace
outsheet using "$repo\base_IPP${scenario}.csv", comma replace
