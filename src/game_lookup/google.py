"""A module for dealing with the Google Drive and Sheets APIs
"""
from typing import List, Union, Dict
from logging import Logger
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from game_lookup.config import save_google_credentials


class GoogleSheet:
    """Basic class to store the ID and title of a Google Document
    :param doc_id: The Google API ID for the document
    :param name: The name of the document
    """

    def __init__(self, doc_id: str, name: str) -> None:
        self.id = doc_id
        self.name = name

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name


def get_credentials(logger: Logger) -> Union[Credentials, None]:
    """Launch the user's web browser to get the OAUTH2 login credentials

    :return: Credentials object
    """
    client_secret = os.path.join(os.path.dirname(__file__), '..', 'game_lookup_conf',
                                 'google_client_secret.json')
    scopes = ['https://www.googleapis.com/auth/drive',
              'https://www.googleapis.com/auth/drive.file',
              'https://www.googleapis.com/auth/spreadsheets']
    flow = InstalledAppFlow.from_client_secrets_file(client_secret,
                                                     scopes=scopes)
    try:
        credentials = flow.run_local_server()
    except HttpError as err:
        logger.warning(err)
        return None
    save_google_credentials(credentials)
    return credentials


def get_documents(credentials: Credentials, logger: Logger) \
        -> Union[List[GoogleSheet], None]:
    """Get a list of spreadsheets in the user's Google drive

    :param credentials: Google credentials object
    :param logger: A logger object
    :return: The list of spreadsheets
    """
    with build('drive', 'v3', credentials=credentials) as service:
        q_filter = "mimeType='application/vnd.google-apps.spreadsheet'"
        ret_files = []
        request = service.files().list(corpora='user', q=q_filter)
        while request is not None:
            try:
                response = request.execute()
            except HttpError as err:
                logger.warning(err)
                return None
            ret_files += response['files']
            logger.debug(f"{len(response['files'])} files found")
            request = service.files().list_next(request, response)
    logger.info(f"Found {len(ret_files)} spreadsheets")
    ret_files = [GoogleSheet(x['id'], x['name']) for x in ret_files]
    return ret_files


def get_spreadsheet_range(doc_id: str, credentials: Credentials,
                          logger: Logger) -> Union[Dict, None]:
    """Get the expected range of game fields in the expected document

    :param doc_id: The Google drive document ID
    :param credentials: Google credentials object
    :param logger: A logger object
    :return: Google spreadsheet object with the selected range
    """
    with build('sheets', 'v4', credentials=credentials) as service:
        request = service.spreadsheets().values().get(spreadsheetId=doc_id,
                                                      range='A:H')
        try:
            response = request.execute()
        except HttpError as err:
            logger.warning(err)
            return None
    return response


def get_permissions(doc_id, credentials: Credentials, logger: Logger) \
        -> Union[Dict, None]:
    """Get permissions for a Google Document

    :param doc_id: The Google drive document ID
    :param credentials: Google credentials object
    :param logger: A logger object
    :return: the list of permissions
    """
    with build('drive', 'v3', credentials=credentials) as service:
        request = service.permissions().list(fileId=doc_id)
        try:
            response = request.execute()
        except HttpError as err:
            logger.warning(err)
            return None
    return response


def pre_flight(doc_id: str, credentials: Credentials, logger: Logger) \
        -> Union[bool, None]:
    """check file permissions to make sure we can edit the document

    :param doc_id: The Google drive document ID
    :param credentials: Google credentials object
    :param logger: A logger object
    :return: True if permissions were fine
    """
    permissions = get_permissions(doc_id, credentials, logger)
    if not permissions:
        logger.warning('Pre flight checks failed, could not get permissions '
                       'for file')
        return None
    permissions = [x for x in permissions['permissions']
                   if x['role'] in ('owner', 'writer')]
    if not permissions:
        logger.warning('Pre flight checks failed, user is not an owner or '
                       'writer of the file')
        return None
    return True


def update_sheet_range(sheet: [Dict], doc_id: str,
                       credentials: Credentials, logger: Logger) \
        -> Union[Dict, None]:
    """Update the Spreadsheet range on the Google Doc

    :param sheet: Google spreadsheet object with the selected range
    :param doc_id: The Google drive document ID
    :param credentials: Google credentials object
    :param logger: A logger object
    :return: The updated Sheet
    """
    sheet_range = sheet['range']
    with build('sheets', 'v4', credentials=credentials) as service:
        request = service.spreadsheets().values().update(spreadsheetId=doc_id,
                                                         range=sheet_range,
                                                         body=sheet,
                                                         valueInputOption='RAW')
        try:
            response = request.execute()
        except HttpError as err:
            logger.warning(err)
            return None
    return response
