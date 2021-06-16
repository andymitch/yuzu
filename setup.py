import setuptools 

setuptools.setup( 
    name='yuzu', 
    version='1.0', 
    author='Andrew Mitchell', 
    author_email='andymitch559@protonmail.com', 
    description='Says hello for now', 
    packages=setuptools.find_packages(), 
    entry_points={ 
        'console_scripts': [ 
            'yuzu = yuzu.yuzu:main' 
        ] 
    }, 
    classifiers=[ 
        'Programming Language :: Python :: 3', 
        'License :: OSI Approved :: MIT License', 
        'Operating System :: OS Independent', 
    ], 
)
