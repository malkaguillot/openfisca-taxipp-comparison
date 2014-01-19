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


# TODO: MBJ, print only some ouput_vars

from pandas import read_stata, ExcelFile
from numpy import logical_not as not_, array, zeros

import subprocess
import pdb

import openfisca_france
openfisca_france.init_country()

from CONFIG import paths
from openfisca_core.simulations import SurveySimulation

THRESHOLD = 5

class Comparison_cases(object):
    """
    La classe qui permet de lancer les comparaisons par cas-types
    Structure de classe n'est peut-être pas nécessaire 
    """
    
    def __init__(self, datesim, dict_param):
        # Paramètres initiaux
        self.datesim = datesim
        self.dic_scenar = None
        self.dic_param = dict_param 
        self.paths = paths

        # Actualisés au cours de la comparaison
        self.dic_var_input = None
        self.dic_var_output = None
        
        self.simulation = None
        
    def work_on_param(self):
        paths = self.paths
        paths['dta_input']  = paths['dta_input'] + self.dic_param['scenario'] + ".dta"
        paths['dta_output']  = paths['dta_output'] + self.dic_param['scenario'] + ".dta"
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
                           'scenario' : 'celib','nmen': 3, 
                           'nb_enf' : 0, 'nb_enf_conj': 0, 'age_enf': 0,  'rev_max': 100000, 'part_rev': 1, 'loyer_mensuel_menage': 1000,
                           'activite': 0, 'cadre': 0, 'public' : 0, 'nbh_sal': 1820, 'taille_ent' : 20, 'tva' : 0,
                           'activite_C': 0, 'cadre_C': 0, 'public_C' : 0, 'nbh_sal_C': 1820, 'taille_ent_C' : 20, 'tva_C' : 0,
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
                    dic['age_enf'] = zeros(1)*dic['npac']
                dic['age_enf'] = str(dic['age_enf'])[1:-1].replace(',', ' ') # To stata

            return dic
            
        dic = self.dic_param
        self.dic_scenar = _dic_param_ini(dic)
        dic['annee_sim'] = self.datesim
        dic = _default_param(dic)
        dic = _civilstate(dic)
        dic = _enf(dic)
        self.dic_param = dic

    def dic_var(self):
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
            
        self.dic_var_input = _dic_corresp('input')
        self.dic_var_output =  _dic_corresp('output')
        
        
    def run_TaxIPP(self):
        do_in = self.paths['do_in']
        do_out = self.paths['do_out']
        len_preamb = 40
        dic = self.dic_param
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
                
                # Repo pour stata +dic_param
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
        subprocess.call([self.paths['stata'],  "do", self.paths['do_out']], shell=True)

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
                data = data.drop('dic_scenar', 1)
            return data
        
        def _adaptation_var(data, dic_var):

            def _quifoy(col):
                # TODO, il faut gérer les pac
                try:
                    quifoy = col["conj"]==1 + col["pac"]==1 # TODO: faux 
                except:
                    quifoy = col["conj"]==1
                return quifoy
            
            def _quimen(col):
                # TODO, il faut gérer les enfants
                try:
                    quimen = col["conj"]==1 + col["concu"]==1 + col["pac"]==1
                except:
                    quimen = col["conj"]==1 + col["concu"]==1 
                return quimen
            
            def _so(data):
                data["so"] = 0
                data.loc[data['proprio_empr'] == 1, 'so'] = 1
                data.loc[data['proprio'] == 1, 'so'] = 2
                data.loc[data['locat'] == 1, 'so'] = 4
                data.loc[data['loge'] == 1, 'so'] = 6
                return data
            
            def _compl(var):
                var = 1- var
                return var
            
            def _count_by_ff(var):
                ''' Compte le nombre de bouléen == 1 au sein du foyer fiscal'''
                nmen = 10
                for i in range(1, nmen):
                    compteur=0
                    j=0
                    while data['idfoy'] == i:
                        j += j
                        if var ==1:
                            compteur += compteur
                        else :  
                            compteur = compteur
                        data[j,'var'] = compteur
                
            def _enf(data):
                data["enf_college"] = 0
                if  (11<data['age']<15):
                    data['enf_college'] = 1
                else:
                    data['enf_college'] = 0
