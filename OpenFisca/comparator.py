# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014 OpenFisca Team
# https://github.com/openfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import logging
import os
import pdb
import subprocess
import sys

from numpy import logical_not as not_, array, zeros
from pandas import read_stata, ExcelFile, DataFrame

import openfisca_france
from openfisca_core import model
from openfisca_core.simulations import SurveySimulation
openfisca_france.init_country()

from CONFIG import paths


class Comparison_cases(object):
    """
    La classe qui permet de lancer les comparaisons par cas-types
    Structure de classe n'est peut-être pas nécessaire 
    """
    
    def __init__(self, datesim, choix_by_scenario):
        # Paramètres initiaux
        self.datesim = datesim
        self.dic_scenar = None
        self.param_scenario = choix_by_scenario
        self.paths = paths

        # Actualisés au cours de la comparaison
        self.ipp2of_input_variables = None
        self.ipp2of_output_variables = None
        
        self.simulation = None
        
    def work_on_param(self):
        paths = self.paths
        paths['dta_input']  = paths['dta_input'] + self.param_scenario['scenario'] + ".dta"
        paths['dta_output']  = paths['dta_output'] + self.param_scenario['scenario'] + ".dta"
        self.paths = paths
        
        def _dic_param_ini(dic):
            dic_param_ini = {}
            for k, v in dic.items():
                dic_param_ini[k] = v
            return dic_param_ini
        
        def _default_param(dic):
            # Activité : [0'Actif occupé',  1'Chômeur', 2'Étudiant, élève', 3'Retraité', 4'Autre inactif']), default = 4)
            # indicatrices : cadre, public, caseT (parent isolé)
            dic_default = { 
                           'scenario' : 'celib', 'nmen': 3, 'option' : 'sali',
                           'nb_enf' : 0, 'nb_enf_conj': 0, 'age_enf': -10,  'rev_max': 100000, 'part_rev': 1, 'loyer_mensuel_menage': 1000, 
                           'activite': 0, 'cadre': 0, 'public' : 0, 'nbh_sal': 151.67*12, 'taille_ent' : 5, 'tva_ent' : 0, 'nbj_nonsal': 0,
                           'activite_C': 0, 'cadre_C': 0, 'public_C' : 0, 'nbh_sal_C': 151.67*12, 'taille_ent_C' : 5, 'tva_ent_C' : 0, 'nbj_nonsal_C': 0,
                           'f2dc' : 0, 'f2tr': 0, 'f3vg':0, 'f4ba':0, 'ISF' : 0, 'caseT': 0, 'caseEKL' : 0
                           }
            
            for key in dic_default.keys():                     
                if key not in dic.keys() :
                    dic[key] = dic_default[key]
            return dic
        
        def _civilstate(dic):
            if dic['scenario'] == 'concubin':
                dic['couple'] = 1
                dic['statmarit'] = 2 
                
            elif dic['scenario'] == 'marie':
                dic['couple'] = 1
                dic['statmarit'] = 1 
        
            elif dic['scenario'] == 'celib':
                dic['couple'] = 0
                dic['statmarit'] = 2
            else :
                print "Scénario demandé non pris en compte"
                pdb.set_trace()
            return dic
        
        def _enf(dic):
            dic['npac'] = dic.pop('nb_enf')
            dic['npac_C'] = dic.pop('nb_enf_conj')
            if dic['npac'] !=0:
                try: 
                    assert dic['npac'] == len(dic['age_enf'])
                except:
                    print "Problème dans la déclaration des âges des enfants"
                    dic['age_enf'] = zeros(1)*dic['npac'] # TODO: check
                
                dic['age_enf'] = str(dic['age_enf'])[1:-1].replace(',', ' ') # To stata

            return dic
            
        dic = self.param_scenario
        self.dic_scenar = _dic_param_ini(dic)
        dic['annee_sim'] = self.datesim
        dic = _default_param(dic)
        dic = _civilstate(dic)
        dic = _enf(dic)
        self.param_scenario = dic

    def def_ipp2of_dic(self):
        ''' 
        Création du dictionnaire dont les clefs sont les noms des variables IPP
        et les arguments ceux des variables OF 
        '''
        def _dic_corresp(onglet):
            names = ExcelFile('correspondances_variables.xlsx').parse(onglet)
            names = array(names.loc[names['equivalence'].isin([1,5,8]), ['var_TAXIPP', 'var_OF']])
            dic = {}
            for i in range(len(names)) :
                dic[names[i,0]] = names[i,1]
            return dic
            
        self.ipp2of_input_variables = _dic_corresp('input')
        self.ipp2of_output_variables =  _dic_corresp('output')
         
    def run_TaxIPP(self):
        do_in = self.paths['do_in']
        do_out = self.paths['do_out']
        len_preamb = 40
        dic = self.param_scenario
        dic_scenar = self.dic_scenar
        
        def _insert_param_dofile(dic, dic_scenar, do_in, do_out, len_preamb):
            lines = open(do_in).readlines()
            head = lines[:len_preamb +1]
            lines = lines[- (len(lines) - len_preamb):]
            with open(do_out, "w") as f:
                f.seek(0)
                # La première ligne du .do contiendra un commentaire contenant le dictionnaire des paramètres de la simulation
                #to_write = "**" +  str(dic) + "\n"
                #f.write(to_write)
                
                # Préambule
                f.writelines(head)
                
                # Repo pour stata +param_scenario
                to_write = 'global repo ' + paths['repo_to_stata'] + "\n"
                f.write(to_write)
                to_write = "global dic_scenar " + '"' + str(dic_scenar)  + '"' +"\n"
                f.write(to_write)
                
                # Insertions des paramètres
                for k, v in dic.items():
                    to_write = 'global ' + k +  " "+ str(v) + "\n"
                    f.write(to_write)
                    
                # Corps du dofile
                f.writelines(lines)
                f.close()
         
        _insert_param_dofile(dic, dic_scenar, do_in, do_out, len_preamb)
        subprocess.call([self.paths['stata'],  "/e", "do", self.paths['do_out']], shell=True)

    def run_OF(self):
        '''
        Lance le calculs sur OF à partir des cas-types issues de TaxIPP
        input : base .dta issue de l'étape précédente
        '''
        dta_input = self.paths['dta_input']
        dic = self.dic_scenar 

        def _test_of_dta(dta_input, dic):
            ''' Cette fonction teste que la table .dta trouvée 
            correspond au bon scénario '''
            data = read_stata(dta_input)
            dic_dta =  data.loc[0,'dic_scenar']
            if str(dic) != str(dic_dta) :
                print "La base .dta permettant de lancer la simulation OF est absente "
                print "La base s'en rapprochant le plus a été construite avec les paramètres : ", dic_dta
                pdb.set_trace()
            else :
                data = data.drop('dic_scenar', 1).sort(['id_foyf', 'id_indiv'], ascending=[True, False])
            return data
        
        def _adaptation_var(data, dic_var):
            
            def _qui(data, entity):
                qui = "qui" + entity
                id = "id" + entity
                data[qui] = 2
                data.loc[data['decl'] == 1, qui] = 0
                data.loc[data['conj'] == 1, qui] = 1
                if entity == "men" :
                     data.loc[data['con2'] == 1, qui] = 1
                j=2
                while any(data.duplicated([qui, id])):
                    data.loc[data.duplicated([qui, id]), qui] = j+1
                    j += 1
                return data[qui]
            
            def _so(data):
                data["so"] = 0
                data.loc[data['proprio_empr'] == 1, 'so'] = 1
                data.loc[data['proprio'] == 1, 'so'] = 2
                data.loc[data['locat'] == 1, 'so'] = 4
                data.loc[data['loge'] == 1, 'so'] = 6
                return data['so']
            
            def _compl(var):
                var = 1- var
                var = var.astype(int)
                return var
            
            def _count_by_entity(data, var, entity, bornes):
                ''' Compte le nombre de 'var compris entre les 'bornes' au sein de l''entity' '''
                id = 'id' +entity
                qui = 'qui' + entity
                data.index = data[id]
                cond = (bornes[0] <= data[var]) & (data[var]<= bornes[1]) & (data[qui]>1)
                col = DataFrame(data.loc[cond, :].groupby(id).size(), index = data.index).fillna(0)
                col.reset_index()
                return col
                
            def _count_enf(data):
                data["f7ea"] = _count_by_entity(data,'age', 'foy', [11,14]) #nb enfants ff au collège (11-14) 
                data["f7ec"] = _count_by_entity(data,'age', 'foy', [15,17]) # #nb enfants ff au lycée  15-17
                data["f7ef"] = _count_by_entity(data,'age', 'foy', [18,99])  #nb enfants ff enseignement sup >17
                data = data.drop(["nenf1113", "nenf1415", "nenf1617", "nenfmaj1819", "nenfmaj20", "nenfmaj21plus", "nenfnaiss", "nenf02",  "nenf35",  "nenf610"], axis = 1)
                data.index = range(len(data))
                return data
            
            def _workstate(data):
                # TODO: titc should be filled in to deal with civil servant  
                data['chpub'] = 0
                data.loc[data['public'] == 1, 'chpub'] = 1
                data.loc[data['public'] == 0, 'chpub' ] = 6
                # Activité : [0'Actif occupé',  1'Chômeur', 2'Étudiant, élève', 3'Retraité', 4'Autre inactif']), default = 4)
                # act5 : [0"Salarié",1"Indépendant",2"Chômeur",3"Retraité",4"Inactif"]
                data['act5'] = 0
                data.loc[(data['activite'] == 0) & (data['stat_prof'] == 1), 'act5'] = 1
                data.loc[data['activite'] == 1, 'act5'] = 2
                data.loc[data['activite'] == 3, 'act5'] = 3
                data.loc[data['activite'].isin([2,4]), 'act5'] = 4
                data['statut']  = 8
                data.loc[data['public'] == 1, 'statut'] = 11
                # [0"Non renseigné/non pertinent",1"Exonéré",2"Taux réduit",3"Taux plein"]
                data['csg_rempl'] = 3
                data.loc[data['csg_exo']==1,'csg_rempl'] = 1 
                data.loc[data['csg_part']==1,'csg_rempl'] = 2 
                data = data.drop(['csg_tout', 'csg_exo', 'csg_part'], axis=1)
                # Variables donnant le nombre de salariés
                return data
            
            def _var_to_ppe(data):
                data['ppe_du_sa'] = 0
                data.loc[data['stat_prof'] == 0, 'ppe_du_sa'] = data.loc[data['stat_prof'] == 0, 'nbh']
                data['ppe_du_ns'] = 0
                data.loc[data['stat_prof'] == 1, 'ppe_du_ns'] = data.loc[data['stat_prof'] == 1, 'nbj']
                
                data['ppe_tp_sa'] = 0
                data.loc[(data['stat_prof'] == 0) & (data['nbh'] >= 151.67*12), 'ppe_tp_sa'] = 1
                data['ppe_tp_ns'] = 0
                data.loc[(data['stat_prof'] == 1) & (data['nbj'] >= 360), 'ppe_tp_ns'] = 1
                return data
                
            data.rename(columns= dic_var, inplace=True)
                
            data["agem"] = 12*data["age"]
            data['quifoy'] = _qui(data, 'foy')
            data['quimen'] = _qui(data, 'men')
            data["idfam"] = data["idmen"]
            data["quifam"] = data['quimen']

            #print data[['idfoy','idmen', 'quimen','quifoy', 'decl', 'conj', 'con2']].to_string()
            data['so'] = _so(data)
            data = _count_enf(data)
            data = _workstate(data)
            data["caseN"] = _compl(data["caseN"])
            data = _var_to_ppe(data)
            doubt = ["rfin"]
            
            not_in_OF = [ "p1", "nbh", "nbh_sal", "loge_proprio",  "loge_locat",  "loge_autr", "loyer_fictif",  "loyer_verse",  "loyer_marche", "pens_alim_ver_foy", "sal_brut",  "sal_h_brut",
                         "bail_prive",  "bail_pers_phys",  "loyer_conso",  "proprio_men",  "locat_men", "loge_men",  "proprio_empr_men", "loyer_fictif_men", 
                         "bail_prive_men",  "bail_pers_phys_men", "loyer_marche_men", "loyer_conso_men",
                          "ba_irpp",  "bic_irpp",  "bnc_irpp",  "nonsalexo_irpp", "nonsal_brut_cn", "nonsal_brut_cn_foy", "nonsal_brut", "nonsal_h_brut"] # variables non-salariés
            other_vars_to_drop = ["couple", "decl", "conj", "pac", "proprio_empr", "proprio", "locat", "nonsal_irpp", "nadul", 
                          "loge", "marie", "change", "pondv", "concu", "cohab", "nenf_concu", "num_indf", "npers", "age_conj", "n_foy_men", "public"]
            vars_to_drop = [var for var in (other_vars_to_drop + not_in_OF) if var in data.columns]            
            data = data.drop(vars_to_drop, axis=1)
            data.rename(columns={"id_conj" : "conj"}, inplace = True)
            return data
        
        data_IPP = _test_of_dta(dta_input, dic)
        var_input = self.ipp2of_input_variables
        if self.param_scenario['option'] == 'salbrut':
            del var_input['sal_irpp_old']
            var_input['sal_brut'] = 'salbrut'
        openfisca_survey =  _adaptation_var(data_IPP, var_input)
        openfisca_survey = openfisca_survey.fillna(0)#.sort(['idfoy','noi'])
        
 #       if self.param_scenario['option'] == 'salbrut':
 #           openfisca_france.init_country(start_from="brut")
 #           from openfisca_core import model
 #           from openfisca_core.simulations import SurveySimulation
 #       else: 
 #           openfisca_france.init_country()
 #           from openfisca_core import model
 #           from openfisca_core.simulations import SurveySimulation
            
        simulation = SurveySimulation()
        simulation.set_config(year=self.datesim, 
                              survey_filename = openfisca_survey,
                              param_file = os.path.join(os.path.dirname(model.PARAM_FILE), 'param.xml'))
        simulation.set_param()
        simulation.compute()
        
        self.simulation = simulation
        self.openfisca_output = simulation.output_table.table
