#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""back up files and directories to google drive"""
__author__ = 'yusuf b'

MAX_BACKUP_FILES = 3
BACKUP_FILE_PREFIX = "vs_backup_"
AUTH_FILE_TO_CREATE = "auth"
PATHS_TO_BACKUP = [
    'xx'
]

import sys, os, zipfile, time, tempfile

try:
    from pydrive.auth import GoogleAuth
    from pydrive.drive import GoogleDrive
except ImportError:
    sys.stderr.write("install PyDrive module first!\n")
    sys.exit(1)


def zipdir(path, ziph):
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))


if __name__ == '__main__':

    if sys.version_info >= (3, 0):
        sys.stderr.write("this script requires python 2.x\n")
        sys.exit(1)

    upload_file_name = "%s%s.zip" % (BACKUP_FILE_PREFIX, time.strftime("%Y-%m-%d-%H-%M-%S"))
    zip_file_name = "%s/%s" % (tempfile.gettempdir(), upload_file_name)
    zipf = zipfile.ZipFile(zip_file_name, 'a', zipfile.ZIP_DEFLATED)

    toZip = 0
    for path in PATHS_TO_BACKUP:
        if os.path.isdir(path):
            zipdir(path, zipf)
            toZip += 1
        elif os.path.isfile(path):
            zipf.write(path)
            toZip += 1
        else:
            sys.stdout.write("no file with name: %s\n" % path)

    zipf.close()

    print "%d file/directory zipped into %s" % (toZip, zip_file_name)

    gauth = GoogleAuth()

    gauth.LoadCredentialsFile(AUTH_FILE_TO_CREATE)
    if gauth.credentials is None:
        gauth.CommandLineAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()
    gauth.SaveCredentialsFile(AUTH_FILE_TO_CREATE)

    drive = GoogleDrive(gauth)

    uploaded_file = drive.CreateFile({'title': upload_file_name})
    uploaded_file.SetContentFile(zip_file_name)
    uploaded_file.Upload()
    print("file uploaded. title: %s, id: %s" % (uploaded_file['title'], uploaded_file['id']))

    os.remove(zip_file_name)

    backed_up_file_list = drive.ListFile(
        {'q': "'root' in parents and trashed=false and title contains '%s'" % BACKUP_FILE_PREFIX,
         'maxResults': "1000", 'orderBy': "title asc"}).GetList()

    file_ids_to_remove = []
    for backed_up_file in backed_up_file_list:
        file_ids_to_remove.append({'id': backed_up_file['id'], 'title': backed_up_file['title']})

    if len(file_ids_to_remove) > MAX_BACKUP_FILES:
        numberOfFilesToRemove = len(file_ids_to_remove) - MAX_BACKUP_FILES
        removedCount = 0
        for file_to_remove in file_ids_to_remove:
            if removedCount < numberOfFilesToRemove and file_to_remove['title'].startswith(BACKUP_FILE_PREFIX):
                gauth.service.files().delete(fileId=file_to_remove['id']).execute()
                removedCount += 1

        if removedCount > 0:
            print "%d file(s) deleted from google drive" % removedCount