# Configuration file for Petrel Scripts.
# What are we going to crawl.
#paths=[ r"\\pertra.locale\detnor\store\petrel\work_osl",
#    r"\\pertra.locale\oslo\t_lager\petrel", # This is the same as \\pertra.locale\detnor\store\petrel\work_osl, we are crawling twice the same resource.
#    r"\\pertra.locale\detnor\store\petrel\work_trd",
#	r"\\pertra.locale\detnor\store\petrel\referanse",
#    r"\\pertra.locale\detnor\store\petrel\resultat_trd",
#    r"\\pertra.locale\detnor\store\petrel\resultat_osl",
#    r"\\pertra.locale\detnor\store\petrel\forretningsutvikling" ]
paths=[ 'Y:\\utm31', 'Y:\\utm32', 'Y:\\utm34', 'X:\\utm31', 'X:\\utm32', 'X:\\utm33', 'X:\\utm34', 'T:\\', 'U:\\', 'W:\\', 'V:\\' ]
TraversePathMech='windows'      # windows = We use the "dir" utility; python = We use os.walk (will be deprecated because it is slow)
                                # windows does not support UNC paths, therefore the paths should be mapped to a drive letter.

LocatorThreads=4                # Number of threads that will be spawned when traversing the file systems.
MaxPetProjectSize=107374182401  # Maximum size of a project to be processed by Petrel.
timeTolerance=900               # Number of seconds of difference between an XML file and Petrel project file.
unsupportedPetrelVersion=''     # If we have an old version of Petrel, populate this with a correct value, if we
                                # have the latest, then we can this variable empty.
#UseXMLFileStore=1				# If set to 0, we will write to the Ocean subdir of the projects, otherwise we will write in XMLFilesStore. Was deprecated, the default behavior is now 1
XMLFilesStore=r"C:\Kadme\petrelLocator\XMLFileStore" # Where are the XMLs locate, this flag depends on UseXMLFileStore
LogLevel="INFO"			# Possible values logging.INFO and logging.DEBUG

# Regarding our local Petrel installation.
PetrelBinary=r"C:\Program Files\Schlumberger\Petrel 2014\Petrel.exe"
PetrelAvailableLicenses=[ 'Petrel_191391163_MAAAIAAABEQQA',
                          'Petrel_131391163_MAAAIAAAAEQQA',
                          'Petrel_171391163_MAAAIAAABNQQA',
                          'Petrel_241391163_MAAAIAAADm+QA' ]
PetrelTimeout=2700              # Number of seconds we give Petrel to process a project, after this we kill it.
# Next parameter is optional, but recommended if installation has several license servers.
PetrelLicenseServers="27000@trdd1-per-lic01,27000@trdd2-per-lic01,27000@trdd3-per-lic01;27000@10.30.192.188;27005@bridgelic"

# LMutil binary (Flexlm packages)
LmutilBin = r"C:\Kadme\petrelLocator\lmutil.exe"

# Our database.
dbConnectionString="pq://petrellocator:L0c4tor123@10.30.192.45/db_petrellocator"

# Starting petrel 2014, we compress the files that are big enough.
compress=1		# 0 - disabled, 1 - enabled
temp_dir=r"C:\Kadme\petrelLocator\TempXMLFileStore" # The XMLs will be written to this directory, and then moved to the XMLFilesStore after they have been slimmed down.
compress_threshold=20971520	# If the output XML file is bigger than 20Mb, we compress it.
