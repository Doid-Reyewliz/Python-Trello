from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.core.cache import cache


from atlassian import Jira
from pymongo import MongoClient

import asyncio
import aiohttp
from asgiref.sync import sync_to_async, async_to_sync

import logging
logger = logging.getLogger(__name__)

import requests
from PIL import Image
import io, os, time

from django.views.decorators.cache import cache_page

def save_avatar(binary_data, filename):
    image = Image.open(io.BytesIO(binary_data))
    image.save(filename)
    
    return filename

def get_index(my_dict, find):
    key_list = list(my_dict.keys())
    index = key_list.index(find)
    
    return index

def has_number(item):
    return isinstance(item, list) and isinstance(item[1], int)

@cache_page(60 * 15) 
async def jira_view(request):
    try:
        usrn = await sync_to_async(request.session.get)('username')    
        token = await sync_to_async(request.session.get)('token')
        
        with open('data/data_{usrn[2:]}.txt', 'r') as f:
            data = f.read()
            
            if data != '':
                return render(request, 'jira.html', eval(data))
        
        fullname = None
        avatar = None
        list_of_clients = []
        get_client = '0'
                    
        jira = Jira(
            url="https://support.p-s.kz", 
            cookies = True,
            username = usrn,
            token = token
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

        get_client = request.GET.get('client', None)
        
        
        print('[0]', get_client, type(get_client))
                
        if get_client is not None and get_client != '-1':
            await sync_to_async(cache.clear)()
            is_associated = False
            
            for i in range(len(clients)):
                if int(get_client) == i:
                    get_client = clients[i]
                    break
            
            for key, item in dict_clients.items():
                if get_client == key:
                    get_client = item[3]
                    is_associated = True
                    break
            
            if is_associated:
                opened_str = f"project = SUP_AML AND status in ('На уточнении', '3 линия', Тестирование, Очередь, 'Клиент - тестирование') AND resolution = Unresolved AND Разработчики = {usrn} AND cf[10609] = {get_client} ORDER BY created ASC"
                closed_str = f"project = SUP_AML AND status in (Решен, Отозван, Закрыт, Done) AND resolved >= startOfMonth() AND Разработчики = {usrn} AND cf[10609] = {get_client} ORDER BY created ASC"
            else:
                opened_str = f"project = SUP_AML AND status in ('На уточнении', '3 линия', Тестирование, Очередь, 'Клиент - тестирование') AND resolution = Unresolved AND Разработчики = {usrn} ORDER BY created ASC"
                closed_str = f"project = SUP_AML AND status in (Решен, Отозван, Закрыт, Done) AND resolved >= startOfMonth() AND Разработчики = {usrn} ORDER BY created ASC"

        else:
            opened_str = f"project = SUP_AML AND status in ('На уточнении', '3 линия', Тестирование, Очередь, 'Клиент - тестирование') AND resolution = Unresolved AND Разработчики = {usrn} ORDER BY created ASC"
            closed_str = f"project = SUP_AML AND status in (Решен, Отозван, Закрыт, Done) AND resolved >= startOfMonth() AND Разработчики = {usrn} ORDER BY created ASC"

        board_info = await sync_to_async(jira.jql)(opened_str)
        closed = await sync_to_async(jira.jql)(closed_str)

        for i in board_info:
            if i == 'issues':
                for ii in board_info[i]:
                    if ii['fields']['assignee'] is not None and str(ii['fields']['assignee']['name']) == usrn:
                        fullname = str(ii['fields']['assignee']['displayName'])
                    
                    if ii['fields']['assignee'] is not None and str(ii['fields']['assignee']['name']) == usrn:
                        try:
                            url = str(ii['fields']['assignee']['self'])
                            
                            headers = {"Authorization": f"Bearer {token}"}
                            
                            response = await sync_to_async(requests.get)(url, headers=headers)
                            response.raise_for_status()
                            
                            data = response.json()
                            
                            avatar_url = data['avatarUrls']['48x48']
                            
                            response = await sync_to_async(requests.get)(avatar_url, stream=True, headers=headers)
                            response.raise_for_status()
                            
                            avatar = await sync_to_async(save_avatar)(response.content, rf"board/static/images/profile_picture_{usrn[2:]}.png")
                            avatar = avatar.replace('board//', '//')
                            
                            logger.exception("[Avatar 1]: %s", avatar)
                            
                        except:
                            avatar = str(ii['fields']['assignee']['avatarUrls']['48x48'])
                            logger.exception("[Avatar 2]: %s", avatar)                            

                    if str(ii['fields']['status']['name']).upper() in tasks:
                        tasks[str(ii['fields']['status']['name']).upper()][0][ii['key']] = []
                        tasks[str(ii['fields']['status']['name']).upper()][0][ii['key']].append(f"{ii['fields']['summary']}")
                        tasks[str(ii['fields']['status']['name']).upper()][0][ii['key']].append(ii['fields']['priority']['name'])
                                            
                        tasks[str(ii['fields']['status']['name']).upper()][1] += 1
                        
                        for client in clients:
                            if client in ii['fields']['customfield_10609'][0]:
                                tasks[str(ii['fields']['status']['name']).upper()][0][ii['key']].append(dict_clients[client])
                                
                                if dict_clients[client][0] not in list_of_clients:
                                    list_of_clients.append([dict_clients[client][0], get_index(dict_clients, client)])    

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
                                    list_of_clients.append([dict_clients[client][0], get_index(dict_clients, client)])
            
            
        list_of_clients = list({tuple(item) for item in list_of_clients if has_number(item)})

        data = {
            'tasks': tasks, 
            'fullname': fullname, 
            'avatar': avatar, 
            'list_of_clients': list_of_clients, 
            'data': 'success'
        }

        if get_client is not None:
            html = await sync_to_async(render_to_string)('tasks_content.html', data)
            print('[2]', get_client, type(get_client))
            return JsonResponse({'html': html})

        logger.exception(f"{usrn}%s", tasks)
            
        print('[1]', get_client, type(get_client))
        del tasks, board_info, closed, list_of_clients, clients, dict_clients, get_client, fullname, avatar
        
        with open('data/data_{usrn[2:]}.txt', 'w') as f:
            f.write(data)
        
        return render(request, 'jira.html', data)

    except Exception as e:
        logger.exception("Error in login: %s", e)
        return redirect('/')