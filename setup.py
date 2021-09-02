from setuptools import setup, find_packages
setup(
    name = 'yuzu',
    version = '0.0.1',
    author = 'John Doe',
    author_email = 'john.doe@foo.com',
    description = '<short description for the tool>',
    long_description_content_type = "text/markdown",
    py_modules = ['cli', 'yuzu'],
    packages = find_packages(),
    python_requires='>=3.7',
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent",
    ],
    entry_points = '''
        [console_scripts]
        yuzu=cli:cli
    '''
)