import json
import requests

from tqdm import tqdm

EVALUATION_URL = 'http://localhost:5000/count_urls/users?handle='

with open('list.json') as f:
    content = json.load(f)

responses = {}
for display_name in tqdm(content):
    responses[display_name] = requests.get(EVALUATION_URL + display_name).json()

with open('results.json', 'w') as f:
    json.dump(responses, f, indent=2)
