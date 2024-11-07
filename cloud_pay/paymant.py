import asyncio
import logging
import pytz

import requests
from typing import Dict, List, Any
from config_data.config import Config, load_config
import datetime
from database.database import premium_setting

logger_pay = logging.getLogger(__name__)
handler_pay = logging.FileHandler(f"{__name__}.log")
formatter_pay = logging.Formatter("%(filename)s:%(lineno)d #%(levelname)-8s "
                                  "[%(asctime)s] - %(name)s - %(message)s")
handler_pay.setFormatter(formatter_pay)
logger_pay.addHandler(handler_pay)
logger_pay.info(f"Testing the custom logger for module {__name__}")

config: Config = load_config('.env')


class CryptoCloudSDK:
    def __init__(self, api_key=config.pay.api_key_cloud):
        """
        Initializing SDK for CryptoCloud.

        :param api_key: API key for authorizing requests.
        """
        self.api_key = api_key
        self.base_url = "https://api.cryptocloud.plus/v2/"

    def _send_request(self, endpoint: str, method: str = "POST", payload: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Sending a request to CryptoCloud API.

        :param endpoint: API endpoint.
        :param method: HTTP method.
        :param payload: Request data.
        :return: Response from server in JSON format.
        """
        headers = {"Authorization": f"Token {self.api_key}"}
        url = self.base_url + endpoint
        response = requests.request(method, url, headers=headers, json=payload)
        return response.json()

    def create_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creating an invoice.
        invoice_data =
        {
            "amount": float,\n
            "shop_id": str,\n
            "currency": str,\n
            "order_id": str,\n
            "add_fields":{
                "time_to_pay": {
                     "hours": int,\n
                     "minutes": int\n
                    },
                "email_to_send":str,
                "available_currencies":List[str], \n
                "period":str - month, week, day\n
                "cryptocurrency": str \n
                }
        }
        :param invoice_data: Data for creating an invoice.

        :return: Response from API about invoice creation.
        """
        return self._send_request("invoice/create", payload=invoice_data)

    def cancel_invoice(self, uuid: str) -> Dict[str, Any]:
        """
        Cancel invoice.

        :param uuid: Unique invoice identifier.
        :return: Response from API about invoice cancellation.
        """
        data = {"uuid": uuid}
        return self._send_request("invoice/merchant/canceled", payload=data)

    def list_invoices(self, start_date: str, end_date: str, offset: int = 0, limit: int = 10) -> Dict[str, Any]:
        """
        Getting a list of invoices.

        :param start_date: Period start date. dd.mm.yyyy
        :param end_date: Period end date. dd.mm.yyyy
        :param offset: Record list offset. 0
        :param limit: Number of entries in the list. 10
        :return: Response from API with list of invoices.
        """
        data = {"start": start_date, "end": end_date, "offset": offset, "limit": limit}
        return self._send_request("invoice/merchant/list", payload=data)

    def get_invoice_info(self, uuids: List[str]) -> Dict[str, Any]:
        """
        Obtaining information about invoices.

        :param uuids: List of unique invoice identifiers.
        :return: Response from the API with information about invoices.
        """
        data = {"uuids": uuids}
        return self._send_request("invoice/merchant/info", payload=data)

    def get_balance(self) -> Dict[str, Any]:
        """
        Obtaining information about your account balance.

        :return: Response from API with balance information.
        """
        return self._send_request("merchant/wallet/balance/all")

    def get_statistics(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Getting account statistics.

        :param start_date: Period start date.
        :param end_date: Period end date.
        :return: Response from API with account statistics.
        """
        data = {"start": start_date, "end": end_date}
        return self._send_request("invoice/merchant/statistics", payload=data)


crypto = CryptoCloudSDK()

dt_end = (datetime.datetime.now(datetime.timezone.utc)).strftime("%d.%m.%Y")


order_list_paid = []


async def list_order():
    order_list = []
    try:
        result = crypto.list_invoices(dt_end, dt_end, limit=100)
        if result:
            for i in result['result']:
                if i not in order_list and i not in order_list_paid:
                    order_list.append(i)
                if i['status'] == 'paid' and i not in order_list_paid:
                    await premium_setting(i['order_id'], 30)
                    order_list_paid.append(i)
                    datetime_obj = datetime.datetime.strptime(i['created'], '%Y-%m-%d %H:%M:%S.%f')
                    datetime_obj = pytz.utc.localize(datetime_obj)
                    datetime_now = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=2)
                    if datetime_obj < datetime_now:
                        order_list_paid.remove(i)
            else:
                pass
    except Exception as e:
        logger_pay.error(e)
    await asyncio.sleep(4)