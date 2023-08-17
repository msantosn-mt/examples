# Version v0.1 / miguel@kadme.com / Oct 2012
# Version 10000 / June 2015.

# Needed this before execution: set PYTHONIOENCODING=cp437:backslashreplace

# We have to load all these modules
# sys and os are mandatory.
# glob we need it for checking the existence of files with wildcards as os.path does not allow this.
# time for some timestamp evaluations
# postgresql to query the database
# multiprocessing to control the threads when searching for petrel projects.
# configuration is our local configuration specified in configuration.py
# subprocess to launch some system calls.
# string provides string manipulation functionalities.
# logging for log creation.
# mimetypes to check what kind of file is it.
import sys, os, glob, time, postgresql, multiprocessing, uuid, logging, subprocess, string, localconfiguration, mimetypes

# Get all from the localconfiguration.py file.
from localconfiguration import *

# Define the log file
if LogLevel is 'DEBUG':
    logging.basicConfig(level=LogLevel, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    LocatorThreads=1
else:
    logging.basicConfig(filename='logs\petrelLocator.log', level=LogLevel, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    print('Sending output to logfile.')

# Define a function called FindPtdDir that will crawl the file system for *.pet or *.petR files
# and once it has found a file, this one will call another function called ValidatePetProject
def FindPtdDir(root_path):
    """ Find the valid *.pet files. """
    if os.path.isdir(os.path.join(root_path)):
        logging.warning('Crawling started for: %s', root_path)

        ### We have two methods to traverse, windows and native using os.walk, the latest takes much more time.
        ### With windows, we have two alternatives, check the output of the command or write the output to a file,
        ### the last is useful when we have issues with different codepages or non-western alphabets.
        if TraversePathMech == 'native':
            logging.debug('Traverse Mechanism is native')
            for path, dirs, files in os.walk(root_path, followlinks=True):
                """ Ignore the ~snapshot directories """
                if '~snapshot' not in str(path):
                    for dir in dirs:
                        """ Normalize the name of the paths, (dir=file) ptd=pet and ptdR=petR  """
                        if dir.lower().endswith('.ptd'):
                            ValidatePetProject(path, dir, ".pet")
                        elif dir.lower().endswith('.ptdr'):
                            ValidatePetProject(path, dir, ".petR")
        else:
            if TraversePathMech == 'windows':
                logging.debug('Traverse Mechanism is windows')
                FindCmd = 'dir /A:D /B /S *.ptd*'
                logging.info('Will execute "%s" in "%s"', FindCmd, root_path)
                FindOutput = subprocess.check_output(FindCmd, shell=True, universal_newlines=True, cwd=root_path)
                logging.info('Execution of "%s" in "%s" finished', FindCmd, root_path)
                #logging.info('Result of the command: %s', FindOutput)
                FindOutputLines = FindOutput.splitlines()
            ### We have two ways to traverse, windows2file will store the output of the dir command in a file
            if TraversePathMech == 'windows2file':
                logging.debug('Traverse Mechanism is windows2file')
                #FindCmd = 'dir /A:D /B /S *.ptd* >' + FindOutputFile
                FindCmd = 'cmd /u /c "dir /A:D /B /S *.ptd* >' + FindOutputFile + '"'
                logging.info('Will execute "%s" in "%s"', FindCmd, root_path)
                FindOutput = subprocess.call(FindCmd, shell=True, universal_newlines=True, cwd=root_path)
                logging.info('Execution of "%s" in "%s" finished', FindCmd, root_path)
                #FindOutputLines = open(FindOutputFile, encoding=sys.stdout.encoding)
                FindOutputLines = open(FindOutputFile, 'r', encoding='utf-16-le')

            for line in FindOutputLines:
                line = line.strip()  # In case our lines contain spaces at the beginning or end
                if '~snapshot' not in line:
                    path = os.path.split(line)[0]
                    dir = os.path.split(line)[1]
                    """ Normalize the name of the paths, (dir=file) ptd=pet and ptdR=petR  """
                    if dir.lower().endswith('.ptd'):
                        ValidatePetProject(path, dir, ".pet")
                    elif dir.lower().endswith('.ptdr'):
                        ValidatePetProject(path, dir, ".petR")
                            
        logging.warning('Crawling finished for: %s', root_path)
    else:
        logging.warning('Cannot access the path: %s', root_path)
        
# Define a function that will validate the Project, so we do not waste time calling Petrel
# We check for:
# That the project file exists and matches the project dir, project dir must have an Ocean directory. PetProjectFlag=20 (invalid project)
# Size of the project, we can define if projects are too big we skip them. PetProjectFlag=10 (too big)
# Number of the characters in the path, Petrel only works with 160 chars. PetProjectFlag=11 (file path too long)
# We can blacklist a specific Petrel version. PetProjectFlag=12 (uncompatible version)
# 
# If these checks are successful, then we verify if we do not have already an XMLCreated. PetProjectFlag=1 (new project)
# If we do, we need to compare the timestamps between the Project and the XMLFile. PetProjectFlag=2 (update)
# If the project had invalid XML files created by the plug-in, we delete them and project will be processed. PetProjectFlag=3 (forced process)
#
# If none of the above, then we assume project is fine and up to date and we skip it. PetProjectFlag=0 (everything is cool)
#
# Summary if PetProjectFlag is 0 we will not do anything, 1-9 (ok to process), 10-19 (not ok, but can extract information), 20+ (ignore them, they are invalid)
def ValidatePetProject(path, dir, PetProjectType):
    PetProjectName = os.path.splitext(dir)[0]            # Getting rid of the extension
    PetProjectFile = os.path.join(path, PetProjectName + PetProjectType)
    PetProjectDir = os.path.join(path, dir)
    PetProjectInfoFile = os.path.join(PetProjectDir, 'project_information.xml')
    PetOceanPath = os.path.join(PetProjectDir, 'Ocean')        # Creating the correct path to the Ocean dir
    PetProjectFlag = 0        # Have to be sure this is 0 before we start.
    PetProjectSize = 0        # Have to be sure this is 0 before we start.
    KeepEvaluating = 1        # Cheap logic fix, we enter in a logic flaw, when we evaluate for example size and the XML is there, we used to mark for processing but we need to ignore them.
    PetProjectFileMTime = 0 # We need to enter with clean values. ;)
    logging.debug('PetProjectName: %s, PetProjectFile: %s, PetProjectDir: %s, PetProjectInfoFile: %s, PetOceanPath: %s', PetProjectName, PetProjectFile, PetProjectDir, PetProjectInfoFile, PetOceanPath)


    if os.path.isdir(XMLFilesStore):
        #import pdb; pdb.set_trace()
        PetProjectXMLFileName = PetProjectName + '___' + str(uuid.uuid3(uuid.NAMESPACE_URL, PetProjectFile)) + '.xml'
        PetProjectXMLFile = os.path.join(XMLFilesStore, PetProjectXMLFileName)
        PetProjectXMLFileNameGZ = PetProjectXMLFileName + '.gz'
        PetProjectXMLFileGZ = os.path.join(XMLFilesStore, PetProjectXMLFileNameGZ)

    PetProjectXMLFile=glob.glob(PetProjectXMLFile) # Verify if it exists in the FS already. Creating an array, legacy code, don't bother.
    PetProjectXMLFileGZ=glob.glob(PetProjectXMLFileGZ) # Verify if it exists in the FS already. Creating an array, legacy code, don't bother.

    if len(PetProjectXMLFileGZ) > 0:
        for XMLFileGZ in PetProjectXMLFileGZ:
            XMLFileGZMimeType = mimetypes.guess_type(XMLFileGZ)[1]
            XMLFileGZFileSize = os.path.getsize(XMLFileGZ)
            # We check if the GZIP file is valid, by extracting the mime type and the size should be at least 10% of the compress_threshold.
            # Also if there is an XML hanging around, we assume the GZIP file is outdated.
            # And finally, if we are not supposed to compress e.g. compress is not 1. We have to remove it in any of these cases.
            if XMLFileGZMimeType[1] != 'gzip' or XMLFileGZFileSize < int(compress_threshold*.1) or len(PetProjectXMLFile) > 0 or compress != 1:
                PetProjectXMLFileGZ.remove(XMLFileGZ)
                logging.warning('%s found, but seems not valid. MIME: %s, Size: %s', XMLFileGZ, XMLFileGZMimeType, XMLFileGZFileSize)
                try:
                    logging.warning('Removing invalid compressed file %s', XMLFileGZ)
                    os.remove(XMLFileGZ)
                except:
                    logging.warning('ERROR: Could not remove file: %s', XMLFileGZ)
            else:
                logging.debug('Compressed XML found. Seems legit.')

    # Verify if we have an entry already in the DB.
    ExistsOnDB = GetPetProjectCountFromDB(PetProjectFile) # Exists in the DB? We received the count
    logging.debug('Exists on DB: %s', str(ExistsOnDB))

    if not os.path.isdir(PetOceanPath) or not os.path.isfile(PetProjectFile):
        logging.warning('%s was not found or there is no Ocean subdirectory', PetProjectFile)
        PetProjectFlag = 20
        KeepEvaluating = 0
    else:
        PetProjectFileMTime = int(os.stat(PetProjectFile).st_mtime)    # Get the modification timestamp of the *.pet or *.petR file as integer.
        logging.debug('%s mtime is %s', PetProjectFile, str(PetProjectFileMTime))
        if ExistsOnDB > 0:
            PetProjectDataFromDB = GetPetProjectDataFromDB(PetProjectFile) # Retrieve the data from DB.
            PetProjectFileMTimeFromDB = PetProjectDataFromDB[0] # Second item in the list contains the timestamp (which is already an integer)
            PetProjectSizeFromDB = PetProjectDataFromDB[1] # From the DB, we get the timestamp, we create a tuple and then create a timestamp which for practical results we convert to integer :)
            logging.debug('PetProjectFileMTimeFromDB: %s, PetProjectSizeFromDB: %s', str(PetProjectFileMTimeFromDB), str(PetProjectSizeFromDB))
        else:
            PetProjectFileMTimeFromDB = 0


        # We compare the timestamps, if they are the same, then there will be no case in getting the size of the folder again. We have been through this before ;-)
        if PetProjectFileMTime == PetProjectFileMTimeFromDB:
            logging.debug('The timestamp matches between FS and DB %s/%s', str(PetProjectFileMTime), str(PetProjectFileMTimeFromDB))
            PetProjectSize = PetProjectSizeFromDB

    if PetProjectFlag == 0 and PetProjectSize == 0 and KeepEvaluating == 1:
        logging.debug('Getting the size of dir %s', PetProjectDir)
        for (path1, dirs1, files1) in os.walk(PetProjectDir):
            for file1 in files1:
                filename1 = os.path.join(path1, file1)
                # We use try, in case file has disappeared we do not crash.
                try:
                    PetProjectSize += os.path.getsize(filename1)
                except:
                    logging.debug('File disappeared %s', filename1)

        if PetProjectSize > MaxPetProjectSize:
            logging.info('Directory %s bigger than the Limit %s', PetProjectDir, str(PetProjectSize))
            if PetProjectXMLFile or PetProjectXMLFileGZ:
                PetProjectFlag = 0
            else:
                PetProjectFlag = 10
            KeepEvaluating = 0

    if PetProjectFlag == 0 and len(PetProjectFile) > 160 and KeepEvaluating == 1:
        logging.warning('Project path is longer than 160 bytes %s', PetProjectFile)
        if PetProjectXMLFile or PetProjectXMLFileGZ:
            PetProjectFlag = 0
        else:
            PetProjectFlag = 11
        KeepEvaluating = 0

    if PetProjectFlag == 0 and os.path.isfile(PetProjectInfoFile) and unsupportedPetrelVersion and KeepEvaluating == 1:
        PetProjectInfoFileContent = open(PetProjectInfoFile)
        UnsupportedVersionString = '<Version>' + unsupportedPetrelVersion
        for line in PetProjectInfoFileContent:
            if UnsupportedVersionString in line:
                logging.warning('%s was edited with Petrel version %s', PetProjectFile, unsupportedPetrelVersion)
                if PetProjectXMLFile or PetProjectXMLFileGZ:
                    PetProjectFlag = 0
                else:
                    PetProjectFlag = 12
                KeepEvaluating = 0
                break
            
    if PetProjectFlag == 0 and KeepEvaluating == 1:
        if not PetProjectXMLFile and not PetProjectXMLFileGZ:
            logging.warning('%s will be processed.', PetProjectFile)
            PetProjectFlag = 1
        else:
            PetProjectXMLFileMTime = 0 # Initialize variable , will use later
            """ We will get rid of the 0-byte size XML files """
            if PetProjectXMLFile:
                if os.path.getsize(PetProjectXMLFile[0]) < 60:
                    logging.warning('Invalid XML found %s', PetProjectXMLFile[0])
                    # We use 'try', in case file has disappeared we do not crash.
                    try:
                        os.remove(PetProjectXMLFile[0])
                        logging.debug('Invalid XML removed %s', PetProjectXMLFile[0])
                    except:
                        logging.warning('Issue trying to remove file %s', PetProjectXMLFile[0])
                else:
                    PetProjectXMLFileMTime = os.stat(PetProjectXMLFile[0]).st_mtime

            # Determine if the XML or Compressed file are updated according to project's timestamp.
            if PetProjectXMLFileGZ:
                PetProjectXMLFileMTime = os.stat(PetProjectXMLFileGZ[0]).st_mtime

            if (PetProjectXMLFileMTime + timeTolerance) < PetProjectFileMTime:
                logging.warning('%s was modified.', PetProjectFile)
                PetProjectFlag = 2
            elif (PetProjectFileMTime == 0):
                logging.warning('%s with invalid XML. Reprocess.', PetProjectFile)
                PetProjectFlag = 3
            else:
                logging.warning('%s is OK.', PetProjectFile)

    # Nice formatting to store in DB.
    PetProjectFileMTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(PetProjectFileMTime))
    
    # Send it to the Store.
    logging.debug('Calling StorePetProject')
    StorePetProject(PetProjectName, PetProjectFile, PetProjectSize, PetProjectFlag, PetProjectFileMTime, ExistsOnDB)

def GetPetProjectCountFromDB(PetProjectFile):
    sqlQuery = 'SELECT count(project_filename) FROM projects WHERE project_filename=$$' + PetProjectFile + '$$'
    sql = db.prepare(sqlQuery)
    logging.debug('Query %s returned %s', sqlQuery, str(int(sql.first())))
    return int(sql.first())

def GetPetProjectDataFromDB(PetProjectFile):
    sqlQuery = 'SELECT project_lastmodified, project_size FROM projects WHERE project_filename=$$' + PetProjectFile + '$$'
    logging.debug('Query %s', sqlQuery)
    sql = db.prepare(sqlQuery)
    PetProjectDataFromDB = []
    # From the DB, we get the date, we need to parse it as a string, we create a tuple and then create a timestamp which for practical results we convert to integer, finally we store them in the list. (2nd item index 1)
    PetProjectDataFromDB.append(int(time.mktime(time.strptime(str(sql.first()[0]),'%Y-%m-%d %H:%M:%S'))))
    PetProjectDataFromDB.append(int(sql.first()[1]))
    logging.debug('PetProjectDataFromDB: %s', str(PetProjectDataFromDB))
    return PetProjectDataFromDB
        
def StorePetProject(PetProjectName, PetProjectFile, PetProjectSize, PetProjectFlag, PetProjectFileMTime, ExistsOnDB):
    # ExistsOnDB = 0 is an Insert, any other value is Update
    if ExistsOnDB == 0:
        sqlQuery = 'INSERT INTO projects(project_filename, project_name, project_lastmodified, project_size, process_flag, last_crawl_date) \
                VALUES($$' + PetProjectFile + '$$,$$' + PetProjectName + '$$,$$' + PetProjectFileMTime + '$$,' + str(PetProjectSize) + ',' + str(PetProjectFlag) + ',NOW())'
    else:
        sqlQuery = 'UPDATE projects set project_size=' + str(PetProjectSize) + ', process_flag=' + str(PetProjectFlag) + ', last_crawl_date=NOW(), \
                project_lastmodified=$$' + PetProjectFileMTime + '$$, project_name=$$' + PetProjectName + '$$ \
                WHERE project_filename=$$' + PetProjectFile + '$$'

    logging.debug('Query: %s', sqlQuery)
    sql = db.prepare(sqlQuery)
    sql()

def main():

    # We need to define these lists, just because we need to. Yes!?
    valid_paths = []
    inaccessible_paths = []
    
    # It is necessary to validate the paths.
    for path in paths:
        if os.path.exists(path):
            valid_paths.append(path)
            logging.debug('Path %s is accessible', path)
        else:
            inaccessible_paths.append(path)
            logging.debug('Path %s is inaccessible', path)

    # Do we have a correct TraversePathMech defined?
    if TraversePathMech is not 'native' and not 'windows' and not 'windows2file':
        logging.warning('Invalid Traverse mechanism defined, duh!')
        return 1

    # Defining the number of threads to process simultaneously.
    # TraversePathMech windows2file cannot run in parallel because the file would be overwritten if 2 tasks end at the same time.
    if TraversePathMech == 'windows2file':
        FindPtdDirProcess = multiprocessing.Pool(processes=1)
    else:
        FindPtdDirProcess = multiprocessing.Pool(processes=LocatorThreads)
    
    FindPtdDirPaths = [FindPtdDirProcess.apply_async(FindPtdDir, (root_path,)) for root_path in valid_paths]
    for FindPtdDirThread in FindPtdDirPaths:
        try:
            print(FindPtdDirThread.get())
        except Exception as e:
            print(str(e))
            logging.warning('Error spawning process: %s', e)

    if len(inaccessible_paths) > 0:
        logging.warning('Error, we were not able to access the following paths: %s', str(inaccessible_paths))


logging.debug('Connecting to: %s',dbConnectionString)
try:
    db=postgresql.open(dbConnectionString)
except:
    logging.warning('Could not connect to DB: %s', str(sys.exc_info()[0]))
    raise


if not os.path.isdir(XMLFilesStore):
    logging.warning('%s is not accesible, verify it or correct configuration.', XMLFilesStore)
else:
    if __name__ == '__main__':
        logging.warning('##### Process started #####')
        main()
        logging.warning('***** Process finished *****')
