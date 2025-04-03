import os
from dotenv import load_dotenv
from src.api.trading_utils import error, debug
import robin_stocks.robinhood as r

load_dotenv()

class RobinhoodClient:
    def __init__(self):
        self.email = os.getenv('EMAIL')
        self.password = os.getenv('PASSWORD')
        self.session = None
    
    async def login(self, username, password):
        try:
            login_info = r.login(username=username, password=password, store_session=True)
            self.session = login_info
            debug(f"Login successful with username: {username}, password: {password}")
            debug(f"Login_info: {login_info}")
            return self.session
        except Exception as e:
            error(f"Login failed: {str(e)}")
            return None

    async def authenticate(self):
        try:
            self.session = await self.login(username=self.email, password=self.password)
            if not self.session:
                raise ValueError("Failed to create authenticated session")
            
            debug(f"Authenticated session: {self.session}")
            return True
        except Exception as e:
            error(f"Failed to authenticate: {str(e)}")
            return False
