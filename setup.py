import os
from distutils.command.build import build

from django.core import management
from setuptools import find_packages, setup

try:
    with open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as f:
        long_description = f.read()
except:
    long_description = ''


class CustomBuild(build):
    def run(self):
        management.call_command('compilemessages', verbosity=1)
        build.run(self)


cmdclass = {
    'build': CustomBuild
}

setup(
    name='pretix-cas',
    version='1.1.0',
    description='Apereo CAS authentication backend for pretix',
    long_description=long_description,
    long_description_content_type='text/markdown',

    url='https://github.com/DataManagementLab/pretix-cas',
    author='Benjamin Haettasch & TU Darmstadt BP Informatik 2019/20 Group 45',
    author_email='benjamin.haettasch@cs.tu-darmstadt.de',

    license='Apache Software License',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Environment :: Web Environment',
        'Development Status :: 5 - Production/Stable',
    ],

    install_requires=['python-cas>=1.5.0'],
    packages=find_packages(exclude=['tests', 'tests.*']),
    include_package_data=True,
    cmdclass=cmdclass,
    entry_points="""
[pretix.plugin]
pretix_cas=pretix_cas:PretixPluginMeta
""",
)
