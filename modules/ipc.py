__all__ = (
    "create_client",
    "get_guilds"
)

from os import getenv
from discord.ext import ipc
from aiohttp.client_exceptions import ClientConnectorError

async def create_client(ipc_client=None):
    if ipc_client is None:
        ipc_client = ipc.Client(host=getenv('IPC_HOST'), port=getenv('IPC_PORT'), secret_key=getenv('IPC_PASSWORD'))
        try: await ipc_client.request("get_guild_count")
        except ClientConnectorError: ipc_client = None
        except ConnectionResetError: 
            ipc_client = ipc.Client(host=getenv('IPC_HOST'), port=getenv('IPC_PORT'), secret_key=getenv('IPC_PASSWORD'))
    return ipc_client

async def get_guilds(discord, ipc_client):
    user= await discord.fetch_user()
    guilds= await discord.fetch_guilds()
    guild_ids= [guild.id for guild in guilds]
    return (await ipc_client.request('get_mutual_guilds_with_admin', user_id=user.id, guild_ids=guild_ids))