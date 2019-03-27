import requests
import tqdm
import json

endpoint = 'http://localhost:5000/misinfo/api'



response = requests.get(endpoint + '/users_stored')

ids = response.json()

results = []

for id in tqdm.tqdm(ids):
    res = requests.get(endpoint + '/count_urls/users/{}?allow_cached=true'.format(id)).json()
    screen_name = res.get('screen_name', None)
    score = res.get('score', None)
    print(screen_name, score)
    results.append({
        'id': id,
        'screen_name': screen_name,
        'score': score
    })

with open('results_all.json', 'w') as f:
    json.dump(results, f, indent=2)