#                data["enf_lycee"] = (data['age'] > 14 & data['age']<19)
#                data["enf_sup"] = (data['age'] >18)
#                data["f7ea"] = _count_by_ff(data["enf_college"]) 
#                data["nenf1113"] + data["nenf1415"] #11-14
#                data["f7ec"] = _count_by_ff(data["enf_lycee"]) #data["nenf1617"] #15-17
#                data["f7ef"] = _count_by_ff(data["enf_sup"]) #data["nenfmaj1819"] + data["nenfmaj20"] + data["nenfmaj21plus"] #>17
                data.drop(["nenf1113", "nenf1415", "nenf1617", "nenfmaj1819", "nenfmaj20",
                                   "nenfmaj21plus", "nenfnaiss", "nenf02",  "nenf35",  "nenf610"], axis = 1, inplace=True)
                return data
            
            def _workstate(data):
                data['chpub'] = 0
                data.loc[data['public'] == 1, 'chpub'] = 1
                data.loc[data['public'] == 0, 'chpub' ] = 6
                return data
            
            data.rename(columns= dic_var, inplace=True)
            data["agem"] = 12*data["age"]
            
            data["idfam"] = data["idmen"]
            data["quifoy"] = data.apply(_quifoy, axis=1).astype(int)
            data["quimen"] = data.apply(_quimen, axis=1).astype(int)
            data["quifam"] = data['quimen']
            
            data = _so(data)
            #data = _enf(data)
            data = _workstate(data)
            print data.columns
            #data["caseN"] = _comp(data["caseN"])
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
            # print data.columns
            return data
        
        data_IPP = _test_of_dta(dta_input, dic)
        openfisca_survey =  _adaptation_var(data_IPP, self.dic_var_input)
        openfisca_survey = openfisca_survey.fillna(0)

        simulation = SurveySimulation()
        simulation.set_config(year=self.datesim, survey_filename = openfisca_survey)
        simulation.set_param()
        simulation.compute()
        
        self.simulation = simulation
        self.openfisca_outputput = simulation.output_table.table
        return openfisca_survey

    
    def compare(self, seuil_abs = 100, seuil_rel = 0.10):
        '''
        Fonction qui comparent les calculs d'OF et et de TaxIPP
        Gestion des outputs
        '''
        dta_output = self.paths['dta_output']
        ipp_output = read_stata(dta_output).fillna(0)
        dta_input = self.paths['dta_input']
        ipp_input =  read_stata(dta_input).fillna(0)
        openfisca_output = self.openfisca_outputput.fillna(0)
        openfisca_input = self.simulation.input_table.table
        ipp2of_output_variables = self.dic_var_output

        check_list = ['csg_sal_ded', 'irpp_net_foy', 'af_foys'] # 'csg_sal_ded',
        print self.dic_param
        
        for ipp_var in check_list:
            of_var = ipp2of_output_variables[ipp_var]
            entity = self.simulation.prestation_by_name[of_var].entity
            
            if entity == 'ind':
                conflict = ((ipp_output[ipp_var] - openfisca_output[of_var].abs()).abs() < THRESHOLD)
                print conflict.to_string()
                print ipp_output.loc[not_(conflict), ipp_var].to_string()
                print openfisca_output.loc[not_(conflict), of_var].to_string()
                                
                print ipp_input.loc[not_(conflict), ].to_string()
                print openfisca_input.loc[not_(conflict), self.relevant_input_variables()].to_string()

                #error_diag()
                
                # TODO: finish by calling error_diag
            elif entity == "fam":
            
                pass
            
            
            elif entity == "foy":
                openfisca_foy = openfisca_output.loc[ openfisca_input.quifoy == 0, of_var]             
                ipp_foy = ipp_output.loc[ openfisca_input.quifoy == 0, ipp_var] 
                print ipp_foy

                conflict = ((ipp_foy - openfisca_foy.abs()).abs() > THRESHOLD)
                print conflict.to_string()
                
                
            elif entity == "men":
                pass
        def _diff(seuil_abs, seuil_rel):
            for k, v in dic.items() :
                diff_abs =  ipp_output[k].mean() - openfisca_output[v].mean()
                
                if diff_abs > seuil_abs :
                    print " Différence absolue pour ", k, ' : ', diff_abs
                
                diff_rel = (ipp_output.loc[(ipp_output[k] != 0) & (openfisca_output[v] != 0), k] /openfisca_output.loc[(ipp_output[k] != 0) & (openfisca_output[v] != 0), v] ).mean()
                if (diff_rel > seuil_rel) & (diff_rel is not None) :
                    print " Différence relative pour  ", k, ' : ', diff_rel
        
#         _diff(seuil_abs, seuil_rel)
    
    def run_all(self, run_stata=True):
        self.work_on_param()
        self.dic_var()
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
    
    dict_param = { 'scenario' : 'marie', 'nmen': 3,
                  'nb_enf' : 3, 'age_enf' : [20,12,2],
                 'nbh_sal': 1820, 'rev_max': 100000, 'part_rev': 0.6
                 }
    dic = {'scenario': 'marie', 'rev_max': 1000000, 'nb_enf' : 3, 'age_enf' : [20,12,2], 'part_rev': 0.6}
    hop = Comparison_cases(2011, dic)
    hop.run_all(run_stata=False)


if __name__ == '__main__':
    
    #fill_with_ipp_input(read_stata(paths['dta_input']+ 'concubin.dta'))
    run()
