import requests
import json


headers = {
    'X-Cosmos-Token': '-dz12h9HqjRaku_BJgIrdQ',
    'Content-Type': 'application/json',
    'User-Agent': 'Cosmos-API-Request'
}

r = requests.get(
    'https://api.cosmos.bluesoft.com.br/gtins/7896512918536.json', headers=headers)


r_json = json.loads(r.text)

print(r_json['description'])

# print(r.text)