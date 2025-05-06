from setuptools import setup, find_packages

setup(
    name='manimgl_3d',
    version='0.1',
    packages=find_packages(),
    use_pth=True, # this ensures pylance can locate the module file statically and correctly
    install_requires=['manimgl==1.6.1', 'trimesh==4.4.7'],
    author='LIYIZHOU',
    author_email='liangkeshulizi@gmail.com',
    description='An extension for manimgl, adding advanced render features.',
    # url='',
)
