from django.shortcuts import render
from django.http import JsonResponse
from django.template.loader import render_to_string

from atlassian import Jira
from pymongo import MongoClient

import requests
from PIL import Image
import io

from django.views.decorators.cache import cache_page

class Database:
    def __init__(self, db_user, db_pass):
        connection_string = f"mongodb+srv://{db_user}:{db_pass}@primecluster.6buri4v.mongodb.net/?retryWrites=true&w=majority"

        self.client = MongoClient(connection_string)
        self.db = self.client['Users']
        self.users_collection = self.db["Prime"]

    def get_user(self, mail):
        return self.users_collection.find_one({"email": f'{mail}@p-s.kz'})

def save_avatar(binary_data, filename=r"board\static\images\profile_picture.png"):
    image = Image.open(io.BytesIO(binary_data))
    image.save(filename)
    
    return filename

def jira_view(request):
    db_user = "alfanauashev"
    db_pass = '50SBW50gejk8Wn7F'
    
    usrn = request.session.get('username')
    pswd = request.session.get('password')
    
    db = Database(db_user, db_pass)
    user_data = db.get_user(usrn)
    
    fullname = None
    avatar = None
    list_of_clients = []
    get_client = '0'
    
    dict_issue = {
        'Ошибка': ['https://support.p-s.kz/secure/viewavatar?size=xsmall&avatarId=10303&avatarType=issuetype', '#ff5630', '#fff']
    }
    
    if user_data['token'] is None:
        return render(request, 'jira.html', {'data': 'error'})
        
    jira = Jira(
        url="https://support.p-s.kz", 
        username = usrn,
        token = user_data['token']
    )
    
    tasks = {
        'ОЧЕРЕДЬ': [{}, 0],
        '3 ЛИНИЯ': [{}, 0], 
        'НА УТОЧНЕНИИ': [{}, 0], 
        "ТЕСТИРОВАНИЕ": [{}, 0], 
        "КЛИЕНТ - ТЕСТИРОВАНИЕ": [{}, 0],
        "ЗАКРЫТЫЕ": [{}, 0]
    }
    
    clients = [  
        "Евразийский Банк",
        "Jusan Bank",
        "ForteBank",
        "КЗИ",
        "Brillink Fintech Limited",
        "Сбербанк",
        "Банк ЦентрКредит",
        "Народный Банк",
        "RBK",
        "Банк Хоум Кредит",
        "Халык Банк Кыргызстан",
        "ВТБ",
        "Заман",
        "Банк Китая",
        "Казпочта (AML)",
        "ЦЕНТРАЛЬНЫЙ ДЕПОЗИТАРИЙ ЦЕННЫХ БУМАГ",
        "Ситибанк",
        "Al Hilal",
        "Altyn Bank",
        "Halyk Finance",
        "Антифрод",
        "Halyk Global Markets"
    ]

    dict_clients = {
        "Евразийский Банк":                         ["Eurasian Bank", "#e774bb", "#713659", "SETTINGS-96"],
        "Jusan Bank":                               ["Jusan", "#fea362", "#813c0c", "SETTINGS-109"],
        "ForteBank":                                ["Forte Bank", "#ae4787", "#fff", "SETTINGS-90"],
        "КЗИ":                                      ["KZI", "#c9372c", "#fff", "SETTINGS-224"],
        "Brillink Fintech Limited":                 ["BFL", "#6cc3e0", "#164555", "SETTINGS-200"],
        "Сбербанк":                                 ["Sber bank", "#1f845a", "#fff", "SETTINGS-95"],
        "Банк ЦентрКредит":                         ["BCC", "#f5cd47", "#533f04", "SETTINGS-91"],
        "Народный Банк":                            ["Halyk Bank", "#1f845a", "#fff", "SETTINGS-100"],
        "RBK":                                      ["RBK", "#53dbdc", "#164555", "SETTINGS-89"],
        "Банк Хоум Кредит" :                        ["Home Credit Bank", "#c9372c", "#fff", "SETTINGS-93"],
        "Халык Банк Кыргызстан":                    ["HBK", "#1f845a", "#fff", "SETTINGS-198"],
        "ВТБ":                                      ["VTB", "#0c66e4", "#fff", "SETTINGS-94"],
        "Заман":                                    ["Zaman", "#227d9b", "#f4f7f9", "SETTINGS-97"],
        "Банк Китая":                               ["Bank of China", "#f5cd47", "#533f04", "SETTINGS-92"],
        "Казпочта (AML)":                           ["Kazpost", "#0c66e4", "#fff", "SETTINGS-99"],
        "ЦЕНТРАЛЬНЫЙ ДЕПОЗИТАРИЙ ЦЕННЫХ БУМАГ" :    ["ЦД", "#0c66e4", "#fff", "SETTINGS-284"],
        "Ситибанк":                                 ["City", "#0c66e4", "#fff", "SETTINGS-101"],
        "Al Hilal":                                 ["Al Hilal", "#fea362", "#7d3909", "SETTINGS-98"],
        "Altyn Bank":                               ["Altyn", "#f5cd47", "#533f04", "SETTINGS-88"],
        "Halyk Finance":                            ["Halyk Finance", "#1f845a", "#fff", "SETTINGS-229"],
        "Антифрод":                                 ["Антифрод", "#0c66e4", "#fff", "SETTINGS-227"],
        "Halyk Global Markets":                     ["HGM", "#4bce97", "#21674b", "SETTINGS-222"]
    }
    
    if (request.method == 'POST' or request.method == 'GET'):
        get_client = request.GET.get('client', None)
                
        if get_client is not None and get_client != '0':
            is_associated = False
            for key, item in dict_clients.items():
                if get_client == item[0]:
                    get_client = item[3]
                    is_associated = True
                    break
                
            if is_associated:
                opened_str = f"project = SUP_AML AND status in ('На уточнении', '3 линия', Тестирование, Очередь, 'Клиент - тестирование') AND resolution = Unresolved AND Разработчики = {usrn} AND cf[10609] = {get_client} ORDER BY created DESC"
                closed_str = f"project = SUP_AML AND status in (Решен, Отозван, Закрыт, Done) AND resolved >= startOfMonth() AND Разработчики = {usrn} AND cf[10609] = {get_client} ORDER BY created DESC"
            else:
                opened_str = f"project = SUP_AML AND status in ('На уточнении', '3 линия', Тестирование, Очередь, 'Клиент - тестирование') AND resolution = Unresolved AND Разработчики = {usrn} ORDER BY created DESC"
                closed_str = f"project = SUP_AML AND status in (Решен, Отозван, Закрыт, Done) AND resolved >= startOfMonth() AND Разработчики = {usrn} ORDER BY created DESC"

        else:
            opened_str = f"project = SUP_AML AND status in ('На уточнении', '3 линия', Тестирование, Очередь, 'Клиент - тестирование') AND resolution = Unresolved AND Разработчики = {usrn} ORDER BY created DESC"
            closed_str = f"project = SUP_AML AND status in (Решен, Отозван, Закрыт, Done) AND resolved >= startOfMonth() AND Разработчики = {usrn} ORDER BY created DESC"

    board_info = jira.jql(opened_str)
    closed = jira.jql(closed_str)
    
    for i in board_info:
        if i == 'issues':
            for ii in board_info[i]:
                if ii['fields']['assignee'] is not None and str(ii['fields']['assignee']['name']) == usrn:
                    fullname = str(ii['fields']['assignee']['displayName'])
                
                if ii['fields']['assignee'] is not None and str(ii['fields']['assignee']['name']) == usrn:
                    url = str(ii['fields']['assignee']['self'])
                    
                    headers = {"Authorization": f"Bearer {user_data['token']}"}
                    
                    response = requests.get(url, headers=headers)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    avatar_url = data['avatarUrls']['48x48']
                    
                    response = requests.get(avatar_url, stream=True, headers=headers)
                    response.raise_for_status()
                    
                    avatar = save_avatar(response.content).replace('board\\', '\\')
                
                if str(ii['fields']['status']['name']).upper() in tasks:
                    tasks[str(ii['fields']['status']['name']).upper()][0][ii['key']] = []
                    tasks[str(ii['fields']['status']['name']).upper()][0][ii['key']].append(f"{ii['fields']['summary']}")
                    tasks[str(ii['fields']['status']['name']).upper()][0][ii['key']].append(ii['fields']['priority']['name'])
                                          
                    tasks[str(ii['fields']['status']['name']).upper()][1] += 1
                    
                    for client in clients:
                        if client in ii['fields']['customfield_10609'][0]:
                            tasks[str(ii['fields']['status']['name']).upper()][0][ii['key']].append(dict_clients[client])
                            
                            if dict_clients[client][0] not in list_of_clients:
                                list_of_clients.append(dict_clients[client][0])
                    
                    for issue in dict_issue:
                        if issue == ii['fields']['issuetype']['name']:
                            tasks[str(ii['fields']['status']['name']).upper()][0][ii['key']].append(dict_issue[issue])

                            
    for i in closed:
        if i == 'issues':
            for ii in closed[i]:
                tasks['ЗАКРЫТЫЕ'][0][ii['key']] = []
                tasks['ЗАКРЫТЫЕ'][0][ii['key']].append(f"{ii['fields']['summary']}")
                tasks['ЗАКРЫТЫЕ'][0][ii['key']].append(ii['fields']['priority']['name'])
                
                tasks['ЗАКРЫТЫЕ'][1] += 1
                
                for client in clients:
                        if client in ii['fields']['customfield_10609'][0]:
                            tasks['ЗАКРЫТЫЕ'][0][ii['key']].append(dict_clients[client])
                            
                            if dict_clients[client][0] not in list_of_clients:
                                list_of_clients.append(dict_clients[client][0])
        
    data = {'tasks': tasks, 'fullname': fullname, 'avatar': avatar, 'list_of_clients': list_of_clients, 'data': 'success'}

    # if get_client is not None:
    # html = render_to_string('tasks_content.html', data)
    # print('[2]', get_client, type(get_client))
    # return JsonResponse({'html': html})

    return render(request, 'jira.html', data)
        
    # print('[1]', get_client, type(get_client))
    # print(tasks)
    # return render(request, 'jira.html', data) 