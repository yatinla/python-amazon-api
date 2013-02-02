try:
        from setuptools import setup
except ImportError:
        from distutils.core import setup

setup(name='python-amazon-api',
        version='0.1',
        description="A Python module for accessing Amazon's Product Advertising API",
        long_description=open('README.rst').read() + '\n\n' + open('HISTORY.rst').read(),
        author='Mike Taylor',
        author_email='mike@taylorwebhome.org',
        url="https://bitbucket.org/mediomuerto/python-amazon-api",
        download_url="https://mediomuerto@bitbucket.org/mediomuerto/python-amazon-api.git",
        package_dir={'python-amazon-api': 'python-amazon-api'},
        license=open('LICENSE').read,
        include_package_data=True,
        packages = ['python-amazon-api']
      )

