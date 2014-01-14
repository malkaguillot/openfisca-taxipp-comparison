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


import datetime
import pandas as pd
from pandas import read_stata
import numpy as np
import subprocess
from tempfile import NamedTemporaryFile
import os
import json

import openfisca_france
openfisca_france.init_country()

from CONFIG import paths
from openfisca_core.simulations import SurveySimulation


class Comparison_cases(object):
    """
    La classe qui permet de lancer les comparaisons par cas-types
    Structure de classe n'est peut-être pas nécessaire 
    """
    
    def __init__(self, datesim, dic_param):
        # Paramètres initiaux
        self.datesim = datesim
        self.dic_param = dic_param
       
        self.paths = paths
        self.paths['dta_out']  = paths['dta_out'] + dic_param['scenario'] + ".dta"
        print self.paths['dta_out']
        # Actualisés au cours de la comparaison
        self.dic_var = None
        
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
        len_preamb = 64
        dic = self.dic_param
        
        def _insert_param_dofile(dic, do_in, do_out, len_preamb):
            lines = open(do_in).readlines()
            head = lines[:len_preamb +1]
            lines = lines[- (len(lines) - len_preamb):]
            with open(do_out, "w") as f:
                f.seek(0)
                # Préambule
                f.writelines(head)
                
                # Insertions des paramètres
                for k, v in dic.items():
                    to_write = 'global ' + k +  " "+ str(v) + "\n"
                    f.write(to_write)
                    
                # Corps du dofile
                f.writelines(lines)
                f.close()
         
        _insert_param_dofile(dic, do_in, do_out, len_preamb)
        subprocess.call([self.paths['stata'], "do", self.paths['do_out']], shell=True)

    def run_OF(self):
        '''
        Lance le calculs sur OF à partir des cas-types issues de TaxIPP
        input : base .dta issue de l'étape précédente
        '''
        table_taxipp = read_stata(self.paths['dta_out'])
        print table_taxipp.columns
        # Keep TaxiPP output
        self.taxipp_output = table_taxipp
        openfisca_survey = table_taxipp.loc[:,["id_foyf","id_indiv", "age", "marie", "mat", "decl", "conj", "pac", "cadre", "public" ]]
        openfisca_survey.rename(columns=self.dic_var, inplace=True)
        print self.dic_var
        print openfisca_survey.to_string()
        
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
        print self.datesim
        

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
    #compare(2011)
    dic_param = { 'scenario' : 'celib','nmen': 15, 'nbh_sal': 1820, 'rev_max': 100000, 'part_rev': 0.6}
    hop = Comparison_cases(2008, dic_param)
    hop.dic_corresp()
    hop.run_TaxIPP()
    hop.run_OF()
    