from asgiref.sync import sync_to_async
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.core.cache import cache

from atlassian import Jira, utils
from tornado import gen, ioloop
from pymongo import MongoClient


import logging
logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_user, db_pass):
        connection_string = f"mongodb+srv://{db_user}:{db_pass}@primecluster.6buri4v.mongodb.net/?retryWrites=true&w=majority"

        self.client = MongoClient(connection_string)
        self.db = self.client['Users']
        self.users_collection = self.db["Prime"]
    
    @gen.coroutine
    def ping(self):
        return self.client.admin.command('ping')

    @gen.coroutine
    def get_user(self, mail):
        return self.users_collection.find_one({"email": f'{mail}@p-s.kz'})

async def login_view(request):
    try:
        if request.method == 'POST':        
            db_user = "alfanauashev"
            db_pass = '50SBW50gejk8Wn7F'
            
            usrn = request.POST.get('InputEmail')
            pswd = request.POST.get('InputPassword')
            
            db = Database(db_user, db_pass)
            user_data = await db.get_user(usrn)
                        
            if user_data['token'] is None:
                messages.error(request, 'Неверный логин или пароль')
                return await render(request, 'login.html')
            
            try:
                f = open(f"board/data/{usrn[2:]}_cookie.txt", "x")
            except:
                pass
                                
            jira = Jira(
                url='https://support.p-s.kz',
                username = usrn,
                token = user_data["token"]
            )
            
            check = jira.api_version        

            if user_data['password'] != pswd or check is None:
                messages.error(request, 'Неверный логин или пароль')
            else:
                await sync_to_async(request.session.__setitem__)('username', usrn)
                await sync_to_async(request.session.__setitem__)('token', user_data["token"])
                await sync_to_async(cache.clear)()
                
                return redirect('/board/')
        
        return render(request, 'login.html')
    except Exception as e:
        logger.exception("Error in login: %s", e)