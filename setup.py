try:
        from setuptools import setup
except ImportError:
        from distutils.core import setup

setup(name='python-amazon-api',
        version='0.5.10',
        description="A Python module for accessing Amazon's Product Advertising API",
        long_description=open('README.rst').read() + '\n\n' + open('HISTORY.rst').read(),
        author='Mike Taylor',
        author_email='mike@taylorwebhome.org',
        packages = ['awspyapi'],
        url="git://github.com/yatinla/python-amazon-api.git",
        download_url="git://github.com/yatinla/python-amazon-api.git",
        license=open('LICENSE').read,
        data_files=[('', ['./HISTORY.rst','./LICENSE','./README.rst','./README.txt','./README.md']),],
        include_package_data=True,
      )

