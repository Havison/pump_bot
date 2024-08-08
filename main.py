import os
from environs import Env

env = Env()
env.read_env()
bot_token = env('BOT_TOKEN')
api_key = env('API_KEY')
api_secret = env('API_SECRET')



