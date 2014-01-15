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
	*- élargir le programme pour prendre en compte d'autres types de revenus (chômage, retraite, capital...)
	*- comprendre pourquoi on ne retombe pas sur sal_irpp pour le public (d'Etat : seule prise en compte dans TAXIPP)
	*- loyer
	*- ISF
	*- mettre que les pacs puissent avoir un revenu
	*- travailler sur les non salariés ? (attention checker nbh nbh_sal nbh_nonsal statprof) & les tempspartiels ?
	
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
qui do "P:\TAXIPP\TAXIPP 0.3\4-Analyses\Test OF\3-Programmes\chemins.do"

global annee_sim = 2008
global annee = ${annee_sim}

* Appel des paramètres : paramètres législatifs stockés pour l'année 2011 sous forme de global
qui do "$progdir\0_appel_parametres0_3.do"

	*^^^^^^^*
	* CHOIX *
	*^^^^^^^*
global scenario "_couple_concubins_enfant_activite"

global nmen =4
global nbh_sal = 1820 /* 1607 Temps plein ?*/
global rev_max = 100000
global part_rev = 0.6 /* \in [0,1] : part du revenu du FF qui va au déclarant ou à con1*/

global statmarit 1 /* "M":marié ; "C":célibataire ; "V": veuf ; "D": divorcé */
global couple 1

global npac 6 /* si on rajouter des pac */
global age_enf "-1 10" /* Faire que dim(age_enf) = npac */
/*si enfant à naître : -1 */

global activite_D 0 /* [u'Actif occupé',  u'Chômeur', u'Étudiant, élève',u'Retraité', u'Autre inactif']), default = 4))*/
global cadre_D  1
global public_D 0
global taille_ent_D 20
global tva_D 1

global activite_C 0 /* [u'Actif occupé',  u'Chômeur', u'Étudiant, élève',u'Retraité', u'Autre inactif']), default = 4))*/
global cadre_C  0
global public_C 0
global taille_ent_C 20 
global tva_C 0

* Revenus du capital
global f2dc 0
global f2tr 0
global f3vg 0
global f4ba 0

global ISF 0 /*Patrimoine imposable à l'ISF */

global caseT 1
global caseEKL 0
global loyer_mensuel_menage 1000 /*Mensuel du ménage*/
global npac_C 1 /* nb enfants du ménage qui appartienne à con2 */


	*^^^^^^^^^^^*
	* FIN CHOIX *
	*^^^^^^^^^^^*
if ${statmarit} == 1{
	global mat ="M" 
	}
if ${statmarit} == 2{
	global mat ="C" 
	}	
if ${statmarit} == 3{
	global mat ="V" 
	}
if ${statmarit} == 4{
	global mat ="D" 
	}
if ${statmarit} == 1{ 
	global mat ="P"  /* pacsé*/
	}	
if ${statmarit} == 3{
	global mat ="V" /* jeune veuf */
	}

	if "$mat" !="M" & ${couple}== 0{
	global marie 0 
	global concubin 0 
	}
if "$mat" =="M"{
	global marie 1 
	global couple 1 /* Pour si on s'est trompé dans le choix : marié => on est en couple */ 
	global concubin 0 
	}
if "$mat" !="M" & ${couple}==1{
	global marie 0 
	global concubin 1 
	}

global rev 
forvalues i = 1 /$nmen {
	global rev1 =(`i'-1)*${rev_max}/(${nmen}-1)
	global rev ${rev} ${rev1}
	}
global num : list sizeof global(rev)
*TEST*
*if ${num}!=(1+${couple})*${nmen} {
*	disp "Il faut qu'il y ait autant de revenus imposables que d'individus créés : " (1+${couple})*${nmen}
*}
if $npac == 0{
	global caseT 0
}
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

gen id_concu = 0
gen id_conj =0
gen id_men =0
gen con1 =0
gen con2 =0
*gen id_fo_concu = 0

if $marie == 1{
	replace id_conj = _n-1 if mod(id_indiv,2)==0 
	replace id_conj = _n+1 if mod(id_indiv,2)==1
	replace decl=1 if mod(id_indiv,2)==1 
	replace conj=1 if mod(id_indiv,2)==0 
	replace id_foy =(_n+1)/2
	replace id_foy =(_n)/2 if mod(id_indiv,2)==0
	replace id_men = id_foy
	replace couple =1
	replace marie =1
}
if $concubin == 1{
	replace couple =1
	replace concu = 1
	replace id_concu = _n-1 if mod(id_indiv,2)==0 
	replace con1 = (mod(id_indiv,2)==1 )
	replace con2 = (mod(id_indiv,2)==0 )
	replace id_concu  = _n+1 if mod(id_indiv,2)==1
*	replace id_fo_concu = id_concu
	replace id_foyf =_n
	replace id_men =(_n+1)/2
	replace id_men =(_n)/2 if mod(id_indiv,2)==0
	replace decl=1
}
if ${concubin}==0 & ${marie} == 0{
	replace couple = 0
	replace id_foy = _n
	replace decl = 1
	replace id_men = id_foyf
}
replace age = 38
replace age_conj = 38

if ${couple}==0 & pac>0{ /* Pour forcer caseT = 1 si on est seul adulte avec enfant(s) */
	global caseT 1
} 
gen mat = "$mat"
replace n_foy_men = 1+${concubin}
replace men = con1 + decl*${marie} if pac == 0
replace foy = men

** a. FIN **********

************
** b.  Rajouter des enfants et les ranger dans les ménages ^puis on les partage entre les foyers fiscaux
global N_enf = ${npac}*${nmen}
expand ${N_enf}+1 in 1,gen(exp)
replace pac = exp
drop exp

foreach var of varlist concu conj decl conj id* concu couple marie age con* men foy{
	replace `var' = 0 if pac ==1
}
replace id_ind = _n if pac ==1

gen id_men_pac = .
replace id_men_pac = _n - ${nmen}*(1+${couple})  if pac ==1
forvalues i =2/$npac{
	replace id_men_pac = _n -${nmen}*(`i'+${couple}) if id_men_pac > ${nmen}  & pac == 1
	}
replace id_men = id_men_pac if pac ==1
byso id_men_pac: gen pac_sum_men = sum(pac)
drop id_men_pac

* Mettre les enfants dans le FF de leurs parents
gen id_foy_pac = .

if ${marie}==1 | ${couple}==0{
	replace id_foy_pac = id_men if pac ==1
}
if ${concubin}==1{
	replace id_foy_pac = id_men*2-1 if pac ==1 & pac_sum_men <=$npac - $npac_C
	replace id_foy_pac = id_men*2 if pac ==1 & pac_sum_men >$npac - $npac_C
}

replace id_foyf = id_foy_pac if pac ==1
so id_foyf id_ind
drop id_foy_pac

* nenf_concu : les enfants du ménage qui sont ceux du concubin
replace nenf_concu = ${npac_C} if con1 ==1
replace nenf_concu = ${npac} - ${npac_C} if con2 ==1

*Age
byso id_foyf : gen pac_sum = sum(pac) if pac==1
replace pac_sum = 0 if pac ==0
global num_age : list sizeof global(age_enf)

gen age_enf = 0
forvalues age = 1/$num_age{
	global A : word `age' of $age_enf
	replace age = ${A} if pac_sum ==  `age' 
	replace age_enf = ${A} if pac_sum ==  `age' 
}
drop npers_men nadul nenf nenfmaj nenfnaiss nenf02 nenf35 nenf610 nenf1113 nenf1415 nenf1617 nenfmaj1819 nenfmaj20 nenfmaj21plus pac_sum
byso id_foy :  egen nenfnaiss = total(age<0) 
byso id_foy :  egen nenf02 = total(age>=0 & age < 3)
byso id_foy :  egen nenf35 = total(age >= 3 & age < 6)
byso id_foy :  egen nenf610 = total(age>=6 & age < 11)
byso id_foy :  egen nenf1113 = total(age >=11 & age < 14)
byso id_foy :  egen nenf1415 = total(age >=14 & age < 16)
byso id_foy :  egen nenf1617 = total(age >=16 & age < 18)
byso id_foy :  egen nenfmaj1819 = total(age_enf >=18 & age_enf < 20)
byso id_foy :  egen nenfmaj20 = total(age_enf == 20) 
byso id_foy :  egen nenfmaj21plus = total(age_enf > 20)
byso id_foy : egen nenfmaj = total(age>17)
byso id_foy : egen nenf = total(age<18)

byso id_foy : egen nadul = total(age >= 18) 
replace npers = nadul + nenf
byso id_men : egen npers_men = total(id_ind>0)
replace seul_enf_irpp = $caseT
replace seul_enfmaj_irpp = $caseEKL
** b. FIN **********

*gen nbp = 1+ ${marie} + .5*(nenf==1) + (.5+.5)*(nenf==2) + (.5+.5+ 1*(nenf-2))*(nenf>=3)/* Nombre de part du FF */

************
** c.  Variables à modifier

*replace id_conj = _n-1 if mod(id_indiv,2)==0 
*replace id_conj = _n+1 if mod(id_indiv,2)==1

gen cadre  = ${cadre_C} if (conj == 1 | con2 == 1)
replace cadre  = ${cadre_D} if (decl == 1 & couple == 0) | (decl == 1 & marie == 1) | con1 == 1

replace public  = ${public_C} if (conj == 1 | con2 == 1)
replace public  = ${public_D} if (decl == 1 & couple == 0) | (decl == 1 & marie == 1) | con1 == 1

replace mat = "C" if pac == 1
bys id_foyf: replace num_indf=_n 

* Revenu du travail

replace nbh = cond(${activite_C}!=0,0,${nbh_sal}) if con2 == 1 | conj == 1
replace nbh = cond(${activite_D}!=0,0,${nbh_sal}) if (decl == 1 & couple == 0) | (decl == 1 & marie == 1) | con1 == 1
replace nbh_sal = nbh

gen rev_temp = 0 
forvalues r = 1/$num{
	global R : word `r' of $rev
	gen id_foy_`r'=1 if id_foy == `r' 
	gen id_men_`r'=1 if id_men == `r' 
	replace rev_temp = ${part_rev}*${R} if id_men_`r'==1 &  con1 == 1 & concu ==1
	replace rev_temp = (1-${part_rev})*${R} if id_men_`r'==1 & con2 == 1 & concu ==1
	replace rev_temp = ${part_rev}*${R} if id_foy_`r'==1 & decl == 1 & marie == 1
	replace rev_temp = (1-${part_rev})*${R} if id_foy_`r'==1 & conj == 1 & marie == 1
	replace rev_temp = ${R} if id_foy_`r'==1 & couple == 0
	drop id_foy_`r'
	drop id_men_`r'
	}
replace sal_irpp = rev_temp 	if ${activite_C} == 0 & (conj == 1 | con2 == 1) /* Actif */
replace chom_irpp = rev_temp 	if ${activite_C} == 1 & (conj == 1 | con2 == 1) /* Chômeur */
replace pension_irpp = rev_temp if ${activite_C} == 3 & (conj == 1 | con2 == 1) /* Retraité */

replace sal_irpp = rev_temp 	if ${activite_D} == 0 & ((decl == 1 & couple == 0) | (decl == 1 & marie == 1) | con1 == 1) /* Actif */
replace chom_irpp = rev_temp 	if ${activite_D} == 1 & ((decl == 1 & couple == 0) | (decl == 1 & marie == 1) | con1 == 1) /* Chômeur */
replace pension_irpp = rev_temp if ${activite_D} == 3 & ((decl == 1 & couple == 0) | (decl == 1 & marie == 1) | con1 == 1) /* Retraité */
drop rev_temp

	* Revenu du capital
replace rfin_div_bar_irpp = ${f2dc} /*+  ${f2fu} */
replace rfin_int_bar_irpp = /*${f2ts} + ${f2go} +*/ ${f2tr}
replace rfin_pv_normal_irpp = ${f3vg}
replace rfon_normal_irpp = ${f4ba}
gen actifnetISF = 0

so id_foyf
sort id_indiv
order id_indiv id_foyf id_conj id_concu couple pac decl conj mat marie sal_irpp
** c. FIN **********

* Logement
replace loyer_verse = ${loyer_mensuel_menage}*12/(1+${couple}) if pac ==0
replace loyer_verse_men = ${loyer_mensuel_menage}*12
replace loyer_conso = loyer_verse + loyer_fictif
replace loyer_conso_men = loyer_verse_men + loyer_fictif_men
	
save "$dofiles\base1${scenario}.dta", replace
use "$dofiles\base1${scenario}.dta", replace

************
** d.  Calcul des revenus bruts (sal, nonsal, chom, pension) à partir des revenus imposables */
global pss ${pss_m}*12
do "$dofiles\revbrut.do"
** d. FIN **********
************
** e.  Imputation de variables nécessaires pour la suite */
qui do "$dofiles\imputations.do"
gen taille_ent = ${taille_ent_C} if  (conj == 1 | con2 == 1)
replace taille_ent = ${taille_ent_D} if ((decl == 1 & couple == 0) | (decl == 1 & marie == 1) | con1 == 1)
gen tva = ${tva_C} if  (conj == 1 | con2 == 1)
replace tva = ${tva_D} if ((decl == 1 & couple == 0) | (decl == 1 & marie == 1) | con1 == 1)
** e. FIN **********

************
** f.  Il faut gérer certaines variables de revenu financier...
qui	do "$dofiles\revfin.do"
** f. FIN **********

************
** g. un truc dont a besoin TAXIPP pour tourner : pas d'impact sur les résultats (car pas pris en compte dans OF?)
gen tx_csp_priv_fac =0
gen tx_csp_pub_0 = 0


* Supprimer les variables créées mais qui vont être recalculées
cap drop rpp1_foy irpp_bar1_foy irpp_bar10_foy reduc_qf1_foy reduc_qf_plaf1_foy irpp_ds1_foy decote_irpp1_foy irpp_brut1_foy nbp02 nbp2 rimp2_foy rpp2_foy irpp_bar2_foy irpp_bar20_foy reduc_qf2_foy reduc_qf_plaf2_foy irpp_ds2_foy decote_irpp2_foy irpp_brut2_foy
drop *_sim salchom_imp-nbp_seul masse_* smic_h_brut_2006 rfon_irpp 
drop reduc_irpp_foy_tot-loyer_fictif_foy credit_div_foy-reduc_double_dec_foy rpp0_foy-irpp_ds_foy decote_irpp_foy irpp_brut_foy
drop sal_irpp_foy nonsal_irpp_foy pension_irpp_foy chom_irpp_foy pens_alim_rec_foy rfr_irpp_concu
** g. FIN **********

gen dic_scenar= "$dic_scenar"
save "$repo\base_IPP_input_${scenario}.dta", replace

****************************************************
*****  2.	Simulation : ne tourne qu'à l'IPP  *****
****************************************************

use "$repo\base_IPP_input_${scenario}.dta", clear
cap drop dic_scenar

qui	do "$taxipp_encours\3-Programmes\1-cotsoc OF.do"
qui	do "$taxipp_encours\3-Programmes\2-irpp OF.do"
qui do "$progdir\3-revcap.do"
qui	do "$taxipp_encours\3-Programmes\4-prestations OF.do"
qui do "$progdir\5-isf.do"
qui do "$taxipp_encours\3-Programmes\6-bouclier_fiscal OF.do"

drop id_indiv-loyer_verse_men reduc_ds-reduc_irpp 

save "$repo\base_IPP_output_${scenario}.dta", replace
