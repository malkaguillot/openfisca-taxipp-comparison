/************************************************************************************************/
* TAXIPP 0.3                                                                                     *
*                                                                                                *
* Imputation de variables nécessaires pour calculer le programme de calcul d'impôts              *
*                                                                                                *
*                                                                                                *
* Quentin Lafféter 03/2012                                                                       *
/************************************************************************************************/

	/*** 1. Création de la variable "cadre" */

	/*** 2. Création de la variable "tva" */


	/*** 3. Création de la variable taille_ent */



/*** 4. Création de variables imputées pour certains revenus du capital */

	* Revenus fonciers réels et imputés
egen masse_loyer_fictif_sim=total(loyer_fictif*pondv/1000000000)
egen masse_loyer_reel_sim=total(loyer_verse*bail_pers_phys_men*pondv/1000000000)
gen masse_loyer_sim=masse_loyer_fictif_sim+masse_loyer_reel_sim
gen masse_rfon_fictif = masse_loyer_fictif_sim+0.5*(${masse_loyer_brut_cn}-masse_loyer_sim)-${masse_rfon_ccf_cn}*(masse_loyer_fictif_sim+0.5*(${masse_loyer_brut_cn}-masse_loyer_sim))/${masse_loyer_brut_cn}-${masse_rfon_int_cn}
gen masse_rfon_reel = masse_loyer_reel_sim+0.5*(${masse_loyer_brut_cn}-masse_loyer_sim)-${masse_rfon_ccf_cn}*(masse_loyer_reel_sim+0.5*(${masse_loyer_brut_cn}-masse_loyer_sim))/${masse_loyer_brut_cn}

gen rfon_fictif_cn = 0
replace rfon_fictif_cn = loyer_fictif*masse_rfon_fictif/masse_loyer_fictif_sim
	
gen rfon_reel_cn=0 
gen rfon_irpp = rfon_normal_irpp + (1-${abt_micro_fon})*rfon_micro_irpp
replace rfon_reel_cn=rfon_irpp*masse_rfon_reel/${masse_rfon_irpp}
egen masse_rfon_reel_cn_temp = total(rfon_reel_cn*pondv/1000000000)
replace rfon_reel_cn=rfon_reel_cn*masse_rfon_reel/masse_rfon_reel_cn_temp

gen rfon_cn=rfon_fictif_cn+rfon_reel_cn

	* Calcul des revenus financiers sur les masses compta nat ou CSG
egen masse_rfin_livret_sim=total(rfin_int_livret_dec*pondv/1000000000)
egen masse_rfin_pel_sim=total(rfin_int_pel_dec*pondv/1000000000)
egen masse_rfin_pea_sim=total(rfin_div_pea_dec*pondv/1000000000)
egen masse_rfin_av_sim=total(rfin_av_dec*pondv/1000000000)
				
global liste "rfin_int_livret rfin_int_pel_csg rfin_int_pel rfin_int_pl rfin_int_csg rfin_int_cn" 
foreach var in $liste {
	gen `var'=0
	}

replace rfin_int_livret=rfin_int_livret_dec*${masse_rfin_int_livret}/masse_rfin_livret_sim
replace rfin_int_pel_csg=rfin_int_pel_dec*${masse_rfin_int_pel_csg}/masse_rfin_pel_sim
replace rfin_int_pel=rfin_int_pel_csg*${masse_rfin_int_pel}/${masse_rfin_int_pel_csg}
replace rfin_int_pl=rfin_int_pl_irpp*(${masse_rfin_pl}-${masse_rfin_div_pl_irpp}-${masse_rfin_av_pl_irpp})/${masse_rfin_int_pl_irpp}
replace rfin_int_csg=rfin_int_pel_csg+rfin_int_pl+rfin_int_bar_irpp
replace rfin_int_cn=rfin_int_livret+rfin_int_pel+rfin_int_pl+rfin_int_bar_irpp 

	* Calcul et calage des dividendes sur les masses comptanat ou CSG
global liste "rfin_div_pea_csg rfin_div_pea_cn rfin_div_csg rfin_div_cn"
foreach var in $liste {
	gen `var'=0
	}
gen rfin_div_pea_residu = rfin_div_pea_dec*(${masse_rfin_div_pea_csg}-${masse_rfin_pea_exo_irpp})/masse_rfin_pea_sim
replace rfin_div_pea_csg=rfin_pea_exo_irpp+rfin_div_pea_residu
replace rfin_div_pea_cn=rfin_div_pea_csg*${masse_rfin_div_pea}/${masse_rfin_div_pea_csg}
replace rfin_div_csg=rfin_div_pea_csg+rfin_div_bar_irpp+rfin_div_pl_irpp
gen rfin_div_imp_cn = (rfin_div_bar_irpp+rfin_div_pl_irpp)*(${masse_rfin_div_cn}-${masse_rfin_div_pea})/(${masse_rfin_div_bar_irpp}+${masse_rfin_div_pl_irpp})
replace rfin_div_cn=rfin_div_pea_cn+rfin_div_imp_cn

	* Calcul et calage d'assurances-vie sur les masses comptanat ou CSG
global liste "rfin_av_residu rfin_av_csg rfin_av_cn"
	foreach var in $liste {
	gen `var'=0
	}

replace rfin_av_residu=rfin_av_dec*(${masse_rfin_av_csg}-${masse_rfin_av_bar_irpp}-${masse_rfin_av_pl_irpp})/masse_rfin_av_sim
replace rfin_av_csg=rfin_av_bar_irpp+rfin_av_pl_irpp+rfin_av_residu
replace rfin_av_cn=rfin_av_csg*${masse_rfin_av_cn}/$masse_rfin_av_csg
