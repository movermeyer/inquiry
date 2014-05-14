from setuptools import setup

classifiers = ["Development Status :: 4 - Beta",
               "License :: OSI Approved :: Apache Software License"]

setup(name='inquiry',
      version='0.0.1',
      description="advanced sql query builder",
      long_description="",
      classifiers=classifiers,
      keywords='',
      author='@stevepeak',
      author_email='steve@stevepeak.net',
      url='https://github.com/stevepeak/inquiry',
      license='Apache v2',
      packages=["inquiry"],
      include_package_data=True,
      zip_safe=False,
      install_requires=[],
      entry_points=None)
