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

import pandas as pd
from pandas import read_stata
import numpy as np
import subprocess
import pdb
from collections import defaultdict

import openfisca_france
openfisca_france.init_country()

from CONFIG import paths
from openfisca_core.simulations import SurveySimulation


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
        self.dic_var = None
        
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
                
            elif dic['scenario'] == 'marié':
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
            return dic
            
        dic = self.dic_param
        self.dic_scenar = _dic_param_ini(dic)
        dic['annee_sim'] = self.datesim
        dic = _default_param(dic)
        dic = _civilstate(dic)
        dic = _enf(dic)
        self.dic_param = dic

    def dic_corresp(self):
        ''' 
        Création du dictionnaire dont les clefs sont les noms des variables IPP
        et les arguments ceux des variables OF 
        '''
        names = pd.ExcelFile('correspondances_variables.xlsx').parse('input')
        names = np.array(names.loc[names['scenario'] == 1, ['var_TAXIPP', 'var_OF']])
        dic = {}
        for i in range(len(names)) :
            dic[names[i,0]] = names[i,1]
            
        self.dic_var = dic
        
        
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
        subprocess.call([self.paths['stata'], "do", self.paths['do_out']], shell=True)

    def run_OF(self):
        '''
        Lance le calculs sur OF à partir des cas-types issues de TaxIPP
        input : base .dta issue de l'étape précédente
        '''
        dta_input = self.paths['dta_input']
        dic = self.dic_scenar
        
        def _test_of_dta(dta_input, dic):
            ''' Cette fonction test que la table .dta trouvée 
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
        
        openfisca_survey = _test_of_dta(dta_input, dic)

        #openfisca_survey = table_taxipp.loc[:,["id_foyf","id_indiv", "age", "marie", "mat", "decl", "conj", "pac", "cadre", "public" ]]
        openfisca_survey.rename(columns=self.dic_var, inplace=True)
        print openfisca_survey.columns
        print openfisca_survey.to_string()
        
         #TODO: REMOVE IF NOT CELIB
        openfisca_survey["idmen"] = openfisca_survey["idfoy"] 
        openfisca_survey["idfam"] = openfisca_survey["idfoy"] 
    
        def _quifoy(col):
            quimen = col["conj"]==1 + col["pac"]==1
            return quimen
        
        openfisca_survey["quifoy"] = openfisca_survey.apply(_quifoy, axis=1).astype(int)
        openfisca_survey.drop(["decl", "conj", "pac"], axis=1)
        print openfisca_survey.columns
        print openfisca_survey.to_string()
        
        # TODO: REMOVE (just for testing import
        openfisca_survey["quimen"] = openfisca_survey["quifoy"]
        openfisca_survey["quifam"] = openfisca_survey["quifoy"]
        ## UNTL HERE
        simulation = SurveySimulation()
        simulation.set_config(year=self.datesim, survey_filename=openfisca_survey)
        simulation.set_param()
        simulation.compute()
        print simulation.input_table.table.describe().to_string()    
        print simulation.output_table.table.describe().to_string()    
        
        return openfisca_survey

    
    def compare(self):
        '''
        Fonction qui comparent les calculs d'OF et et de TaxIPP
        Gestion des outputs
        '''
        dta_output = self.paths['dta_output']
        print self.datesim
    
    def run_all(self):
        self.work_on_param()
        self.dic_corresp()
        if paths['stata'] is None :
            print ("Les programmes Stata de TaxIPP n'ont pas été appelés au cours de cette simulation" 
                "\n Si vous y avez normalement accès, vérifiez le chemin vers Stata dans CONFIG.py \n ")
        else :
            self.run_TaxIPP()
        self.run_OF()
        
        

def fill_with_ipp_input(df):

    print df.columns
    openfisca_survey = df.loc[:,["id_foyf","id_indiv", "age", "marie", "mat", "decl", "conj", "pac", "cadre", "public" ]]
    print openfisca_survey.to_string()
    from pandas import DataFrame
    d = DataFrame()
    
    # simple rename
    
    cols = {"id_foyf" : "idfoy", "id_indiv" : "noi"}
    openfisca_survey.rename( columns=cols, inplace=True)
    
    # TODO: REMOVE IF NOT CELIB
    openfisca_survey["idmen"] = openfisca_survey["idfoy"] 
    openfisca_survey["idfam"] = openfisca_survey["idfoy"] 
    
    def _quifoy(col):
        quimen = col["conj"]==1 + col["pac"]==1
        return quimen
    
    openfisca_survey["quifoy"] = openfisca_survey.apply(_quifoy, axis=1).astype(int)
    openfisca_survey.drop(["decl", "conj", "pac"], axis=1)
    print openfisca_survey.columns
    print openfisca_survey.to_string()
    
    # TODO: REMOVE (just for testing import
    openfisca_survey["quimen"] = openfisca_survey["quifoy"]
    openfisca_survey["quifam"] = openfisca_survey["quifoy"]
    ## UNTL HERE
    simulation = SurveySimulation()
    simulation.set_config(year=2006, survey_filename=openfisca_survey)
    simulation.set_param()
    simulation.compute()
    print simulation.input_table.table.describe().to_string()    
    print simulation.output_table.table.describe().to_string()    
    
    return openfisca_survey


if __name__ == '__main__':
    dict_param = { 'scenario' : 'concubin', 'nmen': 3, 
                 'nbh_sal': 1820, 'rev_max': 100000, 'part_rev': 0.6
                 }
    hop = Comparison_cases(2011, dict_param)
    hop.run_all()