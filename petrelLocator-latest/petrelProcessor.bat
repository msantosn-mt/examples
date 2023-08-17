set PYTHONIOENCODING=cp437:backslashreplace
del /q /s TempXMLFileStore/*
call mapping.bat >>logs/petrelProcessor.log 2>&1
call petrelProcessor.py