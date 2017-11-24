
import logging
import logging.config
import yaml
# Imports the Google Cloud client library
from google.cloud import storage
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
import os
from stat import *
import win32api
import win32con
import win32file


def setup_logging():
    default_path = 'logging.yaml'
    default_level = logging.INFO
    """Setup logging configuration"""
    path = default_path
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)


def walktree(top, callback):
    ''' recursively descend the directory tree rooted at top,
       calling the callback function for each regular file '''
    files = []
    for i in os.listdir(top):
        pathname = os.path.join(top, i)
        mode = os.stat(pathname).st_mode
        if S_ISDIR(mode):
            # It's a directory, recurse into it
            walktree(pathname, callback)
        elif S_ISREG(mode):
            # It's a file, call the callback function
            fattrib = callback(pathname)
            if fattrib:
                files.append(i)
                logger.info('file attributes returned')
                files.append(fattrib)
            else:
                logger.info('the file does not have any attributes')
        else:
            # Unknown file type, print a message
            print 'Skipping %s' % pathname
    return files

def getfileattrib(path):

    # set up dictionary for file attribute values
    attributes = {}

    # Get cumulative int value of attributes
    intAttributes = win32file.GetFileAttributes(path)
    # Assign individual attributes
    attributes['archive'] = (intAttributes & 32) == 32
    attributes['compressed'] = (intAttributes & 2048) == 2048
    attributes['directory'] = (intAttributes & 16) == 16
    attributes['encrypted'] = (intAttributes & 16384) == 16384
    attributes['hidden'] = (intAttributes & 2) == 2
    attributes['normal'] = (intAttributes & 128) == 128
    attributes['notIndexed'] = (intAttributes & 8192) == 8192
    attributes['offline'] = (intAttributes & 4096) == 4096
    attributes['readonly'] = (intAttributes & 1) == 1

    return attributes

# TOGGLE ARCHIVE BIT TO ALLOW FOR BACKUP
# def togglefileattribute(filename, fileattribute, value):
#      """Turn a specific file attribute on or off, leaving the other
#      attributes intact.
#      """
#
#      if value:
#         bitvector |= fileattribute
#      else:
#          bitvector &= ~fileattribute
#          win32file.SetFileAttributes(filename, bitvector)


def create_transfer_client():
    return discovery.build('storagetransfer', 'v1')


def upload_blob(bn, sfn, dbn):
    """Uploads a file to the bucket."""
    sc = storage.Client.from_service_account_json(settings['gcloud']['key'])
    bucket = sc.get_bucket(bn)
    blob = bucket.blob(settings['gcloud']['destination_blob_name'])

    blob.upload_from_filename(sfn)

    print('File {} uploaded to {}.'.format(
        source_file_name,
        dbn))


if __name__ == '__main__':

    # Open settings file for gcloud and project settings
    with open("settings.yaml", "r") as f:
        settings = yaml.load(f)
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info('*** STARTING MEDGIS BACKUP SCRIPT ***')
    # List Settings
    logger.info('SETTINGS CONFIG FILE: ')
    logger.info(settings)
    # The ID of the Google Cloud Platform Console project that the Google service
    # account is associated with.
    logger.info('PROJECT_ID: ' + settings['gcloud']['project_id'])
    # Edit the dirpath in the setting.yaml file for the source files to be uploaded
    logger.info('Checking Files in the Source Directory: ' + settings['project']['dirpath'])
    # Search for files in dirpath directory and callback getfileattrib to get attributes
    fa=[]
    fa.append(walktree(settings['project']['dirpath'], getfileattrib))

    # store archive bit value to determine if file has been backed up
    # Note: File may have been backed up to tape and archive bit set

   # Create Code to iterate list of dictionaries
    archive_attrib = fa.get('archive')
    if archive_attrib:
        logger.info('The Archive Attribute Value: ' + str(archive_attrib))
    else:
        logger.info('The Archive Attribute Value: ' + str(archive_attrib))
        logger.info('The file has already been backed up')
        # Call ogglefileattribute()???? to force backup?

    # Instantiates a client
    storage_client = storage.Client.from_service_account_json(settings['gcloud']['key'])

    #################################################################################
    # 1. ADD test to determine if bucket already exists                                #
    # 2. CREATE bucket name using appended data and time?                              #
    #################################################################################

    # The name for the test bucket
    test_bucket_name = settings['gcloud']['test_bucket_name']
    # Creates the new bucket
    # bucket = storage_client.create_bucket(test_bucket_name)
    # Make an authenticated API request
    buckets = list(storage_client.list_buckets())
    logger.info(buckets)

    # Upload an object to a bucket
    source_file_name = settings['project']['testfile']
    logger.info('test file for upload: ' + settings['project']['testfile'])
    destination_blob_name = settings['gcloud']['destination_blob_name']
    upload_blob(test_bucket_name, source_file_name, destination_blob_name)

    buckets = list(storage_client.list_buckets())
    logger.info(buckets)


