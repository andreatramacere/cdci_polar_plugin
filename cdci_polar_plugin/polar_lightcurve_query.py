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
from oda_api.data_products import NumpyDataProduct,NumpyDataUnit,BinaryData

from .polar_dataserve_dispatcher import PolarDispatcher
from .polar_dataserve_dispatcher import  PolarAnalysisException


class PolarLigthtCurve(LightCurveProduct):
    def __init__(self,name,file_name,data,header,prod_prefix=None,out_dir=None,src_name=None,meta_data={}):


        if meta_data == {} or meta_data is None:
            self.meta_data = {'product': 'polar_lc', 'instrument': 'polar', 'src_name': src_name}
        else:
            self.meta_data = meta_data

        self.meta_data['time'] = 'time'
        self.meta_data['rate'] = 'rate'
        self.meta_data['rate_err'] = 'rate_err'



        super(LightCurveProduct, self).__init__(name=name,
                                               data=data,
                                               name_prefix=prod_prefix,
                                               file_dir=out_dir,
                                               file_name=file_name,
                                               meta_data=meta_data)


    @classmethod
    def build_from_res(cls,
                             res,
                             src_name='',
                             prod_prefix='polar_lc',
                             out_dir=None,
                             delta_t=None):



        lc_list = []

        if out_dir is None:
            out_dir = './'

        if prod_prefix is None:
            prod_prefix=''







        file_name =  src_name+'.fits'
        print ('file name',file_name)

        meta_data={}
        meta_data['src_name'] = src_name
        meta_data['time_bin'] = delta_t

        res_json = res.json()
        df = pd.read_json(res_json['data'])

        root_file_path= prod_prefix + '_' + src_name+'.root'
        root_file_path=FilePath(file_name=root_file_path,file_dir=out_dir)
        #NOTE np.array(df.to_records()) does not work with decoding in py27, because pandas puts the u in the dtyep name
        #NOTE works only if decoded with py36

        
        if res_json['status']['success']:
            data=np.zeros(len(df['rate']), dtype=[('rate', '<f8'), ('rate_err', '<f8'),('time', '<f8')])
            data['rate']=df['rate']
            data['rate_err'] = df['rate_err']
            data['time'] = df['time']
            npd = NumpyDataProduct(data_unit=NumpyDataUnit(data=data,
                                                           hdu_type='table'),meta_data=meta_data)

            lc = cls(name=src_name, data=npd, header=None, file_name=file_name, out_dir=out_dir, prod_prefix=prod_prefix,
                     src_name=src_name,meta_data=meta_data)


        else:
            #print("result",res) # logging?
            _d=res_json['status']['exceptions'][0]
            print('_d',_d)
            raise PolarAnalysisException(message='polar light curve failed: %s'%_d['comment'],debug_message=_d['kind'])


        try:
            open(root_file_path.path, "wb").write(BinaryData().decode(res_json['root_file_b64']))
            lc.root_file_path=root_file_path
            #lc.root_file_b64=res_json['root_file_b64']
        except :
            raise PolarAnalysisException(message='polar failed to open/decode root_file')

        lc_list.append(lc)

        return lc_list



class PolarLightCurveQuery(LightCurveQuery):

    def __init__(self, name):

        super(PolarLightCurveQuery, self).__init__(name)

    def build_product_list(self, instrument, res, out_dir, prod_prefix='polar_lc',api=False):

        delta_t = instrument.get_par_by_name('time_bin')._astropy_time_delta.sec
        prod_list = PolarLigthtCurve.build_from_res(res,
                                                      src_name='lc',
                                                      prod_prefix=prod_prefix,
                                                      out_dir=out_dir,
                                                      delta_t=delta_t)

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
        q = PolarDispatcher(instrument=instrument,config=config,param_dict=param_dict,task='api/v1.0/lightcurve/')

        return q


    def set_instr_dictionaries(self, T1,T2,E1,E2,delta_t):
        return  dict(
            time_start=T1,
            time_stop=T2,
            time_bin=delta_t,
            energy_min=E1,
            energy_max=E2,
        )


    def process_product_method(self, instrument, prod_list,api=False):

        _names = []
        _lc_path = []
        _root_path=[]
        _html_fig = []

        _data_list=[]
        _binary_data_list=[]
        for query_lc in prod_list.prod_list:
            print('->name',query_lc.name)

            query_lc.write()
            if api == False:
                _names.append(query_lc.name)
                _lc_path.append(str(query_lc.file_path.name))
                _root_path.append(str(query_lc.root_file_path.name))
                print ('_root_path',_root_path)
                #x_label='MJD-%d  (days)' % mjdref,y_label='Rate  (cts/s)'
                _html_fig.append(query_lc.get_html_draw(x=query_lc.data.data_unit[0].data['time'],
                                                        y=query_lc.data.data_unit[0].data['rate'],
                                                        dy=query_lc.data.data_unit[0].data['rate_err'],
                                                        title='Start Time: %s'%instrument.get_par_by_name('T1')._astropy_time.utc.value,
                                                        x_label='Time  (s)',
                                                        y_label='Rate  (cts/s)'))

            if api==True:
                _data_list.append(query_lc.data)
                #try:
                #    open(root_file_path.path, "wb").write(BinaryData().decode(res_json['root_file_b64']))
                #    lc.root_file_path = root_file_path
                #except:
                #    pass
                _d,md=BinaryData(str(query_lc.root_file_path)).encode()
                _binary_data_list.append(_d)

        query_out = QueryOutput()

        if api == True:
            query_out.prod_dictionary['numpy_data_product_list'] = _data_list
            query_out.prod_dictionary['binary_data_product_list'] = _binary_data_list
        else:
            query_out.prod_dictionary['name'] = _names
            query_out.prod_dictionary['file_name'] = _lc_path
            query_out.prod_dictionary['root_file_name'] = _root_path
            query_out.prod_dictionary['image'] =_html_fig
            query_out.prod_dictionary['download_file_name'] = 'light_curves.tar.gz'

        query_out.prod_dictionary['prod_process_message'] = ''


        return query_out

    def get_dummy_products(self, instrument, config, out_dir='./'):
        raise RuntimeError('method to implement')

        # src_name = instrument.get_par_by_name('src_name').value
        #
        # dummy_cache = config.dummy_cache
        # delta_t = instrument.get_par_by_name('time_bin')._astropy_time_delta.sec
        # print('delta_t is sec', delta_t)
        # query_lc = LightCurveProduct.from_fits_file(inf_file='%s/query_lc.fits' % dummy_cache,
        #                                             out_file_name='query_lc.fits',
        #                                             prod_name='isgri_lc',
        #                                             ext=1,
        #                                             file_dir=out_dir)
        # print('name', query_lc.header['NAME'])
        # query_lc.name=query_lc.header['NAME']
        # #if src_name is not None:
        # #    if query_lc.header['NAME'] != src_name:
        # #        query_lc.data = None
        #
        # prod_list = QueryProductList(prod_list=[query_lc])
        #
        # return prod_list













