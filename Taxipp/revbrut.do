* Création des revenus au niveau du foyer fiscal
global liste "sal_irpp nonsal_irpp pension_irpp chom_irpp nonsalexo_irpp rfon_normal_irpp rfon_micro_irpp rfin_div_bar_irpp rfin_int_bar_irpp rfin_av_bar_irpp rfin_div_pl_irpp rfin_int_pl_irpp rfin_av_pl_irpp rfin_pv_normal_irpp rfin_pv_options1_irpp rfin_pv_options2_irpp rfin_pv_exo_irpp rfin_pv_pro_irpp rfin_pv_pro_exo_irpp rfin_pea_exo_irpp ded_epar_ret pens_alim_rec pens_alim_ver"
foreach var in $liste {
	bys id_foyf : egen `var'_foy = total(`var')
	}
*use "$sources_2006\base1.dta", replace
************
		* Secteur privé 
gen sal_brut=0
gen sal_h_brut=0
global pss_h_brut = ${pss_m}/$htp

forvalues cadre = 0/1{
	global C `cadre'
	if $C==0{
		global X = "n" 
		}
	if $C==1{
		global X = "c" 
		}
	replace sal_brut  =sal_irpp/(1-${csg_act_ded}*(1-${csg_abt_0_4})-${s1pr$X})                                                                                        		            	if public==0 & cadre == $C
	replace sal_h_brut=sal_brut/nbh_sal                                                                     		                                                  		         	    	if public==0 & cadre == $C
	replace sal_brut  =(sal_irpp+(${s1pr$X}-${s2pr$X})*${pss_h_brut}*nbh_sal)/(1-${csg_act_ded}*(1-${csg_abt_0_4})-${s2pr$X})	                                                      	    	if sal_h_brut>=${pss_h_brut} & public==0 & cadre == $C
	replace sal_h_brut=sal_brut/nbh_sal                                                                        		                                                  		           	 		if sal_h_brut>=${pss_h_brut} & public==0 & cadre == $C
	replace sal_brut  =(sal_irpp+(${s1pr$X}+3*${s2pr$X}-4*${s3pr$X}+4*(${csg_abt_4_}- ${csg_abt_0_4})*${csg_act_ded})*${pss_h_brut}*nbh_sal)/(1-${csg_act_ded}*(1-${csg_abt_4_})-${s3pr$X}) 	if sal_h_brut>=4*${pss_h_brut} & public==0 & cadre == $C
	replace sal_h_brut=sal_brut/nbh_sal                                                                                                                               		          	  		if sal_h_brut>=4*${pss_h_brut} & public==0 & cadre == $C
	replace sal_brut  =(sal_irpp+(${s1pr$X}+3*${s2pr$X}+4*${s3pr$X}-8*${s4pr$X}+4*(${csg_abt4_}-${csg_abt_0_4})*${csg_act_ded})*${pss_h_brut}*nbh_sal)/(1-${csg_act_ded}*(1-${csg_abt_4_})-${s4pr$X}) if sal_h_brut>=8*${pss_h_brut} & public==0 & cadre == $C
	replace sal_h_brut=sal_brut/nbh_sal      
}			


		* Secteur public 
		
* Hypothèses:
* - On impute des primes moyennes proportionnelles
* - Les fonctionnaires sont considérés comme titulaires de la fonction publique d'État
replace sal_brut= sal_irpp/(1-${csg_act_ded}*(1-${csg_abt_0_4})-${st}*(1-${tx_primes})-(${tx_primes}*${rafp_s}))                               if sal_brut<= 12*${fds_seuil} & public==1  
replace sal_h_brut=sal_brut/nbh_sal                                                                                                            if sal_brut<= 12*${fds_seuil} & public==1 
replace sal_brut= sal_irpp/(1-${csg_act_ded}*(1-${csg_abt_0_4})-${st}*(1-${tx_primes}) - ${fds_s_0_4}-(${tx_primes}*${rafp_s}))                if sal_brut>12*${fds_seuil} & sal_h_brut<=4*${pss_h_brut} & public==1  
replace sal_h_brut=sal_brut/nbh_sal                                                                                                            if sal_brut>12*${fds_seuil} & sal_h_brut<=4*${pss_h_brut} & public==1  
replace sal_brut=(sal_irpp+(${csg_act_ded}* (${csg_abt_4_}- ${csg_abt_0_4}))*4*${pss_h_brut}*nbh_sal)/(1-${csg_act_ded}*(1-${csg_abt_4_})-${st}*(1-${tx_primes})- (${tx_primes}*${rafp_s})-${fds_s_0_4}) if sal_h_brut>4*$pss_h_brut & public==1
replace sal_h_brut=sal_brut/nbh_sal 

			
	* Cas des salaires horaires bruts inférieurs au Smic

* On règle ce problème en diminuant le nombre d'heures travaillées, en faisant l'hypothèse qu'elles sont payées au Smic horaire 
gen smic_h_brut_2006 = 8.15
replace sal_h_brut=0 if sal_h_brut==.
gen inf_smic=(sal_h_brut<smic_h_brut_2006 & sal_h_brut>0)
			
replace nbh_sal = smic_h_brut_2006*sal_h_brut           if inf_smic==1
replace sal_h_brut = smic_h_brut_2006                   if inf_smic==1


* Calcul du revenu brut non-salariés 

gen nonsal_brut   = nonsal_irpp/(1-${csg_act_ded}*(1-${csg_abt_0_4})-${tx_cs_nonsal_0})
gen nonsal_h_brut = nonsal_brut/nbh_nonsal
replace nonsal_brut   = nonsal_irpp/(1-${csg_act_ded}*(1-${csg_abt_0_4})-${tx_cs_nonsal_0})                                                                                  if nonsal_h_brut>$pss_h_brut
replace nonsal_h_brut = nonsal_brut/nbh_nonsal                                                                                                                               if nonsal_h_brut>$pss_h_brut
replace nonsal_brut = (nonsal_irpp+(${tx_cs_nonsal_0}-${tx_cs_nonsal_pss})*${pss_h_brut}*nbh_nonsal)/(1-${csg_act_ded}*(1-${csg_abt_0_4})-${tx_cs_nonsal_pss})               if nonsal_h_brut>=$pss_h_brut & nonsal_brut>0
replace nonsal_h_brut = nonsal_brut/nbh_nonsal                                                                                                                               if nonsal_h_brut>=$pss_h_brut
replace nonsal_brut = (nonsal_irpp+(${tx_cs_nonsal_0}+3*${tx_cs_nonsal_pss}-4*${tx_cs_nonsal_4pss})*${pss_h_brut}*nbh_nonsal)/(1-${csg_act_ded}*(1-${csg_abt_4_})-${tx_cs_nonsal_4pss})  if nonsal_h_brut>=4*$pss_h_brut & nonsal_brut>0
replace nonsal_h_brut = nonsal_brut/nbh_nonsal if nonsal_h_brut>=4*$pss_h_brut
		
replace nonsal_h_brut = 0 if nonsal_h_brut==.

/* 5.b Calcul de l'assiette brute des revenus de remplacement */
******************************************************************
		
* Note: pour calculer les allocations chômage et les pensions brutes, il est nécessaire de connaître le 
*       revenu fiscal de référence (RFR) - ces revenus étant exonérés de CSG et CRDS (SUR DEMANDE EXPRESSE FAITE A L'ADMINISTRATION FISCALE). 
		
	* Calcul du revenu fiscal de référence, du nombre de part du QF et du revenu net d'IRPP
	
do "$dofiles\1d-irpp2006_0_3.do"
	
	* Calcul des pensions brutes
	
/* Avant tout, on a besoin du "rfr_irpp_foy" de l'année N-2, c'est-à-dire 2004 ici. On l'obtient en "vieillissant" rfr_irpp_foy grâce aux masses
   des DF pour les revenus de 2004 et de 2006. On fait de même avec "irpp_net_foy" */
	
*gen rfr_irpp_foy_N2 = rfr_irpp_foy*491.043/527.903
*gen irpp_net_foy_N2 = irpp_net_foy*55.960/56.764
gen rfr_irpp_foy_N2 = rfr_irpp_foy
gen irpp_net_foy_N2 = irpp_net_foy


*Ensuite, calcul des pensions
gen pension_brut     = pension_irpp if pension_irpp==0 | rfr_irpp_foy_N2<=${seuil_exo_tf_th} + 2*(nbp-1)*${seuil_exo_tf_th_demipart}
replace pension_brut = pension_irpp/(1-${csg_pens_red}) if rfr_irpp_foy_N2>${seuil_exo_tf_th}+2*(nbp-1)*${seuil_exo_tf_th_demipart} & irpp_net_foy_N2<=0
replace pension_brut = pension_irpp/(1-${csg_pens_ded}) if rfr_irpp_foy_N2>${seuil_exo_tf_th}+2*(nbp-1)*${seuil_exo_tf_th_demipart} & irpp_net_foy_N2>0
			
	* Calcul des allocations chômage brutes

*** Proposition ***
gen csg_tout = (irpp_net_foy_N2 > 0)
gen csg_part = (irpp_net_foy_N2 <= 0) & (rfr_irpp_foy_N2 > ${seuil_exo_tf_th}+2*(nbp-1)*${seuil_exo_tf_th_demipart})
gen csg_exo  = (chom_irpp==0) | ((irpp_net_foy_N2 <= 0) & (rfr_irpp_foy_N2 <= ${seuil_exo_tf_th}+2*(nbp-1)*${seuil_exo_tf_th_demipart}))

gen chom_brut     = chom_irpp 										if csg_exo == 1
replace chom_brut = chom_irpp/(1-${csg_cho_ded}*(1-${csg_abt_0_4})) if (csg_tout == 1 | csg_part == 1) 
replace chom_brut = chom_irpp/(1-${csg_cho_ded})					if (csg_tout == 1 | csg_part == 1) & chom_brut > 4*$pss
drop csg_tout csg_part csg_exo
***
/*	
* Note: on ne prend pas en compte la condition sur revenu activité + chômage >= smic brut après déduction CSG.
gen chom_brut     = chom_irpp if chom_irpp==0 | rfr_irpp_foy_N2 <= ${seuil_exo_tf_th}+2*(nbp-1)*${seuil_exo_tf_th_demipart}
replace chom_brut = chom_irpp/(1-${csg_cho_ded}*(1-${csg_abt_0_4})) if rfr_irpp_foy_N2>${seuil_exo_tf_th}+2*(nbp-1)*${seuil_exo_tf_th_demipart} & irpp_net_foy_N2<=0
replace chom_brut = chom_irpp/(1-${csg_cho_ded}*(1-${csg_abt_0_4})) if rfr_irpp_foy_N2>${seuil_exo_tf_th}+2*(nbp-1)*${seuil_exo_tf_th_demipart} & irpp_net_foy_N2>0
*/
drop inf_smic 
rename sal_irpp sal_irpp_old
rename pension_irpp pension_irpp_old
rename chom_irpp chom_irpp_old
