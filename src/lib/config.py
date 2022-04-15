"""Module for managing the google credentials
"""
from typing import Union
import os
import pickle
from appdirs import user_config_dir
from google.oauth2.credentials import Credentials


def load_google_credentials() -> Union[Credentials, None]:
    """Attempt to load the Google credentials from a previously saved pickle
    file

    :return: The Google credentials object, or none if the pickle file
        doesn't exist
    """
    # Attempt to load the pickle file
    pickle_dir = user_config_dir('game_lookups', 'djnrrd')
    if not os.path.isdir(pickle_dir):
        # On Windows appdirs always have to be %appdir%//author//appname so
        # we have to create the author folder first
        if not os.path.isdir(os.path.join(user_config_dir(), 'djnrrd')):
            os.mkdir(os.path.join(user_config_dir(), 'djnrrd'))
        os.mkdir(pickle_dir)
    pickle_file = os.path.join(pickle_dir, 'google_account.pkl')
    if os.path.isfile(pickle_file):
        with open(pickle_file, 'rb') as f:
            credentials = pickle.load(f)
        return credentials
    return None


def save_google_credentials(credentials: Credentials) -> None:
    """Save the Google credentials object as a pickle file

    :param credentials: The Google credentials object
    """
    pickle_dir = user_config_dir('game_lookups', 'djnrrd')
    if not os.path.isdir(pickle_dir):
        # On Windows appdirs always have to be %appdir%//author//appname so
        # we have to create the author folder first
        if not os.path.isdir(os.path.join(user_config_dir(), 'djnrrd')):
            os.mkdir(os.path.join(user_config_dir(), 'djnrrd'))
        os.mkdir(pickle_dir)
    pickle_file = os.path.join(pickle_dir, 'google_account.pkl')
    with open(pickle_file, 'wb') as f:
        pickle.dump(credentials, f)


def delete_google_credentials() -> None:
    """Delete the saved pickle file from disc
    """
    # Attempt to load the pickle file
    pickle_dir = user_config_dir('game_lookups', 'djnrrd')
    pickle_file = os.path.join(pickle_dir, 'google_account.pkl')
    os.remove(pickle_file)