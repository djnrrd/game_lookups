"""A module for looking up games on IGDB
"""
import asyncio
from typing import List, Dict
import logging
from basewebapi.asyncbasewebapi import AsyncBaseWebAPI


class IgdbAPI(AsyncBaseWebAPI):
    """Basic API to connect to IGDB

    :param client_id: Twitch Client ID
    :param oauth_token: OAUTH token from Twitch
    :param logger: A logging object
    """

    def __init__(self, client_id: str, oauth_token: str,
                 logger: logging.Logger = None) -> None:
        super().__init__('api.igdb.com', '', '', secure=True)
        self.headers['Client-ID'] = client_id
        self.headers['Authorization'] = f"Bearer {oauth_token}"
        self.headers['Accept'] = 'application/json'
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger()
            self.logger.setLevel(logging.DEBUG)
        self.genres: Dict[int, str] = {}
        self.keywords: Dict[int, str] = {}

    async def search_game(self, game: str) -> List[Dict]:
        """Search for a game on IGDB

        :param game: The name of the Game to search for
        :return: The list of matching games
        """
        self.logger.info(f"Searching for {game}")
        path = '/v4/games'
        body = f"search \"{game}\";\n" \
               f"fields name,summary,genres,keywords,rating;"
        results = await self._transaction('post', path, data=body)
        self.logger.debug(f"IGDB returned {results}")
        self.logger.info(f"Found {len(results)} results")
        for result in results:
            result['genres'] = await self.get_genres(result.get('genres'))
            result['keywords'] = await self.get_keywords(result.get('keywords'))
            await asyncio.sleep(0.33)
            result['steampage'] = await self.get_steam_page(result['id'])
        return results

    async def get_genres(self, genre_ids: List[int]) -> List[str]:
        """Get the genres for the list of genre IDs provided, caching entries
        from IGDB

        :param genre_ids: The list of IDs
        :return: A list of genre names
        """
        lookup_ids = []
        ret_list = []
        if genre_ids is not None:
            # Try the local cache first
            for genre_id in genre_ids:
                genre_name = self.genres.get(genre_id)
                if genre_name:
                    self.logger.debug(f"Found {genre_name} for {genre_id} in "
                                      f"genre cache")
                    ret_list.append(genre_name)
                else:
                    self.logger.debug(f"Did not find {genre_id} in genre cache")
                    lookup_ids.append(genre_id)
            # If nothing was in the cache
            if lookup_ids:
                self.logger.info(f"Looking up genre IDs {lookup_ids} after "
                                 f"sleep")
                await asyncio.sleep(0.33)
                lookups = await self._get_genres(lookup_ids)
                self.genres.update(lookups)
                return await self.get_genres(genre_ids)
            return ret_list
        self.logger.debug('No Genre IDs for game')
        return None

    async def _get_genres(self, genre_ids: List[int]) -> Dict[int, str]:
        """Get the genres from IGDB

        :param genre_ids: a list of the genre IDs
        :return: a dictionary of id to genre name
        """
        genre_ids = [str(x) for x in genre_ids]
        path = '/v4/genres'
        body = f"where id = ({','.join(genre_ids)});\n" \
               f"fields name;"
        results = await self._transaction('post', path, data=body)
        self.logger.debug(f"Received {results} from IGDB for genres")
        results = {x['id']: x['name'] for x in results}
        return results

    async def get_keywords(self, keyword_ids: List[int]) -> List[str]:
        """Get the keywords for the list of keyword IDs provided, caching
        entries from IGDB

        :param keyword_ids: The list of IDs
        :return: A list of keywords
        """
        lookup_ids = []
        ret_list = []
        if keyword_ids is not None:
            # Try the local cache first
            for keyword_id in keyword_ids:
                keyword = self.keywords.get(keyword_id)
                if keyword:
                    self.logger.debug(f"Found {keyword} for {keyword_id} in "
                                      f"genre cache")
                    ret_list.append(keyword)
                else:
                    self.logger.debug(f"Did not find {keyword_id} in keyword "
                                      f"cache")
                    lookup_ids.append(keyword_id)
            # If nothing was in the cache
            if lookup_ids:
                self.logger.info(f"Looking up keyword IDs {lookup_ids} after "
                                 f"sleep")
                await asyncio.sleep(0.33)
                lookups = await self._get_keywords(lookup_ids)
                self.keywords.update(lookups)
                return await self.get_keywords(keyword_ids)
            return ret_list
        self.logger.debug('No Keyword IDs for game')
        return None

    async def _get_keywords(self, keyword_ids: List[int]) -> Dict[int, str]:
        """Get the keywords from IGDB

        :param keyword_ids: a list of the keyword IDs
        :return: a dictionary of id to keyword
        """
        keyword_ids = [str(x) for x in keyword_ids]
        path = '/v4/keywords'
        body = f"where id = ({','.join(keyword_ids)});\n" \
               f"fields name;"
        results = await self._transaction('post', path, data=body)
        self.logger.debug(f"Received {results} from IGDB for keywords")
        results = {x['id']: x['name'] for x in results}
        return results

    async def get_steam_page(self, game_id: int) -> List[str]:
        """Get the Steam page from IGDB

        :param game_id: The ID of the game
        :return: The URL to the steam page
        """
        self.logger.info(f"Looking up Steam page for game ID {game_id}")
        path = '/v4/websites'
        body = f"where game = {game_id} & category = 13;\n" \
               f"fields url;"
        results = await self._transaction('post', path, data=body)
        self.logger.debug(f"Received {results} from IGDB for Steam webpage")
        results = [x['url'] for x in results]
        return results
