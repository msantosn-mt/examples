# Version v0.1 / miguel@kadme.com / Nov 2012

# Needed this before execution: set PYTHONIOENCODING=cp437:backslashreplace

# We have to load all these modules
# sys and os are mandatory.
# time for some timestamp evaluations
# postgresql to query the database
# localconfiguration is our local configuration specified in localconfiguration.py
import sys, os, time, glob, postgresql, uuid, logging, localconfiguration

# To manipulate the XML
from xml.dom.minidom import Document

# To write letters in different languages.
import codecs

# Get all from the localconfiguration.py file.
from localconfiguration import *

# Define the log file
if LogLevel is 'DEBUG':
    logging.basicConfig(level=LogLevel, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
else:
    logging.basicConfig(filename='logs\petrelXMLGenerator.log', level=LogLevel, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    print('Sending output to logfile.')

def UpdateDB(PetProjectFile):
    sqlQuery = 'UPDATE projects SET last_process_date=NOW(), process_flag=0, processing_time=1, \
               process_exit_code=0, process_error_count=0 WHERE project_filename=$$' + PetProjectFile + '$$'
    logging.debug('Query: %s', sqlQuery)
    sql = db.prepare(sqlQuery)
    sql()

def CreatePetProjectXMLFileName(PetProjectName, PetProjectFile, PetOceanPath):
    PetProjectXMLFileNameString = PetProjectName + '___' + str(uuid.uuid3(uuid.NAMESPACE_URL, PetProjectFile)) + '.xml'
    PetProjectXMLFileName = os.path.join(XMLFilesStore, PetProjectXMLFileNameString)
    logging.debug('CreatePetProjectXMLFileName() = %s', PetProjectXMLFileName)
    return PetProjectXMLFileName
    
def StoreXML(PetXML, PetProjectFile):
    #import pdb; pdb.set_trace()
    logging.debug('PetProjectFile: %s', PetProjectFile)
    if PetProjectFile.lower().endswith('.pet'):
        PetProjectDir = os.path.splitext(PetProjectFile)[0] + '.ptd'
    elif PetProjectFile.lower().endswith('.petr'):
        PetProjectDir = os.path.splitext(PetProjectFile)[0] + '.ptdR'
    else:
        logging.warning('Possible garbage in the database: %s', PetProjectFile)
        return 1

    if os.path.isdir(PetProjectDir):
        PetProjectName = os.path.splitext(os.path.split(PetProjectFile)[1])[0]
        PetOceanPath = os.path.join(PetProjectDir, 'Ocean')        # Creating the correct path to the Ocean dir

        logging.debug('Calling CreatePetProjectXMLFileName(PetProjectName, PetProjectFile, PetOceanPath) as (%s, %s, %s)', PetProjectName, PetProjectFile, PetOceanPath)
        PetProjectXMLFileName = CreatePetProjectXMLFileName(PetProjectName, PetProjectFile, PetOceanPath)

        global XMLFilesStore
        
        logging.debug('XMLFilesStore: %s', XMLFilesStore)
        if os.path.isdir(XMLFilesStore):
            PetProjectXMLFileExist=glob.glob(PetProjectXMLFileName)
            logging.debug('PetProjectXMLFileExist = %s', str(PetProjectXMLFileExist))
            if not PetProjectXMLFileExist:
                try:
                    logging.debug('Will create XMLFile %s', PetProjectXMLFileName)
                    with codecs.open(PetProjectXMLFileName, 'w', 'utf-8') as out:
                        PetXML.writexml(out)
                    #print(PetXML.toprettyxml())
                    logging.warning('%s was created.', PetProjectXMLFileName)
                    return 0
                except:
                    logging.warning('Problem writing file %s', PetProjectXMLFileName)
                    return 2
            else:
                logging.warning('We found a XML, it should not be there, probably comming from Petrel %s', PetProjectXMLFileName)
                return 3
        else:
            logging.warning('No Ocean dir.. Deprecated.. Project %s', PetProjectFile)
            return 4
    else:
        logging.warning('No Project dir? something may be wrong. Project %s', PetProjectFile)
        return 5

def CreateXML(PetProjectFile,project_lastmodified,project_name,project_size,process_exit_code):
    # Creating the object PetXML.
    PetXML = Document()
    PetXMLProject = PetXML.createElement("Project")
    PetXML.appendChild(PetXMLProject)

    # One the elements inside <Project> ... </Project>
    PetXMLProjectFile = PetXML.createElement("ProjectFile")
    PetXMLProject.appendChild(PetXMLProjectFile)
    PetXMLProjectFile.appendChild(PetXML.createTextNode(PetProjectFile)) # Here we assign the text.

    # We do the same with the other elements.
    PetXMLProjectFileLastModified = PetXML.createElement("ProjectFileLastModified")
    PetXMLProject.appendChild(PetXMLProjectFileLastModified)
    PetXMLProjectFileLastModified.appendChild(PetXML.createTextNode(project_lastmodified))
        
    PetXMLName = PetXML.createElement("Name")
    PetXMLProject.appendChild(PetXMLName)
    PetXMLName.appendChild(PetXML.createTextNode(project_name))
       
    PetXMLSize = PetXML.createElement("Size")
    PetXMLProject.appendChild(PetXMLSize)
    PetXMLSize.appendChild(PetXML.createTextNode(project_size))
    
    PetXMLPetrelEC = PetXML.createElement("exit_code")
    PetXMLProject.appendChild(PetXMLPetrelEC)
    PetXMLPetrelEC.appendChild(PetXML.createTextNode(process_exit_code))

    return PetXML
    
# Connecting to DB.
logging.debug('Connecting to: %s',dbConnectionString)
try:
    db=postgresql.open(dbConnectionString)
except:
    logging.warning('Could not connect to DB: %s', str(sys.exc_info()[0]))
    raise

if not os.path.isdir(XMLFilesStore):
    logging.warning('%s is not accesible, verify access or adjust configuration.', XMLFilesStore)
    sys.exit(1)
    
logging.warning('##### Process started. #####')

logging.warning('Creating XML files (phase 1)')
# Creating a query to DB to get the projects which we need to generate a XML for (process_flag between 10 and 19)
sqlQuery = 'SELECT project_filename FROM projects WHERE (process_flag >= 10 AND process_flag < 20) OR (process_exit_code > 0 AND process_exit_code < 10 AND process_error_count > 3)'
logging.debug('Query: %s', sqlQuery)
for sqlResult in db.prepare(sqlQuery):
    PetProjectFile = sqlResult[0]
    # Now we query for the specific fields of each project.
    sqlQuery = 'SELECT project_lastmodified, project_name, project_size, process_exit_code FROM projects WHERE project_filename = $$' + PetProjectFile + '$$'
    logging.debug('Query: %s', sqlQuery)
    sql = db.prepare(sqlQuery)
    if sql.first() is not None:      # We are supposed to receive something, but in case we don't we don't make a big deal
        project_lastmodified = str(sql.first()[0])
        #project_name = str(sql.first()[1])
        project_name = os.path.split(PetProjectFile)[1]
        project_size = str(sql.first()[2])
        process_exit_code = str(sql.first()[3])

        logging.warning('Calling CreateXML(%s,%s,%s,%s,%s)',PetProjectFile,project_lastmodified,project_name,project_size,process_exit_code)
        PetXML = CreateXML(PetProjectFile,project_lastmodified,project_name,project_size,process_exit_code)
       
        if StoreXML(PetXML, PetProjectFile) == 0:
            logging.warning('StoreXML() is not 0, calling UpdateDB(%s)', PetProjectFile)
            UpdateDB(PetProjectFile)
        time.sleep(1)

logging.warning('Cleaning up XMLs or compressed XMLs of inexistent projects (phase 2)')

# We need to define these lists, just because we need to ignore the deletion of XMLs from the shares we cannot reach
inaccessible_paths = []
sqlQueryExtra='' # We have to initialize this one.
inaccessible_paths_count = 0 # And this one.
for path in paths:
    if not os.path.exists(path):
        inaccessible_paths.append(path)
        logging.debug('Path %s is inaccessible', path)

if len(inaccessible_paths) > 0:
    sqlQueryExtra = ' AND ( '
    for path in inaccessible_paths:
        sqlQueryExtra += ' project_filename NOT ILIKE $$' + path + '%$$ '
        inaccessible_paths_count += 1
        while (inaccessible_paths_count < len(inaccessible_paths)):
            sqlQueryExtra += 'OR'
    sqlQueryExtra += ')'

sqlQuery = r"SELECT project_filename,project_name,id FROM projects WHERE last_crawl_date < ( (SELECT max(last_crawl_date) from projects) - interval '2 days')" + sqlQueryExtra
logging.debug('Query: %s', sqlQuery)
for sqlResult in db.prepare(sqlQuery):
    PetProjectFile = sqlResult[0]
    PetProjectName = sqlResult[1]
    sqlRecordId = str(sqlResult[2])
    logging.debug('PetProjectFile: %s, PetProjectName: %s, sqlRecordId: %s', PetProjectFile, PetProjectName, sqlRecordId)
    if PetProjectFile.lower().endswith('.pet'):
        PetProjectDir = os.path.splitext(PetProjectFile)[0] + '.ptd'
    elif PetProjectFile.lower().endswith('.petr'):
        PetProjectDir = os.path.splitext(PetProjectFile)[0] + '.ptdR'
    else:
        logging.info('garbage in the database: %s', PetProjectDir)

    if os.path.isfile(PetProjectFile) and os.path.isdir(PetProjectDir):
        logging.warning('%s was found, ignoring', PetProjectFile)
    else:
        logging.debug('%s or %s not found. Calling CreatePetProjectXMLFileName(%s, %s, %s)', PetProjectFile, PetProjectDir, PetProjectName, PetProjectFile, PetProjectDir)
        PetProjectXMLFileName = CreatePetProjectXMLFileName(PetProjectName, PetProjectFile, PetProjectDir)
        PetProjectXMLFileNameGZ = PetProjectXMLFileName + '.gz'
        # XML file removal (if exists)
        if os.path.isfile(PetProjectXMLFileName):
            try:
                os.remove(PetProjectXMLFileName)
                logging.info('%s removed.', PetProjectXMLFileName)
            except:
                logging.info('Issues while removing %s', PetProjectXMLFileName)

        # Compressed file removal (if exists)
        if os.path.isfile(PetProjectXMLFileNameGZ):
            try:
                os.remove(PetProjectXMLFileNameGZ)
                logging.info('%s removed.', PetProjectXMLFileNameGZ)
            except:
                logging.info('Issues while removing %s', PetProjectXMLFileNameGZ)

        sqlQuery='DELETE FROM projects where id = ' + sqlRecordId
        logging.debug('Query: %s', sqlQuery)
        sql = db.prepare(sqlQuery)
        sql()
        logging.warning('%s was removed from the store.', PetProjectFile)
    time.sleep(1)


logging.warning('Cleaning up orphaned XML files (phase 3)')
# Get the list of Files
XMLFileList = os.listdir(XMLFilesStore)
logging.debug('After XMLFileList: %s', str(XMLFileList))
sqlQuery = r"SELECT project_filename,project_name FROM projects"
logging.debug('Query: %s', sqlQuery)
for sqlResult in db.prepare(sqlQuery):
    PetProjectFile = sqlResult[0]
    PetProjectName = sqlResult[1]
    PetProjectXMLFileName = CreatePetProjectXMLFileName(PetProjectName, PetProjectFile, 'not important')
    PetProjectXMLFileNameGZ = PetProjectXMLFileName + '.gz'
    logging.debug('PetProjectFile: %s, PetProjectName: %s, os.path.split(PetProjectXMLFileName)[1]: %s', PetProjectFile, PetProjectName, os.path.split(PetProjectXMLFileName)[1])
    try:
        XMLFileList.remove(os.path.split(PetProjectXMLFileName)[1])
    except:
        logging.debug('Could not find %s in the file system', PetProjectXMLFileName)

    try:
        XMLFileList.remove(os.path.split(PetProjectXMLFileNameGZ)[1])
    except:
        logging.debug('Could not find %s in the file system', PetProjectXMLFileNameGZ)

logging.debug('After XMLFileList: %s', str(XMLFileList))
if len(XMLFileList) > 0:
    for XMLFile in XMLFileList:
        XMLFilePath = os.path.join(XMLFilesStore, XMLFile)
        try:
            os.remove(XMLFilePath)
            logging.info('%s removed.', XMLFilePath)
        except:
            logging.warning('Issues while removing file: %s', XMLFilePath)
            time.sleep(1)

logging.warning('***** Process finished *****')
