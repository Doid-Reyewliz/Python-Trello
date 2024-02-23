from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login

from atlassian import Jira
from pymongo import MongoClient


class Database:
    def __init__(self, db_user, db_pass):
        connection_string = f"mongodb+srv://{db_user}:{db_pass}@primecluster.6buri4v.mongodb.net/?retryWrites=true&w=majority"

        self.client = MongoClient(connection_string)
        self.db = self.client['Users']
        self.users_collection = self.db["Prime"]
        
    def ping(self):
        return self.client.admin.command('ping')

    def get_user(self, mail):
        return self.users_collection.find_one({"email": f'{mail}@p-s.kz'})

def login_view(request):
    if request.method == 'POST':        
        db_user = "alfanauashev"
        db_pass = '50SBW50gejk8Wn7F'
        
        usrn = request.POST.get('InputEmail')
        pswd = request.POST.get('InputPassword')
        
        
        db = Database(db_user, db_pass)
        user_data = db.get_user(usrn)
        
        if user_data['token'] is None:
            messages.error(request, 'Неверный логин или пароль')
            return render(request, 'login.html')
                
        jira = Jira(
            url='https://support.p-s.kz',
            username = usrn,
            token = user_data["token"]
        )
        
        check = jira.api_version        

        if user_data['password'] != pswd:
            messages.error(request, 'Неверный логин или пароль')
        elif check is None:
            messages.error(request, 'Неверный логин или пароль')
        else:
            request.session['username'] = usrn
            request.session['password'] = pswd
            
            return redirect('/board/')
    
    return render(request, 'login.html')