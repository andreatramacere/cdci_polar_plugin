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

from builtins import (bytes, str, open, super, range,
                      zip, round, input, int, pow, object, map, zip)

__author__ = "Andrea Tramacere"

# Standard library
# eg copy
# absolute import rg:from copy import deepcopy
import os

# Dependencies
# eg numpy
# absolute import eg: import numpy as np

# Project
# relative import eg: from .mod import f


import ddosaclient as dc

# Project
# relative import eg: from .mod import f
import  numpy as np
import pandas as pd
from astropy.table import Table

from pathlib import Path

from astropy.io import fits as pf
from cdci_data_analysis.analysis.io_helper import FitsFile
from cdci_data_analysis.analysis.queries import LightCurveQuery
from cdci_data_analysis.analysis.products import LightCurveProduct,QueryProductList,QueryOutput
from cdci_data_analysis.analysis.io_helper import FilePath

from .polar_dataserve_dispatcher import PolarDispatcher



class PolarLigthtCurve(LightCurveProduct):
    def __init__(self,name,file_name,data,header,prod_prefix=None,out_dir=None,src_name=None):


        super(PolarLigthtCurve, self).__init__(name,
                                               data,
                                               header,
                                               file_name=file_name,
                                               name_prefix=prod_prefix,
                                               file_dir=out_dir,
                                               src_name=src_name)




    @classmethod
    def build_from_res(cls,
                             res,
                             src_name='',
                             prod_prefix='polar_lc',
                             out_dir=None):



        lc_list = []

        if out_dir is None:
            out_dir = './'

        if prod_prefix is None:
            prod_prefix=''
        #print('CICCIO', prod_prefix, src_name)

        #lc_paht = getattr(res, lightcurve_attr)
        #print('lc file-->', lc_paht, lightcurve_attr)
        #lc_paht='./'
        data = pd.read_json(res.json()['data'])
        data = np.array(Table.from_pandas(data))
        #print ('data',type(data),lc_paht)
        #hdu_list = FitsFile(lc_paht).open()
        #for hdu in hdu_list:
        #    if hdu.name == 'ISGR-SRC.-LCR':
        #        # print('name', hdu.header['NAME'])
        #        name = hdu.header['NAME']
        #        data = hdu.data
        #        header = hdu.header

        file_name = prod_prefix + '_' + src_name+'.fits'
        print ('file name',file_name)
        lc = cls(name=src_name, data=data, header=None, file_name=file_name, out_dir=out_dir, prod_prefix=prod_prefix,
                 src_name=src_name)

        lc_list.append(lc)

        return lc_list



class PolarLightCurveQuery(LightCurveQuery):

    def __init__(self, name):

        super(PolarLightCurveQuery, self).__init__(name)

    def build_product_list(self, instrument, res, out_dir, prod_prefix='polar_lc'):
        src_name = instrument.get_par_by_name('src_name').value

        prod_list = PolarLigthtCurve.build_from_res(res,
                                                      src_name=src_name,
                                                      prod_prefix=prod_prefix,
                                                      out_dir=out_dir)

        # print('spectrum_list',spectrum_list)

        return prod_list


    def get_data_server_query(self, instrument,
                              config=None):

        #scwlist_assumption, cat, extramodules, inject=OsaDispatcher.get_osa_query_base(instrument)
        E1=instrument.get_par_by_name('E1_keV').value
        E2=instrument.get_par_by_name('E2_keV').value
        src_name = instrument.get_par_by_name('src_name').value
        T1=instrument.get_par_by_name('T1')._astropy_time.unix
        T2=instrument.get_par_by_name('T2')._astropy_time.unix
        delta_t = instrument.get_par_by_name('time_bin')._astropy_time_delta.sec
        param_dict=self.set_instr_dictionaries(T1,T2,E1,E2,delta_t)

        print ('build here',config,instrument)
        q = PolarDispatcher(instrument=instrument,config=config,param_dict=param_dict,task='api/v1.0/lightcurve')

        return q


    def set_instr_dictionaries(self, T1,T2,E1,E2,delta_t):
        return  dict(
            time_start=T1,
            time_stop=T2,
            time_bin=delta_t,
            energy_min=E1,
            energy_max=E2,
        )


    def process_product_method(self, instrument, prod_list):

        _names = []
        _lc_path = []
        _html_fig = []

        for query_lc in prod_list.prod_list:
            print('->name',query_lc.name)

            query_lc.write()

            _names.append(query_lc.name)
            _lc_path.append(str(query_lc.file_path.name))
            _html_fig.append(query_lc.get_html_draw(x=query_lc.data['time'],y=query_lc.data['rate'],dy=query_lc.data['rate_err']))
            # print(_html_fig[-1])

        query_out = QueryOutput()
        _data={}
        _data['time']=query_lc.data['time']
        _data['rate']=query_lc.data['rate']
        _data['rate_err']=query_lc.data['rate_err']

        query_out.prod_dictionary['data'] = _data
        query_out.prod_dictionary['name'] = _names
        query_out.prod_dictionary['file_name'] = _lc_path
        query_out.prod_dictionary['image'] =_html_fig
        query_out.prod_dictionary['download_file_name'] = 'light_curves.tar.gz'
        query_out.prod_dictionary['prod_process_message'] = ''

        return query_out

    def get_dummy_products(self, instrument, config, out_dir='./'):
        src_name = instrument.get_par_by_name('src_name').value

        dummy_cache = config.dummy_cache
        delta_t = instrument.get_par_by_name('time_bin')._astropy_time_delta.sec
        print('delta_t is sec', delta_t)
        query_lc = LightCurveProduct.from_fits_file(inf_file='%s/query_lc.fits' % dummy_cache,
                                                    out_file_name='query_lc.fits',
                                                    prod_name='isgri_lc',
                                                    ext=1,
                                                    file_dir=out_dir)
        print('name', query_lc.header['NAME'])
        query_lc.name=query_lc.header['NAME']
        #if src_name is not None:
        #    if query_lc.header['NAME'] != src_name:
        #        query_lc.data = None

        prod_list = QueryProductList(prod_list=[query_lc])

        return prod_list













