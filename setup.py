from distutils.core import setup
Version="0.1"

setup (name = "cmip5utils",
       author="PCMDI Software Team",
       version=Version,
       description = "Utilities for CMIP5 data manipulation",
       url = "https://github.com/doutriaux1/CMIP5splices/wiki",
       packages = ['cmip5utils'],
       package_dir = {'cmip5utils': 'Lib'},
       scripts = ['Script/cdsplice.py','Script/BIG_dict.py','Script/combine_models_ann_glb.py'],
      )
    
