import csv
import json
import requests
import matplotlib
matplotlib.use('PS')
import matplotlib.pyplot as plt
plt.style.use('seaborn-whitegrid')
import numpy as np

input_file = 'input_urls.tsv'
url_time_distrib = 'http://localhost:5000/misinfo/api/analysis/time_distribution'
url_get_factchecking_date = 'http://localhost:5000/misinfo/api/utils/time_published'

def read_inputs():
    with open(input_file) as f:
        reader = csv.DictReader(f, delimiter='\t')
        result = [r for r in reader]
        return result


def retrieve():
    rows = read_inputs()
    result_month = []
    result_week = []
    result_day = []
    for r in rows:
        factchecking_url = r['factchecking']
        claim_url = r['claim']
        factchecking_updated = r['factchecking_updated']
        id = r['id']
        response_date = requests.get(url_get_factchecking_date, params={'url': factchecking_updated}).json()

        response_factchecking_week = requests.get(url_time_distrib, params={'url': factchecking_url, 'time_granularity': 'week'}).json()
        response_claim_week = requests.get(url_time_distrib, params={'url': claim_url, 'time_granularity': 'week'}).json()
        response_factchecking_day = requests.get(url_time_distrib, params={'url': factchecking_url, 'time_granularity': 'day'}).json()
        response_claim_day = requests.get(url_time_distrib, params={'url': claim_url, 'time_granularity': 'day'}).json()
        response_factchecking_month = requests.get(url_time_distrib, params={'url': factchecking_url, 'time_granularity': 'month'}).json()
        response_claim_month = requests.get(url_time_distrib, params={'url': claim_url, 'time_granularity': 'month'}).json()


        result_week.append({
            'id': id,
            'claim_url': claim_url,
            'factchecking_url': factchecking_url,
            'factchecking_date': response_date['round_week'],
            'claim_share_distribution': response_claim_week,
            'factchecking_share_distribution': response_factchecking_week
        })
        result_day.append({
            'id': id,
            'claim_url': claim_url,
            'factchecking_url': factchecking_url,
            'factchecking_date': response_date['round_day'],
            'claim_share_distribution': response_claim_day,
            'factchecking_share_distribution': response_factchecking_day
        })
        result_month.append({
            'id': id,
            'claim_url': claim_url,
            'factchecking_url': factchecking_url,
            'factchecking_date': response_date['round_month'],
            'claim_share_distribution': response_claim_month,
            'factchecking_share_distribution': response_factchecking_month
        })

    with open('result_week.json', 'w') as f:
        json.dump(result_week, f, indent=2)
    with open('result_day.json', 'w') as f:
        json.dump(result_day, f, indent=2)
    with open('result_month.json', 'w') as f:
        json.dump(result_month, f, indent=2)

def plot_all():
    for granularity in ['week', 'month', 'day']:
        f_name = 'result_{}.json'.format(granularity)
        with open(f_name) as f:
            content = json.load(f)
        for el in content:
            id = el['id']
            plot_thing(el, 'id_{}_granularity_{}'.format(id, granularity))


def plot_thing(data, name):
    font = {
        #'family' : 'normal',
        #'weight': 'bold',
        'size': 15
    }

    matplotlib.rc('font', **font)
    fig = plt.figure(num=None, figsize=(25, 10), dpi=500)
    ax = plt.axes()

    x1 = [el['name'] for el in sorted(data['claim_share_distribution'], key=lambda el: el['name'])]
    x2 = [el['name'] for el in sorted(data['factchecking_share_distribution'], key=lambda el: el['name'])]
    y1 = [el['value'] for el in sorted(data['claim_share_distribution'], key=lambda el: el['name'])]
    y2 = [el['value'] for el in sorted(data['factchecking_share_distribution'], key=lambda el: el['name'])]
    ax.plot(x1, y1, color='r')
    ax.plot(x2, y2, color='g')

    create_tsv([x1, y1, x2, y2], name)

    #plt.yscale('symlog', basey=2)
    plt.axvline(x=data['factchecking_date'], color='k')
    plt.xticks(rotation=90)

    all_x = sorted([el for el in set(x1 + x2)])
    tot_x = len(all_x)
    scale_factor = 1 + tot_x // 40
    ax.set_xticks(all_x[::scale_factor])
    ax.set_xticklabels(all_x[::scale_factor])

    plt.ylabel('Number of tweets containing the URL')
    plt.legend(['Claim: {}'.format(data['claim_url']), 'Fact-checking: {}'.format(data['factchecking_url']), 'time of fact-checking'], loc='upper right', fontsize='14')
    #plt.locator_params(nbins=10)

    plt.savefig('figs/' + name + '.png')
    plt.close()

def create_tsv(iters, name):
    lines = []
    for z in zip(*iters):
        #print(z)
        z = [str(el) for el in z]
        lines.append('\t'.join(list(z)))
    with open('tsvs/' + name + '.tsv', 'w') as f:
        f.write('\n'.join(lines))

if __name__ == "__main__":
    #retrieve()
    plot_all()