This directory contains 5 files.

- Readme.txt				This very file.
- localconfiguration.py		The configuration of the scripts that come along this distribution.
- petrelLocator.py			The script that will traverse the file systems looking for the projects and store them in a DB.
- petrelProcessor.py		Script that will invoke Petrel when we identify a project that matches our criteria.
- petrelXMLGenerator.py	Another script that will create basic XML files from projects we cannot process.

Pre-requisites:
------------------------------
- Python v.3.3.x or newer.
- py-postgresql 
- A PostgreSQL database.
- A Petrel installation (2009 to 2011).

How to use:
------------------------------
It is necessary to set an environment variable before invoking any of the scripts. This in order to handle correctly the issues with the Windows codepage.

set PYTHONIOENCODING=cp437:backslashreplace

** PETRELLOCATOR.PY **
petrelLocator.py can be scheduled to run during workhours, it will traverse the file paths specified in the localconfiguration.py:paths variable, validating
size, last modification or existence of XML file. This will be stored in a database. The process_flag field will be populated as follow.

Value	Description
0		Project is ok, no need to execute Petrel.
1		New project detected and fits our criteria, must call petrel.
2		Project file was modified and XML is outdated, must call petrel.
3		Invalid XML file found in the project, must call petrel.
10		Project size is too big, is out of our criteria, petrel is not going to be invoked.
11		Project filename is too long to be processes by petrel, petrel is not going to be invoked.
12		Project was edited with an uncompatible version of petrel, set by localconfiguration.py:unsupportedPetrelVersion, petrel is not invoked.

The script should be invoked as follows:
c:\kadme\petrel-scripts-2011> set PYTHONIOENCODING=cp437:backslashreplace
c:\kadme\petrel-scripts-2011> python petrelLocator.py


** PETRELPROCESSOR.PY **
petrelProcessor.py should be scheduled only outside working hours as it invokes Petrel and consumes a petrel license, the logic is to retrieve from the database
the projects that are valid (have process_flag between 1-10) or those projects that were processed and fail because of issues with Petrel itself. After processing
the projects it will set the process_flag to 0 and store the exit code of the petrel process.

The script should be invoked as follows:
c:\kadme\petrel-scripts-2011> set PYTHONIOENCODING=cp437:backslashreplace
c:\kadme\petrel-scripts-2011> python petrelProcessor.py


** PETRELXMLGENERATOR.PY **
petrelXMLGenerator.py can be scheduled anytime after petrelLocator.py, it will read from the DB those projects that by
default should not be processed, and from those records extract information as when was last modified, the size, etc.

The script should be invoked as follows:
c:\kadme\petrel-scripts-2011> set PYTHONIOENCODING=cp437:backslashreplace
c:\kadme\petrel-scripts-2011> python petrelXMLGenetor.py
