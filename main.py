
import logging
import logging.config
import yaml
# Imports the Google Cloud client library
from google.cloud import storage
from googleapiclient import discovery
import os
from stat import *
import win32file
import datetime
import time


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
    # list of dictionaries containing file attributes
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
                logger.info('file attributes returned for file: ' + i)
                fdict = {'filename': i}
                fdict.update(fattrib)
                logger.info('Creation Date: ' + fdict['createddate'])
                logger.info('Creation Date: ' + fdict['modifieddate'])
                logger.info('File Size (Bytes): ' + str(fdict['filesize']))
                files.append(fdict)
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
    fsize = os.path.getsize(path)
    ctime = time.ctime(os.path.getmtime(path))
    mtime = time.ctime(os.path.getctime(path))
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
    attributes['filesize'] = fsize
    attributes['createddate'] = ctime
    attributes['modifieddate'] = mtime

    return attributes


def create_transfer_client():
    return discovery.build('storagetransfer', 'v1')


def upload_blob(bn, sfn, dbn):
    """Uploads a file to the bucket."""
    sc = storage.Client.from_service_account_json(settings['gcloud']['key'])
    bucketup = sc.get_bucket(bn)
    blob = bucketup.blob(dbn)
    blob.upload_from_filename(sfn)

    print('File {} uploaded to {}.'.format(
        source_file_name,
        dbn))


if __name__ == '__main__':

    # Open/Load settings file for gcloud and project settings
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
    logger.info('Source Directory: ' + settings['project']['dirpath'])

    #################################################################################
    # Get file attributes:                                                          #
    # Note: The files in the source directory are constantly being modified.        #
    #       Therefore, it is not necessary to determine which files need to be      #
    #       backed up.                                                              #
    #################################################################################

    fa = (walktree(settings['project']['dirpath'], getfileattrib))

    # Instantiates a Google storage client
    storage_client = storage.Client.from_service_account_json(settings['gcloud']['key'])

    # List Existing Buckets
    buckets = list(storage_client.list_buckets())
    logger.info('Buckets Pre-Backup:')
    logger.info(buckets)

    #####################################################################################
    # 1. Create a bucket in the project. A new bucket will be created for each backup.  #                            #
    # 2. The naming convention will be the Project ID + Date Time                       #
    #####################################################################################

    today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today = today.replace(':', '_')
    today = today.replace(" ", "-")
    bucket_name = settings['gcloud']['project_id'] + '-' + today
    bucket = storage_client.create_bucket(bucket_name)
    logger.info('[*] New Bucket Has Been Created: ' + bucket_name)

    # Upload files to the new bucket
    for x in fa:
        source_file_name = settings['project']['dirpath'] + x['filename']
        logger.info('[*] Uploading Source File: ' + source_file_name)
        destination_blob_name = x['filename']
        upload_blob(bucket_name, source_file_name, destination_blob_name)

    buckets = list(storage_client.list_buckets())
    logger.info(buckets)


