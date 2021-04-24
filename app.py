import quart.flask_patch
from quart import Quart, render_template, request, session, redirect, url_for, flash
from quart_discord import DiscordOAuth2Session, Unauthorized
from quart_discord.utils import requires_authorization as req_auth
from modules import *
from dotenv import load_dotenv
from os import getenv
load_dotenv()

app = Quart(__name__)
app.config["SECRET_KEY"] = getenv('SECRET_KEY')
app.config["DISCORD_CLIENT_ID"] = getenv('CLIENT_ID')
app.config["DISCORD_CLIENT_SECRET"] = getenv('CLIENT_SECRET')
app.config["DISCORD_REDIRECT_URI"] = getenv('REDIRECT_URI')

ipc_client= None
discord = DiscordOAuth2Session(app)

@app.route("/")
async def home():
    try:
        user= await discord.fetch_user()
    except Unauthorized:
        user = None
    return await render_template("index.html", user=user)

@app.route("/login")
async def login():
	return await discord.create_session(prompt=None)

@app.route("/logout")
async def logout():
    discord.revoke()
    return redirect(url_for("home"))

@app.route("/callback")
async def callback():
    await discord.callback()
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
@req_auth
async def dashboard():
    global ipc_client
    user= await discord.fetch_user()
    user_guilds= await discord.fetch_guilds()
    
    ipc_client = await create_client(ipc_client)
    if ipc_client is None:
        guild_ids = []
        await flash('Unable to load client', 'danger')
    else:
        guild_ids = await get_guilds(discord, ipc_client)
    guilds = [guild for guild in user_guilds if guild.id in guild_ids]
    
    guilds_row_col = []
    temp_guilds = []
    for count, guild in enumerate(guilds):
        temp_guilds.append(guild)
        if (count+1)%3 == 0:
            guilds_row_col.append(temp_guilds)
            temp_guilds=[]
    else:
        guilds_row_col.append(temp_guilds)
    return await render_template("dashboard.html", user=user, guilds=guilds, guilds_row_col=guilds_row_col)

@app.route('/server/<int:server_id>', methods=('GET','POST'))
@req_auth
async def server(server_id):
    global ipc_client
    user= await discord.fetch_user()
    user_guilds= await discord.fetch_guilds()
    ipc_client= await create_client(ipc_client)
    guild_ids= await get_guilds(discord, ipc_client)
    if server_id not in guild_ids:
        return "Error (301)"
    if request.method=="GET":
        guild = [guild for guild in user_guilds if guild.id==server_id][0]
        categories = await ipc_client.request("get_channels", guild_id=server_id)
        return await render_template('server.html', user=user, guild=guild, categories=categories, server_id=server_id)
    if request.method=="POST":
        form = await request.form
        response = await ipc_client.request('send_message', guild_id=int(server_id), channel_id=int(form['channel']), message={"content":form['message']})
        print(response)
        return redirect(url_for('server', server_id=server_id))
    
@app.errorhandler(Unauthorized)
async def handle_unauthorized(e):
    await flash('Error occured when logging in. Try again!', 'danger')
    return redirect(url_for('home'))


if __name__ == "__main__":
	app.run(host=getenv('HOST'), port=getenv('PORT'), debug=True)