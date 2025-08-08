# price_action/base.py

from abc import ABC, abstractmethod
import pandas as pd

class BasePriceAction(ABC):

    def __init__(self, symbol: str, timeframe: str, params: dict = None):
        self.symbol = symbol
        self.timeframe = timeframe
        self.params = params or {}

    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        باید در کلاس‌های فرزند پیاده‌سازی شود.
        خروجی: دیتافریم شامل ستون‌هایی که نتایج پرایس اکشن هستند.
        """
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__} symbol={self.symbol} tf={self.timeframe} params={self.params}>"
