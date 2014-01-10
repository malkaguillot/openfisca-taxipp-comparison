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
from pandas import read_stata

import openfisca_france
openfisca_france.init_country()

from openfisca_core.simulations import ScenarioSimulation, SurveySimulation



def compare(year = 2006):

    ## TODO: loop through stata files

    df = read_stata("../Taxipp/base_IPP_celib.dta")
    print df.to_string()
    
    # TODO: fill simulation and scenario
    simulation = ScenarioSimulation()
    simulation.set_config(year = year, reforme = False, nmen = 3, maxrev = 100000, x_axis = 'sali')
    # Add husband/wife on the same tax sheet (foyer).

    fill_with_ipp_input(simulation, df)
    
    simulation.scenario.addIndiv(1, datetime.date(1975, 1, 1), 'conj', 'part')
    simulation.set_param()

    # TODO: compare results 

    df = simulation.get_results_dataframe(index_by_code=True)
    print df.to_string()


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
#    compare(2011)
    df = read_stata("../Taxipp/base_IPP_celib.dta")
    fill_with_ipp_input(df)