#         print self.openfisca_output[["cotpat","salsuperbrut"]] # TODO: DOESN'T WORK AS EXPECTED BiZARRE !!
        return openfisca_survey

    
    def compare(self, threshold = 1):
        '''
        Fonction qui comparent les calculs d'OF et et de TaxIPP
        Gestion des outputs
        '''
        dta_output = self.paths['dta_output']
        ipp_output = read_stata(dta_output).sort(['id_foyf', 'id_indiv'], ascending=[True, False])
        openfisca_output = self.openfisca_output 
        openfisca_input = self.simulation.input_table.table
        ipp2of_output_variables = self.ipp2of_output_variables

        if self.param_scenario['option'] == 'salbrut':
            del ipp2of_output_variables['sal_brut']

        scenario = self.param_scenario['scenario']
        act = self.param_scenario['activite']
        act_conj = self.param_scenario['activite_C']

        check_list_commun = ['isf_foy', 'irpp_net_foy', 'irpp_bar_foy', 'ppe', 'ppe_brut_foy']
        check_list_minima = ['rsa_foys', 'rsa_act_foys', 'mv_foys', 'rsa_logt', 'y_rmi_rsa']
        check_list_af =['paje_foys', 'paje_base_foys', 'paje_clca_foys', 'af_foys', 'af_base', 'af_diff', 'af_maj', 'nenf_prest', 'biact_or_isole']
        check_list_sal =  ['csp_exo','csg_sal_ded', 'sal_irpp', 'sal_brut','csp_mo_vt','csp_nco', 'csp_co','vt','mo', 'sal_superbrut', 'sal_net', 'crds_sal', 'csg_sal_nonded', 'ts', 'tehr'] # 'csg_sal_ded'] #, 'irpp_net_foy', 'af_foys']- cotisations salariales : 'css', 'css_nco', 'css_co', 'sal_superbrut' 'csp',
        # 'decote_irpp_foy' : remarque par d'équivalence Taxipp
        check_list_chom =  ['csg_chom_ded', 'chom_irpp', 'chom_brut', 'csg_chom_nonded', 'crds_chom']
        check_list_ret =  ['csg_pens_ded', 'pension_irpp', 'pension_net', 'csg_pens_nonded', 'crds_pens']
        id_list = act + act_conj
        lists = {0 : check_list_sal, 1: check_list_sal + check_list_chom, 2: check_list_chom, 3 : check_list_sal + check_list_ret, 4 : check_list_chom + check_list_ret, 6 : check_list_ret}
        check_list = lists[id_list]
        if (scenario == 'celib') & (act == 3):
            check_list = check_list_ret
            
        check_list +=  check_list_minima + check_list_commun + check_list_af
        
        def _conflict_by_entity(ent, of_var, ipp_var, pb_calcul, output1 = openfisca_output, input1 = openfisca_input, output2 = ipp_output):
            if ent == 'ind':
                output1 = output1.loc[input1['quimen'].isin([0,1]), of_var]   
                output2 = output2[ipp_var]
                output2.index =  output1.index
            else :
                output1 = output1.loc[ input1['qui'+ent] == 0, of_var]    
                output2 = output2.loc[ input1['qui'+ent] == 0, ipp_var]
                input1 = input1.loc[ input1['qui'+ent] == 0, :]
            
            conflict = ((output2.abs() - output1.abs()).abs() > threshold)
            if len(output2[conflict]) != 0: # TODO : a améliorer
                print "Le calcul de " + of_var + " pose problème : "
                from pandas import DataFrame
                print DataFrame( {"IPP": output2[conflict], "OF": output1[conflict], "diff.": output2[conflict]-output1[conflict].abs()} ).to_string()
                print input1.loc[conflict[conflict == True].index, self.relevant_input_variables()].to_string()
                pb_calcul += [of_var]
