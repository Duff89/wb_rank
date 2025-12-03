import json
import requests

from loguru import logger

from get_token import get_token

HEADERS = {
    'accept': '*/*',
    'accept-language': 'ru-RU,ru;q=0.9',
    'priority': 'u=1, i',
    'referer': 'https://www.wildberries.ru/catalog/0/search.aspx?search=%D0%BD%D0%BE%D0%B2%D0%BE%D0%B3%D0%BE%D0%B4%D0%BD%D0%B8%D0%B5%20%D1%83%D0%BA%D1%80%D0%B0%D1%88%D0%B5%D0%BD%D0%B8%D1%8F',
    'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
    'x-spa-version': '13.15.1',
    'x-userid': '0',
}

TOKEN = '1.1000.a133f093f65642dcbdb2fb6cf90f3d6e.MHwxNzguMTIwLjUwLjU2fE1vemlsbGEvNS4wIChXaW5kb3dzIE5UIDEwLjA7IFdpbjY0OyB4NjQpIEFwcGxlV2ViS2l0LzUzNy4zNiAoS0hUTUwsIGxpa2UgR2Vja28pIENocm9tZS8xNDIuMC4wLjAgU2FmYXJpLzUzNy4zNnwxNzY1ODA0NTE2fHJldXNhYmxlfDJ8ZXlKb1lYTm9Jam9pSW4wPXwwfDN8MTc2NTE5OTcxNnwx.MEUCIQD5Pb2WV/wl+r3tnAkNiHGAop6AW0SwvZTox2V9R9bFgwIgVjfnUenxL4gv+XhW1ruSQjhWXE+XYEb6+3osp/Kial8='


class WbRank:
    SEARCH_URL = "https://www.wildberries.ru/__internal/u-search/exactmatch/sng/common/v18/search"

    DEFAULT_PARAMS = {
        "ab_testing": ["false", "false"],
        "appType": "1",
        "curr": "rub",
        "dest": "-3626404",
        "hide_dtype": "11",
        "inheritFilters": "false",
        "lang": "ru",
        "page": "1",
        "resultset": "catalog",
        "sort": "popular",
        "spp": "30",
        "suppressSpellcheck": "false",
        "query": "джинсы женские",
    }


    def __init__(self, goods: list):
        self.goods = goods
        self.token = TOKEN

    def _update_token(self):
        logger.info("Обновляем токен")
        self.token = get_token()
        logger.info("Обновили токен")

    def get_fetch(self, query: str, retries: int = 2):
        params = self.DEFAULT_PARAMS.copy()
        params["query"] = query

        for attempt in range(1, retries + 2):
            logger.info(f"Попытка {attempt}")
            response = requests.get(
                self.SEARCH_URL,
                params=params,
                cookies={"x_wbaas_token": self.token},
                headers=HEADERS
            )
            if response.status_code == 498:
                logger.warning("498 code")
                self._update_token()
                continue
            if response.status_code != 200:
                logger.warning(response.status_code)
                return None

            try:
                return response.json()
            except Exception:
                logger.exception("Json error")
                return None

        logger.warning("Все попытки неуспешны")
        return None

    def get_rank_position(self, data: json, sku: str | int) -> int | None:
        products = data.get("products")
        if not products:
            logger.warning("Нет products в json")
            return None

        try:
            sku = int(sku)
        except ValueError:
            return None

        for index, product in enumerate(products, start=1):
            if product.get("id") == sku:
                return index
        return None


    def parse_rank(self) -> list:
        results = []

        for good in self.goods:
            sku = good.get("sku")
            query = good.get("query")

            if not sku or not query:
                logger.warning("Нет артикула или запроса")
                continue

            data = self.get_fetch(query=query)
            if not data:
                results.append(
                    {"sku": sku, "query": query, "rank": None}
                )
                continue

            results.append(
                {"sku": sku, "query": query, "rank": self.get_rank_position(data=data, sku=sku)}
            )
        return results



if __name__ == "__main__":
    input_list = [
        {"sku": "401385455", "query": "джинсы женские"},
        {"sku": "499047922", "query": "джинсы женские"},
        {"sku": "311720382", "query": "джинсы женские"},
        {"sku": "500901385", "query": "новогодний декор"},
        {"sku": "185459879", "query": "новогодний декор"},
        {"sku": "113178770", "query": "новогодний декор"},
    ]

    results = WbRank(goods=input_list).parse_rank()
    logger.success(results)
