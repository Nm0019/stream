# indicators/base_indicator.py

from abc import ABC, abstractmethod
import pandas as pd

class BaseIndicator(ABC):
    """
    کلاس پایه برای همه اندیکاتورهای تکنیکال. این کلاس ساختار پایه‌ای را برای
    محاسبه اندیکاتور، تولید سیگنال، امتیازدهی و توضیح فراهم می‌کند.
    """

    def __init__(self, symbol: str, timeframe: str, params: dict = None):
        """
        :param symbol: نماد معاملاتی (مثل BTCUSD)
        :param timeframe: تایم‌فریم (مثل M15)
        :param params: دیکشنری از پارامترهای قابل تنظیم اندیکاتور
        """
        self.symbol = symbol
        self.timeframe = timeframe
        self.params = params or {}

    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        محاسبه مقدار اندیکاتور و تحلیل آن.

        باید حداقل یک DataFrame بازگرداند شامل:
        - مقدار اندیکاتور در ستون value_<name>
        - سیگنال در ستون sig_<name>
        - امتیاز در ستون score_<name>
        - توضیح در ستون reason_<name>

        :param df: دیتافریم شامل OHLCV
        :return: pd.DataFrame شامل خروجی تحلیل اندیکاتور
        """
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__} symbol={self.symbol} tf={self.timeframe} params={self.params}>"
