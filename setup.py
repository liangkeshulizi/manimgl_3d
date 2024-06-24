from setuptools import setup, find_packages

setup(
    name='manimgl_3d',
    version='0.1',
    packages=find_packages(),
    use_pth=True, # this ensures pylance can locate the module file statically and correctly
    install_requires=[],
    extras_require={
        'dev': ['pytest',],
    },
    author='liangkeshulizi',
    author_email='liangkeshulizi@gmail.com',
    description='in development...',
    # url='',
)
