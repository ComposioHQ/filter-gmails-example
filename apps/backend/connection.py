from composio import Composio
from composio.types import auth_scheme

composio = Composio()

connection_request = composio.connected_accounts.initiate(
    user_id="sid",
    auth_config_id="ac_Z9G2e3_hPAil",
    config=auth_scheme.oauth2(options={"status": "INITIALIZING"}),
)
