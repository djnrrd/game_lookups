"""A Module for stitching together the game lookups and google sheets in a
separate thread to the TK app
"""
from typing import Tuple, Dict, List
import platform
from threading import Thread
import asyncio
from logging import Logger
from google.oauth2.credentials import Credentials
from game_lookup_conf import twitch
from game_lookup.google import pre_flight, get_spreadsheet_range, update_sheet_range
from game_lookup.twitch import AsyncTwitchIDAPI
from game_lookup.igdb import IgdbAPI


async def get_twitch_oauth(logger: Logger) -> Tuple[str, str]:
    """Get the OAUTH token from Twitch

    :return: The Client ID and OAUTH Token
    """
    async with AsyncTwitchIDAPI(twitch.CLIENT_ID, twitch.CLIENT_SECRET,
                                logger) as twitch_id:
        oauth_token = await twitch_id.get_oauth_token()
    return twitch.CLIENT_ID, oauth_token


def match_game(name: str, games: Dict, logger: Logger) -> List[str]:
    """Try to match an exact game from the provided string to the potential
    multiple results from IGDB

    :param name: The game name from the original spreadsheet
    :param games: The results from IGDB
    :param logger: The custom logger object
    :return: the updated row for the Google Sheet
    """
    # Did we find anything?
    if len(games) == 0:
        logger.warning('No Matching Games found!')
        return ['NO MATCHING GAMES']
    if len(games) > 1:
        logger.info('Multiple matches found, looking for exact matches')
        filtered_games = [x for x in games
                          if x['name'].upper() == name.upper()]
        # If it's still multiple matches
        if len(filtered_games) > 1:
            logger.warning('Multiple exact matches found, update sheet '
                           'manually')
            return ['CHECK IGDB MANUALLY']
        if len(filtered_games) == 0:
            logger.warning('No exact matches found, Update Column A with '
                           'correct title')
            return ['NO EXACT MATCHES'] + [','.join([x['name'] for x in games])]
        # We should only have one game left
        game = filtered_games.pop()
    else:
        # We only had one game to start with
        game = games.pop()
    logger.info(f"Adding game {game['name']} to sheet")
    genres = ','.join(game['genres']) if game['genres'] is not None else ''
    keywords = ','.join(game['keywords']) \
        if game['keywords'] is not None else ''
    steampage = ','.join(game['steampage']) if game['steampage'] is not None \
        else ''
    return [game.get('summary'), genres, keywords, str(game.get('rating')),
            steampage]


async def loop_sheet(sheet: Dict, logger: Logger) -> Dict:
    """Loop through the rows of the Google sheet and lookup the games on IGDB

    :param sheet: The Google Sheet
    :param logger: The custom logger object
    :return: The updated Google Sheet
    """
    client_id, oauth_token = await get_twitch_oauth(logger)
    async with IgdbAPI(client_id, oauth_token, logger) as igdb:
        for row in sheet['values']:
            # Fill in gaps if needed
            while len(row) < 3:
                logger.debug('Beefing out entry to 3 columns')
                row.append('')
            # Lookup anything not looked up
            if len(row) == 3:
                logger.info(f"Looking up game {row[0]}")
                games = await igdb.search_game(row[0])
                row += match_game(row[0], games, logger)
    return sheet


def do_game_sheet(doc_id: str, credentials: Credentials, logger: Logger) \
        -> None:
    """Load the Google sheet and start the Asyncio loop to lookup the values
    in IGDB

    :param doc_id: The Google Drive ID
    :param credentials: The Google credentials object
    :param logger: The custom logger
    """
    if not pre_flight(doc_id, credentials, logger):
        return
    logger.info('Getting spreadsheet from Google')
    sheet = get_spreadsheet_range(doc_id, credentials, logger)
    if sheet is not None:
        logger.debug('Starting async loop for lookups')
        if platform.system() == 'Windows':
            asyncio.set_event_loop_policy(
                asyncio.WindowsSelectorEventLoopPolicy())
        loop = asyncio.new_event_loop()
        sheet = loop.run_until_complete(
            loop_sheet(sheet, logger)
        )
        logger.debug('Lookups complete, updating sheet on Google API')
        sheet = update_sheet_range(sheet, doc_id, credentials, logger)
    if sheet is None:
        logger.warning('Something went wrong with the sheet')
    else:
        logger.info('Sheet updated. All done.')


def start_lookup_thread(doc_id: str, credentials: Credentials, logger: Logger) \
        -> None:
    """Start a new thread to lookup the games from the Google Sheet

    :param doc_id: The Google Drive ID
    :param credentials: The Google credentials object
    :param logger: The custom logger
    """
    logger.debug('Starting new Thread')
    lookup = Thread(target=do_game_sheet, args=(doc_id, credentials, logger))
    lookup.start()
