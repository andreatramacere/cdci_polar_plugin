"""
Overview
--------
   
general info about this module


Classes and Inheritance Structure
----------------------------------------------
.. inheritance-diagram:: 

Summary
---------
.. autosummary::
   list of the module you want
    
Module API
----------
"""

from __future__ import absolute_import, division, print_function


__author__ = "Andrea Tramacere"

# Standard library
# eg copy
# absolute import rg:from copy import deepcopy

# Dependencies
# eg numpy 
# absolute import eg: import numpy as np

# Project
# relative import eg: from .mod import f


from cdci_polar_plugin import conf_file,conf_dir

from cdci_data_analysis.analysis.queries import  *
from cdci_data_analysis.analysis.instrument import Instrument
from .polar_dataserve_dispatcher import PolarDispatcher

from .polar_lightcurve_query import PolarLightCurveQuery




def common_instr_query():
    #not exposed to frontend
    #TODO make a special class
    #max_pointings=Integer(value=50,name='max_pointings')


    E1_keV = SpectralBoundary(value=0., E_units='keV', name='E1_keV')
    E2_keV = SpectralBoundary(value=10000., E_units='keV', name='E2_keV')
    spec_window = ParameterRange(E1_keV, E2_keV, 'spec_window')
    instr_query_pars=[spec_window]


    return instr_query_pars


def polar_factory():
    print('--> Polar Factory')
    src_query=SourceQuery('src_query')



    instr_query_pars=common_instr_query()

    instr_query=InstrumentQuery(
        name='polar_parameters',
        extra_parameters_list=instr_query_pars,
        input_prod_list_name=[],
        input_prod_value=None,
        catalog=None,
        catalog_name='user_catalog')





    light_curve =PolarLightCurveQuery('polar_lc_query')



    query_dictionary={}
    query_dictionary['polar_lc'] = 'polar_lc_query'
    #query_dictionary['update_image'] = 'update_image'

    print('--> conf_file',conf_file)
    print('--> conf_dir', conf_dir)

    return  Instrument('polar',
                       asynch=False,
                       data_serve_conf_file=conf_file,
                       src_query=src_query,
                       instrumet_query=instr_query,
                       product_queries_list=[light_curve],
                       data_server_query_class=PolarDispatcher,
                       query_dictionary=query_dictionary)

