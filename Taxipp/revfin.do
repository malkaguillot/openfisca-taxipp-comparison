*IMPUTATIONS DE VARIABLES FINANCIERES
	* Revenus fonciers réels et imputés
	* Imputation des profits non-distribués et calcul des variables de revenus financiers agrégés prélim. :
gen rfin_pv_irpp = rfin_pv_normal_irpp + rfin_pv_options1_irpp + rfin_pv_options2_irpp + rfin_pv_exo_irpp + rfin_pv_pro_irpp + rfin_pv_pro_exo_irpp

drop rfin_pv_irpp_foy 
global liste "rfin_int_cn rfin_div_cn rfin_av_cn rfin_pv_irpp rfin_int_livret rfin_int_pel rfon_cn rfon_fictif_cn"
foreach var in $liste {
	bys id_foyf : egen `var'_foy = total(`var')
	}
	
gen rfin_dist_cn_foy=(rfin_int_cn_foy+rfin_div_cn_foy+rfin_av_cn_foy+rfin_pv_irpp_foy)
gen rfin_nondist_cn_foy=(rfin_div_cn_foy*${masse_profit_nondist_cn}/${masse_rfin_div_cn})
gen is_foy=(rfin_int_cn_foy-rfin_int_livret_foy-rfin_int_pel_foy+rfin_div_cn_foy+rfin_av_cn_foy+rfin_nondist_cn_foy)*${masse_is_cn}/(${masse_rfin_int_cn}-${masse_rfin_int_livret}-${masse_rfin_int_pel}+${masse_rfin_div_cn}+${masse_rfin_av_cn}+${masse_profit_nondist_cn})
replace is_foy=0 if is_foy < 0.1
gen rfin_cn_foy=rfin_dist_cn_foy+rfin_nondist_cn_foy+is_foy
gen yk_cn_foy = rfin_cn_foy+rfon_cn_foy
gen yk_cn = 0
replace yk_cn = yk_cn_foy/(1+marie) if pac~=1

* Calcul du patrimoine par les rendements au niveau individuel et foyer fiscal
gen kfon_cn_foy=rfon_cn_foy/$r_fon_cn 
gen kfin_int_cn_foy=rfin_int_cn_foy/$r_fin_int_cn 
gen kfin_aut_cn_foy=(rfin_cn_foy-rfin_int_cn_foy)/$r_fin_aut_cn
gen kfin_cn_foy=kfin_int_cn_foy+kfin_aut_cn_foy

gen kfin_int_cn=0
replace kfin_int_cn=kfin_int_cn_foy/(1+marie) if pac~=1 
gen kfin_aut_cn=0
replace kfin_aut_cn=kfin_aut_cn_foy/(1+marie) if pac~=1 
gen kfin_cn=0
replace kfin_cn=kfin_cn_foy/(1+marie) if pac~=1 

* Manque nonsal_brut_cn_foy !! (on va le calculer ci-dessous :)
*drop masse_nonsal_brut_2006
egen masse_nonsal_brut_2006 = total(nonsal_brut*pondv/1000000000)
gen nonsal_brut_cn = nonsal_brut*${masse_nonsal_cn}/masse_nonsal_brut_2006
bys id_foyf : egen nonsal_brut_cn_foy = total(nonsal_brut_cn)
	
gen kpro_cn_foy = nonsal_brut_cn_foy*${part_cap_nonsal}/$r_cn 
gen kpro_cn = nonsal_brut_cn*${part_cap_nonsal}/$r_cn 

gen k_cn_foy = kfon_cn_foy + kfin_cn_foy + kpro_cn_foy
gen k_cn = kfon_cn + kfin_cn + kpro_cn

gen actifnetISF = 0

