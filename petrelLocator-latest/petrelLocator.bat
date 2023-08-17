set PYTHONIOENCODING=cp437:backslashreplace
call mapping.bat >>logs/petrelLocator.log 2>&1
call petrelLocator.py
call petrelXMLGenerator.py