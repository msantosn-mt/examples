# Version 10000 / June 2015.

# Needed this before execution: set PYTHONIOENCODING=cp437:backslashreplace

# We have to load all these modules
# sys and os are mandatory.
# time for some timestamp evaluations
# postgresql to query the database
# localconfiguration is our local configuration specified in localconfiguration.py
# subprocess is to manage the spawned Petrel process.
# logging for writing report to file
# re for regular expressions
# random for random numbers generation
# gzip for compressing files.
# mimetypes to detect the type of file.
import sys, os, time, postgresql, subprocess, uuid, logging, re, random, localconfiguration, gzip, mimetypes, fileinput, shutil

# To manipulate the XML (test the validity of the XML).
import xml.sax

# Get all from the localconfiguration.py file.
from localconfiguration import *

# Define the log file
if LogLevel is 'DEBUG':
    logging.basicConfig(level=LogLevel, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
else:
    logging.basicConfig(filename='logs\petrelProcessor.log', level=LogLevel, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    print('Sending output to logfile.')


logging.debug('Connecting to: %s',dbConnectionString)
try:
    db=postgresql.open(dbConnectionString)
except:
    logging.critical('Could not connect to DB: %s', str(sys.exc_info()[0]))
    print('Error connecting to the database.')
    raise

# We define a function to store data. Not big thing.
def StorePetProject(PetProjectFile, PetProjectProcCode, PetrelProcessingTime):
    sqlQuery = 'UPDATE projects SET last_process_date=NOW(), process_flag=0, processing_time=' + str(PetrelProcessingTime) + ', \
               process_exit_code=' + str(PetProjectProcCode) + ' WHERE project_filename=$$' + PetProjectFile + '$$'
    logging.debug('sqlQuery: %s', sqlQuery)
    sql = db.prepare(sqlQuery)
    sql()
    # We have to keep track of how many times Petrel has failed to process.
    if PetProjectProcCode == 0:
        sqlQuery = 'UPDATE projects SET process_error_count = 0 WHERE project_filename=$$' + PetProjectFile + '$$'
    else:
        sqlQuery = 'UPDATE projects SET process_error_count = process_error_count + 1 WHERE project_filename=$$' + PetProjectFile + '$$'
    logging.debug('sqlQuery: %s', sqlQuery)
    sql = db.prepare(sqlQuery)
    sql()

def GetPetrelLicense():
    NumberPetrelAvailableLicenses = len(PetrelAvailableLicenses) - 1 # We start counting from 0
    # Verify existence of lmutil binary if not just take a random license
    if (os.path.exists(LmutilBin)):
        # For each entry in the array, ask the server
        for PetrelAvailableLicense in PetrelAvailableLicenses:
            LmutilResult = '' # Have to initialize
            LmutilCmd = LmutilBin + ' lmstat -f ' + PetrelAvailableLicense
            if 'PetrelLicenseServers' in locals():
                LmutilCmd = LmutilCmd + ' -c ' + PetrelLicenseServers
            logging.debug('Command to execute: %s', LmutilCmd)
            try:
                LmutilResult = subprocess.check_output(LmutilCmd, shell=True, timeout=60, universal_newlines=True)
                logging.debug('LmutilResult: %s', LmutilResult)
            except:
                logging.info('An issue with %s, server down or wrong variables', LmutilBin)
            if len(LmutilResult) > 0 and PetrelAvailableLicense in str(LmutilResult):
                try:
                    string1 = re.search('Users of ' + PetrelAvailableLicense + '.+ licenses? in use',LmutilResult).group() # We need to find something like this: Users of Petrel_11391094_MMAAAAA:   (Total of # license issued;   Total of # license in use)
                    string2 = re.search('Total of [0-9]+ license.*issued;',string1).group() # We need to find something like this in the string1: Total of # license(s) issued
                    TotalLicenses = re.search('[0-9]+',string2).group() # We need to find the total of licenses
                    logging.debug('TotalLicenses: %s', TotalLicenses)
                    string2 = re.search(';.*Total of [0-9]+ license.*in use',string1).group() # We need to find something like this in the string1: Total of # license(s) in use
                    TotalLicensesInUse = re.search('[0-9]+',string2).group() # We need to find the total of licenses in use
                    logging.debug('TotalLicensesInUse: %s', TotalLicensesInUse)
                except:
                    logging.warning('Could not find any useful information when we executed Lmutil: %s', LmutilCmd)
                    break
                if ((int(TotalLicenses) - int(TotalLicensesInUse)) > 0):
                    PetrelLicense = PetrelAvailableLicense
                    logging.info('Found available license: %s', PetrelLicense)
                    return PetrelLicense
                    break
    else:
        logging.warning('Did not locate the binary lmutil.exe')

    PetrelLicense = PetrelAvailableLicenses[random.randint(0, NumberPetrelAvailableLicenses)]
    logging.info('Choosing random license for petrel: %s', PetrelLicense)
    return PetrelLicense
  
 
#
# This is a batch process, in summary, we get from DB all the projects that can be processed by petrel (process_flag=1-9)
# 1 - No XML found
# 2 - Outdated XML found.
# 6 to 9 - Not defined yet.
#
# We then verify if there is a LockFile, if there is we set PetProjectCode = 1
# We verify we see the file, as it may have disappeared, if we cannot find it we set PetProjectCode = 2
# 3 - Petrel was killed.
# 4 - XML file is invalid.
# 5 - XML file may be valid but no useful metadata.
# 6 - Could not trim down the temporary XML, something was wrong with what petrel left us.
# 7 - A compressed file had to be created, but for some reason it failed. We kept the original XML file.
# 8 - Could not move the XML from temp_dir to XMLFileStore
# Verification that we do have Petrel installed, if we do not find it, we just quit.

# We are ready to ask the DB what projects do we have. The enter into a for for each project.
logging.warning('##### Process started #####')

if not os.path.isdir(XMLFilesStore):
    logging.warning('XMLFileStore: %s is not accessible, verify access or adjust configuration.', XMLFilesStore)
    sys.exit(1)

if not os.path.isdir(temp_dir):
    logging.warning('temp_Dir: %s is not accessible, verify access or adjust configuration.', temp_dir)
    sys.exit(1)

#sqlQuery = 'SELECT project_filename FROM projects WHERE (process_flag > 0 AND process_flag < 10) OR (process_exit_code=1 OR process_exit_code=2223) ORDER BY last_process_date ASC'
sqlQuery = 'SELECT project_filename FROM projects WHERE (process_flag > 0 AND process_flag < 10) OR (process_exit_code=1 OR process_exit_code=2223) ORDER BY project_size ASC'
logging.debug('sqlQuery: %s', sqlQuery)

for sqlResult in db.prepare(sqlQuery):
    PetrelLicense = GetPetrelLicense() # Get a license for every iteration. Needed because it could be taken while we finish a project and start a new one.
    PetProjectFile = sqlResult[0]
    PetLockFile = str(os.path.splitext(PetProjectFile)[0]) + '.lock'    # Name of the lock file ProjectName.lock
    PetProjectProcCode = 0        # We need this with 0.
    PetrelProcessingTime = 0    # We need a value, no way around it.
    logging.debug('PetProjectFile: %s, PetLockFile: %s', PetProjectFile, PetLockFile)

    if PetProjectProcCode == 0 and not os.path.isfile(PetProjectFile):
        logging.warning('Project cannot be accessed %s', PetProjectFile)
        PetProjectProcCode = 2

    if PetProjectProcCode == 0 and not os.path.exists(PetrelBinary):
        logging.critical('Cannot find Petrel Binary, seems I am wrongly configured: %s', PetrelBinary)
        break

    # We assume everything is cool and ready to call petrel. We use the internal command 'call' to execute petrel, this allow us to run
    # in without displaying a window.
    if PetProjectProcCode == 0:
        logging.warning('Processing: %s', PetProjectFile)

        PetProjectName = os.path.splitext(os.path.split(PetProjectFile)[1])[0]
        PetProjectXMLFileName = PetProjectName + '___' + str(uuid.uuid3(uuid.NAMESPACE_URL, PetProjectFile)) + '.xml'
        PetProjectXMLFileNameTemp = PetProjectXMLFileName + '.tmp'
        PetProjectXMLFileNameGZ = PetProjectXMLFileName + '.gz'
        PetProjectXMLFile = os.path.join(XMLFilesStore, PetProjectXMLFileName)
        PetProjectXMLFileGZ = os.path.join(XMLFilesStore, PetProjectXMLFileNameGZ)
        # If temp_dir is defined, we will write the XML here, remove the leading spaces then remove the indentation to make it slimmer and finally write it to the XMLFilesStore
        PetProjectXMLFileTemp = os.path.join(temp_dir, PetProjectXMLFileNameTemp)
        PetProjectXMLFileNormalized = os.path.join(temp_dir, PetProjectXMLFileName)

        # first and foremost, we need to remove the compressed XML. If it does not work it is ok, we don't expect it to be there. :)
        if os.path.isfile(PetProjectXMLFileGZ):
            try:
                os.remove(PetProjectXMLFileGZ)
                logging.debug('Removed compressed file: %s', PetProjectXMLFileGZ)
            except Exception as e:
                logging.warning('Could not remove compressed file: %s', e)

        if '2012' in PetrelBinary:
            PetrelCommand = '"' + PetrelBinary + '" /licensePackage ' + PetrelLicense + ' /readonly /nosplashscreen \
                -exec "Kadme.ProjectSaver.ProjectSaver, Kadme.ProjectSaver" SaveToFile /soption \
                "Kadme.ProjectSaver=OutputFile=' + PetProjectXMLFileTemp + '" "' + PetProjectFile + '"'
        elif '2013' in PetrelBinary:
            PetrelCommand = '"' + PetrelBinary + '" /licensePackage ' + PetrelLicense + ' /readonly /nosplashscreen /exec \
                "Kadme.ProjectSaver.ProjectSaver, Kadme.ProjectSaver, Version=1.0.7.0, Culture=neutral, PublicKeyToken=f4796359a966221a" \
                SaveToFile /soption "Kadme.ProjectSaver=OutputFile=' + PetProjectXMLFileTemp + '" "' + PetProjectFile + '"'
        else:
            PetrelCommand = '"' + PetrelBinary + '" /readonly /nosplashscreen /licensePackage ' + PetrelLicense + ' -exec "Kadme.ProjectSaver.ProjectSaver, Kadme.ProjectSaver" \
                SaveToFile /soption "Kadme.ProjectSaver=OutputFile=' + PetProjectXMLFileTemp + '" "' + PetProjectFile + '"'


        logging.debug('Executing: %s', PetrelCommand)

        # We will get the timestamp to calculate how much time Petrel took.
        timestamp1 = int(time.time())
        # We will execute petrel now!! WooHoo!!
        try:
            PetrelTask = subprocess.call(PetrelCommand, shell=False, timeout=PetrelTimeout)
            PetProjectProcCode = PetrelTask
        except subprocess.TimeoutExpired:
            logging.info('Petrel did not finish on time. We kill it')
            PetProjectProcCode = 3
            if os.path.isfile(PetProjectXMLFileTemp):
                try:
                    os.remove(PetProjectXMLFileTemp)
                except:
                    logging.warning('Could not remove the XML file %s, %s', PetProjectXMLFileTemp, str(sys.exc_info()))
        except:
            logging.warning('Petrel error %s', str(sys.exc_info()))

        # Taking timestamps
        timestamp2 = int(time.time())
        PetrelProcessingTime = timestamp2 - timestamp1
        logging.info('Error code: %s Processing time: %s', str(PetProjectProcCode), str(PetrelProcessingTime))

        # Verifying validity of the XML file.
        if os.path.isfile(PetProjectXMLFileTemp): # First we verify it exists, probably petrel did not create XML because it was killed.

            # Getting size of the XML to verify it has metadata.
            try:
                XMLFileSize = os.path.getsize(PetProjectXMLFileTemp)
                logging.debug('XMLFileSize: %s', XMLFileSize)
            except:
                logging.warning('Cannot get the size of the file %s', PetProjectXMLFileTemp)
                XMLFileSize = 0

            # Verifying if it has metadata or not, 60 bytes is thought to be invalid.
            if XMLFileSize < 60:
                logging.warning('Petrel created a XML with no metadata %s', PetProjectXMLFileTemp)
                PetProjectProcCode = 5
            else:
                logging.info('Trimming XML %s', PetProjectXMLFileTemp)
                try:
                    with open(PetProjectXMLFileNormalized,'w',encoding='utf-8') as output:
                        for line in open(PetProjectXMLFileTemp,'r',encoding='utf-8'):
                            output.writelines(line.lstrip())
                except Exception as e:
                    logging.warning('Failure to trim XML %s, because: ', PetProjectXMLFileTemp, e)
                    PetProjectProcCode = 6

            timestamp3 = int(time.time())

            if PetProjectProcCode != 5 and PetProjectProcCode != 6: 
                logging.info('Parsing XML: %s', str(PetProjectXMLFileNormalized))
                try:
                    PetProjectXMLNormalizedFH = open(PetProjectXMLFileNormalized,'r',encoding='utf-8')
                    PetXMLParser = xml.sax.make_parser()
                    PetXMLParser.parse(PetProjectXMLNormalizedFH)
                except Exception as e:
                    logging.warning('We ended up with an invalid XML %s, because: ', PetProjectXMLFileNormalized, e)
                    PetProjectProcCode = 4
                try:
                    PetProjectXMLNormalizedFH.close()
                except Exception as e:
                    logging.warning('Could not close this file handle %s, because: ', PetProjectXMLFileNormalized, e)

            timestamp4 = int(time.time())

            # Time to delete (if we have any errors or if we don't use the temp XML anymore)
            if PetProjectProcCode == 4:
                try:
                    os.remove(PetProjectXMLFileNormalized)
                    logging.debug('Removing XML file: %s', PetProjectXMLFileNormalized)
                except:
                    logging.warning('Could not remove the XML file: %s', PetProjectXMLFileNormalized)
            else:
                try:
                    os.remove(PetProjectXMLFileTemp)
                    logging.debug('Removing temp XML file: %s', PetProjectXMLFileTemp)
                except:
                    logging.warning('Could not remove the temp XML file: %s', PetProjectXMLFileTemp)

                # Do we need to compress? then compress it to the final location, if not, just move it to the final location.
                if compress == 1 and XMLFileSize > compress_threshold:
                    logging.info('Compressing %s', PetProjectXMLFileGZ)
                    try:
                        f_in = open (PetProjectXMLFileNormalized, 'rb')
                        f_out = gzip.open(PetProjectXMLFileGZ, 'wb')
                        f_out.writelines(f_in)
                        f_in.close()
                        f_out.close()
                    except Exception as e:
                        logging.warning('Could not compress %s, because: %s', PetProjectXMLFileNormalized, e)
                        PetProjectProcCode = 7

                    if os.path.isfile(PetProjectXMLFileGZ):
                        XMLFileGZMimeType = mimetypes.guess_type(PetProjectXMLFileGZ)
                        XMLFileGZFileSize = os.path.getsize(PetProjectXMLFileGZ)
                        # We check if the GZIP file is valid, by extracting the mime type and the size should be at least 10% of the compress_threshold. Then  get rid of the original XML.
                        if XMLFileGZMimeType[1] != 'gzip' or XMLFileGZFileSize < int(compress_threshold*.1):
                            try:
                                logging.warning('Removing invalid compressed file %s', PetProjectXMLFileGZ)
                                os.remove(PetProjectXMLFileGZ)
                            except:
                                logging.warning('Could not remove file, we should, it looks invalid: %s', PetProjectXMLFileGZ)
                        else:
                            try:
                               os.remove(PetProjectXMLFileNormalized)
                            except:
                               logging.warning('Could not remove file and we do not need it: %s', PetProjectXMLFileNormalized)
                else:
                    try:
                        logging.warning('Moving %s', PetProjectXMLFile)
                        shutil.move(PetProjectXMLFileNormalized, PetProjectXMLFile)
                    except Exception as e:
                        logging.warning('Could not move XML file: %s, because: %s', PetProjectXMLFileNormalized, e)
                        PetProjectProcCode = 8

            # Taking timestamps to report
            timestamp5 = int(time.time())
            TrimmingTime = timestamp3 - timestamp2
            ParsingTime = timestamp4 - timestamp3
            CleaningCompressingTime = timestamp5 - timestamp4
            logging.info('Trimming time: %s, Parsing time: %s,  Cleaning/Compressing/Moving: %s', str(TrimmingTime), str(ParsingTime), str(CleaningCompressingTime))

    # We call the store function.
    logging.debug('Will call StorePetProject function with PetProjectFile: %s, PetProjectProcCode: %s and PetrelProcessingTime: %s', PetProjectFile, str(PetProjectProcCode), str(PetrelProcessingTime))
    StorePetProject(PetProjectFile, PetProjectProcCode, PetrelProcessingTime)

    # We need to wait a little bit in case we have issues with license.
    if PetProjectProcCode == 2223:
        logging.warning('Issue with License server code, will pause the processing and get a new license.')
        time.sleep(30)
        GetPetrelLicense()

logging.warning('***** Process finished. *****')
