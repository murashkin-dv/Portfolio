from typing import Any

import requests
from loguru import logger

from config_data.config import RAPID_API_HOST, RAPID_API_KEY


@logger.catch
def api_request(method_endswith: str,
                params: dict,
                method_type: str
                ) -> Any:
    """
    This function makes requests to API

    :param method_endswith: API url finish, it depends on the GET method
    :param params: optional parameters as API requires
    :param method_type: GET or POST
    :return: a function based on methods GET or POST
    """

    url = f"https://motorcycles-by-api-ninjas.p.rapidapi.com{method_endswith}"

    if method_type == 'GET':
        return get_request(url, params, complete_result=[])


@logger.catch
def get_request(url: str, params: dict, complete_result: list) -> Any:
    """
    Function gets data from a server based on API parameters

    :param url: str
    :param params: dict
    :param complete_result: list
    :return: json object
    """

    response = requests.get(
            url=url,
            headers={"X-RapidAPI-Key": RAPID_API_KEY,
                     "X-RapidAPI-Host": RAPID_API_HOST},
            params=params,
            timeout=15)

    if response.status_code == requests.codes.ok:
        current_result = response.json()
        complete_result += current_result
        if len(current_result) == 30:
            #  '30' is a limit for result with offset = 0 by API server
            params['offset'] += 30
            return get_request(url, params, complete_result)
        else:
            return complete_result
    else:
        logger.debug('Server Error')
        return
