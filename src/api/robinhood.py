import os
from dotenv import load_dotenv
from src.api.trading_utils import error, debug
import robin_stocks.robinhood as r
from typing import Optional

load_dotenv()

async def login_to_robinhood(username: Optional[str] = None, password: Optional[str] = None,
                             mfa_code: Optional[str] = None, use_sms_challenge: bool = False) -> bool:
    """Authenticate with Robinhood API.
    
    Args:
        username: Robinhood username (optional, will use .env if None)
        password: Robinhood password (optional, will use .env if None)
        mfa_code: MFA code for 2FA (optional, will generate from MFA_SECRET if available)
        use_sms_challenge: Whether to use SMS challenge authentication instead of MFA
        
    Returns:
        bool: True if login successful, False otherwise
    """
    client = RobinhoodClient()
    if not username or not password:
        username = os.getenv('EMAIL')
        password = os.getenv('PASSWORD')
    
    # Handle MFA if needed
    if not mfa_code:
        mfa_secret = os.getenv('MFA_SECRET')
        if mfa_secret:
            try:
                import pyotp
                mfa_code = pyotp.TOTP(mfa_secret).now()
                debug(f"Generated MFA code from secret: {mfa_code}")
            except Exception as mfa_error:
                debug(f"Failed to generate MFA code: {str(mfa_error)}")
    
    try:
        if use_sms_challenge:
            debug("Using SMS challenge authentication")
            session = await client.login(
                username=username,
                password=password,
                mfa_code=None,
                by_sms=True
            )
        else:
            debug("Using MFA code authentication")
            session = await client.login(username, password, mfa_code)
        
        return session is not None
    except Exception as e:
        error(f"Robinhood login failed: {str(e)}")
        return False

async def get_account_info() -> dict:
    """Get account information from Robinhood
    
    Returns:
        dict: Account information including buying power, positions, etc.
    """
    client = RobinhoodClient()
    if not await client.authenticate():
        return {}
    return await client.get_account_info()

class RobinhoodClient:
    def __init__(self):
        self.email = os.getenv('EMAIL')
        self.password = os.getenv('PASSWORD')
        self.session = None
    
    async def login(self, username, password, mfa_code=None, by_sms=False):
        try:
            # Create a custom pickle name to avoid conflicts with other applications
            login_info = r.login(
                username=username,
                password=password,
                store_session=True,
                mfa_code=mfa_code,  # Pass MFA code if provided
                expiresIn=86400,  # 24 hour session
                pickle_name="_trading_bot",  # Custom pickle name to avoid conflicts
                by_sms=by_sms  # Whether to use SMS challenge
            )
            self.session = login_info
            debug(f"Login successful for username: {username}")
            debug(f"Session details: { {k:v for k,v in login_info.items() if k != 'token'} }")
            return self.session
        except Exception as e:
            error(f"Login failed: {str(e)}")
            # If login fails, try to delete the pickle file to force a fresh login next time
            try:
                home_dir = os.path.expanduser("~")
                pickle_path = os.path.join(home_dir, ".tokens", "robinhood_trading_bot.pickle")
                if os.path.exists(pickle_path):
                    os.remove(pickle_path)
                    debug("Removed corrupted pickle file for fresh login next time")
            except Exception as pickle_error:
                error(f"Failed to remove pickle file: {str(pickle_error)}")
            return None

    async def authenticate(self):
        try:
            # First try to use existing session if available
            if self.session:
                try:
                    # Test if the session is still valid
                    account_info = r.account.build_user_profile()
                    debug("Using existing authenticated session")
                    return True
                except Exception as session_error:
                    debug(f"Existing session invalid, re-authenticating: {str(session_error)}")
                    self.session = None
            
            # Create a new session
            self.session = await self.login(username=self.email, password=self.password)
            if not self.session:
                raise ValueError("Failed to create authenticated session")
            
            debug(f"Successfully authenticated with new session")
            return True
        except Exception as e:
            error(f"Failed to authenticate: {str(e)}")
            return False

    async def get_account_info(self) -> dict:
        """Get account information from Robinhood
        
        Returns:
            dict: Account information including buying power, positions, etc.
        """
        try:
            if not self.session:
                authenticated = await self.authenticate()
                if not authenticated:
                    error("Failed to authenticate before getting account info")
                    return {}
            
            try:
                # First try to get user profile
                account_info = r.account.build_user_profile()
                debug(f"Retrieved account profile successfully")
            except Exception as profile_error:
                # If that fails, try to re-authenticate and try again
                error(f"Error getting user profile: {str(profile_error)}")
                authenticated = await self.authenticate()
                if not authenticated:
                    return {}
                account_info = r.account.build_user_profile()
            
            # Enrich with additional account information
            try:
                account_details = r.account.load_account_profile()
                if account_details:
                    account_info['account_details'] = account_details
            except Exception as details_error:
                debug(f"Could not load additional account details: {str(details_error)}")
            
            debug(f"Account info retrieved successfully")
            return account_info
        except Exception as e:
            error(f"Failed to get account info: {str(e)}")
            return {}
