from django.shortcuts import render
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.cache import cache_page

from atlassian import Jira
from pymongo import MongoClient


class Database:
    def __init__(self, db_user, db_pass):
        connection_string = f"mongodb+srv://{db_user}:{db_pass}@primecluster.6buri4v.mongodb.net/?retryWrites=true&w=majority"

        self.client = MongoClient(connection_string)
        self.db = self.client['Users']
        self.users_collection = self.db["Prime"]

    def get_user(self, mail):
        return self.users_collection.find_one({"email": f'{mail}@p-s.kz'})

# @cache_page(60 * 15)
def jira_view(request):
    db_user = "alfanauashev"
    db_pass = '50SBW50gejk8Wn7F'
    
    usrn = request.session.get('username')
    pswd = request.session.get('password')
    
    db = Database(db_user, db_pass)
    user_data = db.get_user(usrn)
    
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
    
    fullname = None
    avatar = None
    list_of_clients = []
    list_of_priority = []
    
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
        "RBK":                                      ["RBK", "#6cc3e0", "#164555", "SETTINGS-89"],
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
    
    dict_prior = {
        "Критический": "Critical",
        "Высокий": "High",
        "Средний": "Medium",
        "Низкий": "Low"
    }
    
    jql_str = f"project = SUP_AML AND status in (Решен, Отозван, Закрыт, Done) AND resolved >= startOfMonth() AND Разработчики = {usrn} ORDER BY created DESC"

    closed = jira.jql(jql_str)
    
    board_id = 28
    board_info = jira.get_issues_for_board(board_id, jql=None, fields=None, start=0, limit=None, expand=None)

    for i in board_info:
        if i == 'issues':
            for ii in board_info[i]:
                if ii['fields']['assignee'] is not None and str(ii['fields']['assignee']['name']) == usrn:
                    fullname = str(ii['fields']['assignee']['displayName'])
                
                if ii['fields']['assignee'] is not None and str(ii['fields']['assignee']['name']) == usrn:
                    avatar = str(ii['fields']['assignee']['avatarUrls']['48x48'])

                
                if str(ii['fields']['status']['name']).upper() in tasks:
                    tasks[str(ii['fields']['status']['name']).upper()][0][ii['key']] = []
                    tasks[str(ii['fields']['status']['name']).upper()][0][ii['key']].append(f"{ii['fields']['summary']}")
                    tasks[str(ii['fields']['status']['name']).upper()][0][ii['key']].append(ii['fields']['priority']['name'])
                    
                    if ii['fields']['priority']['name'] not in list_of_priority:
                        list_of_priority.append(ii['fields']['priority']['name'])
                    
                    tasks[str(ii['fields']['status']['name']).upper()][1] += 1
                    
                    for client in clients:
                        if client in ii['fields']['customfield_10609'][0]:
                            tasks[str(ii['fields']['status']['name']).upper()][0][ii['key']].append(dict_clients[client])
                            
                            if dict_clients[client][0] not in list_of_clients:
                                list_of_clients.append(dict_clients[client][0])
                            
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
    
    return render(request, 'jira.html', {'tasks': tasks, 'fullname': fullname, 'avatar': avatar, 'list_of_clients': list_of_clients, 'list_of_priority': list_of_priority, 'data': 'success'}) 