*************************************************************************************************************************

* OBJECTIF : ce dofile a pour objectif de 
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
	
* PLAN
	* 0. Préambule
	* 1. Création base : création de la base de chaque scénario
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
global nmen= 4 /* Nombre de foyer fiscaux créés */
global nbh_sal = 1607 /* Temps plein ?*/
global rev_max = 100000
global couple 0 /* si on veut faire des couples */
	global marie 1 /* 1 si marié */
	global concubin 0 /* 1 si concubin */
global statut_mat "C" /* Les couples peuvent être mariés*/

global npac 0 /* si on rajouter des pac (inactif pour l'instant) */

global cadre  0
global public 0
global taille_ent 20
global tva 0
	*^^^^^^^^^^^*
	* FIN CHOIX *
	*^^^^^^^^^^^*

* ne pas se tromper : is couple = 0, les individus sont célibataires d'office
if $couple ==0{
	global marie 0 /* 1 si marié */
	global concubin 0 /* 1 si concubin */
	global statut_mat "C"
}
global rev 
forvalues i = 1 /$nmen {
	global rev1 =(`i'-1)*${rev_max}/(${nmen}-1)
	global rev ${rev} ${rev1}
	}
global num : list sizeof global(rev)
*TEST*
if ${num}!=(1+${couple_mar})*${nmen} {
	disp "Il faut qu'il y ait autant de revenus imposables que d'individus créés : " (1+${couple_mar})*${nmen}
}

***********************************
*******  1.	Création base 	*******
***********************************

use "$sources_2006\base.dta", clear

* Objectif : créer X foyers fiscaux (avec le bon nombre d'individu dans chaque)

************
** a. On met d'abord les personnes de référence et leur conjoint (s'il y a lieu)
global N_obs = (1+${couple})*${X} /* on garde X individus si célib / 2*X si couples */
expand ${N_obs} in 1

replace id_indiv = _n

gen id_con =0 /* "con" deviendra concubin ou conjoint selon le scénario choisi */
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
}
** a. FIN **********

************
** b.  Rajouter des enfants 
global N_obs2 = ${npac}*${nmen} +1
expand ${N_obs2} in 1,gen(exp)
replace pac = exp
replace id_ind = _n if pac ==1
* Mettre les enfants dans les foyers fiscaux : A FAIRE (car ce truc ne fonctionne pas)
if pac ==1{
	replace id_foyf = mod(id_ind,${nmen}+1)
}
* Les variables des enfants : (A COMPLETER)
replace nenf= $npac
** b. FIN **********

************
** c.  Variables à modifier
replace nadul=1 if pac !=1
replace age = 38 if pac !=1/* Pour qu'il naisse en 1975 */
replace age = 10 if pac ==1
replace marie = ${marie}
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
	
************
** d.  Calcul des revenus bruts (sal, nonsal, chom, pension) à partir des revenus imposables */
qui	do "$taxipp_encours\3-Programmes\revbrut.do"
** d. FIN **********

************
** e.  Imputation de variables nécessaires pour la suite */
qui do "$dofiles\1e-imputations0_3.do"
replace cadre  = $cadre
replace public = $public 
replace taille_ent = $taille_ent
replace tva = $tva
** e. FIN **********

************
** f.  Il faut gérer certaines variables de revenu financier...
qui	do "$taxipp_encours\3-Programmes\0b_revfin.do"
** f. FIN **********

************
** g. un truc dont a besoin TAXIPP pour tourner : pas d'impact sur les résultats (mais VERIFIER)
egen masse_sal_brut_priv = total(sal_brut*(1-public)*pondv/1000000000)
gen tx_csp_priv_fac =0
replace tx_csp_priv_fac = ${masse_csp_priv_fac_cn}/masse_sal_brut_priv if masse_sal_brut_priv !=0

egen masse_sal_brut_pub=total(sal_brut*public*pondv/1000000000)
gen tx_csp_pub_0 = 0
replace tx_csp_pub_0 = ${masse_csp_pub_cn}/masse_sal_brut_pub if masse_sal_brut_pub!=0

drop *_sim salchom_imp-nbp_seul masse_* smic_h_brut_2006 rfon_irpp 
drop reduc_irpp_foy_tot-loyer_fictif_foy credit_div_foy-reduc_double_dec_foy rpp0_foy-irpp_ds_foy decote_irpp_foy irpp_brut_foy
drop sal_irpp_foy nonsal_irpp_foy pension_irpp_foy chom_irpp_foy pens_alim_rec_foy rfr_irpp_concu
global liste "rfon_defglo rfon_defcat rfon_defcat_ant defglo_ant reduc_irpp"
foreach var in $liste {
	gen `var'=0
	replace `var' = `var'_foy/(1+marie) if pac~=1
	}

** g. FIN **********

save "$sources_2006\base2.dta", replace

*********************************
*****  2.	Simulation 	 	*****
*********************************

use "$sources_2006\base2.dta", clear

qui	do "$taxipp_encours\3-Programmes\1-cotsoc OF.do"
qui	do "$taxipp_encours\3-Programmes\2-irpp OF.do"
qui do "$progdir\3-revcap.do"
qui do "$progdir\4-prestations.do"
qui do "$progdir\5-isf.do"
qui do "$progdir\6-bouclier_fiscal.do"

***********************************
*******  3.	Résultats 	 	*******
***********************************