#                pdb.set_trace()
        
        pb_calcul = []
        for ipp_var in check_list: # in ipp2of_output_variables.keys(): #
            of_var = ipp2of_output_variables[ipp_var] 
            entity = self.simulation.prestation_by_name[of_var].entity
            _conflict_by_entity(str(entity), of_var, ipp_var, pb_calcul)   
        print len(pb_calcul), pb_calcul
                
    def run_all(self, run_stata=True):
        self.work_on_param()
        self.def_ipp2of_dic()
        if paths['stata'] is None or run_stata is False:
            print ("Les programmes Stata de TaxIPP n'ont pas été appelés au cours de cette simulation" 
                "\n Si vous y avez normalement accès, vérifiez le chemin vers Stata dans CONFIG.py \n ")
        else :
            self.run_TaxIPP()
        self.run_OF()
        self.compare()
        
    def relevant_input_variables(self):
        simulation = self.simulation
        dataframe = simulation.input_table.table
        input_variables = list()
        for name, col in simulation.column_by_name.iteritems():
            if not all(dataframe[name] == col._default): 
                input_variables.append(name)
        return input_variables 

    def relevant_output_variables(self):
        simulation = self.simulation
        dataframe = simulation.output_table.table
        output_variables = list()
        for name, col in simulation.prestation_by_name.iteritems():
            if not all(dataframe[name] == col._default): 
                output_variables.append(name)
        return output_variables

def run():
    logging.basicConfig(level=logging.ERROR, stream=sys.stdout)
    param_scenario = {'scenario': 'celib', 'nb_enf' : 0, 'nmen':10, 'rev_max': 20000, 'activite':0} 
    param_scenario2 = {'scenario': 'marie', 'nb_enf' : 3, 'age_enf': [17,8,12], 'part_rev': 0.75, 'nmen':10, 'rev_max': 15000, 'activite':0} #'age_enf': [17,8,12], 'nb_enf_conj': 1, 'part_rev': 0.6, 'activite': 1, 'activite_C': 1}
    hop = Comparison_cases(2013, param_scenario)
    hop.run_all()#run_stata= False)

if __name__ == '__main__':
    run()