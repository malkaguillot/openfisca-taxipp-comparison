# -*- coding: utf-8 -*-
import os

# Your paths
path_comparison = os.path.dirname(__file__) 
path_stata = None # To complete to lauch TaxIPP

paths = {
         'do_in' : path_comparison + '/Taxipp/Programme_IPP.do',
         'do_out': path_comparison + '/OpenFisca/do_out.do',
         'stata' : path_stata,
         'dta_input' : path_comparison + '/Taxipp/base_IPP_input_',
         'dta_output' : path_comparison + '/Taxipp/base_IPP_output_',
         'repo_to_stata' : (path_comparison + '\Taxipp')
          }