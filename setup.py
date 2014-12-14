from setuptools import setup

classifiers = ["Development Status :: 4 - Beta",
               "License :: OSI Approved :: Apache Software License"]

install_requires = ["valideer>=0.3", "timestring"]

setup(name='inquiry',
      version='0.0.3',
      description="psql query generator",
      long_description="",
      classifiers=classifiers,
      keywords='',
      author='@stevepeak',
      author_email='steve@stevepeak.net',
      url='https://github.com/tasks/inquiry',
      license='Apache v2',
      packages=["inquiry"],
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      entry_points=None)
