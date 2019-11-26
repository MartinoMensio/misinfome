import json
import csv


def extract_tsv(f_name, out_name):
    with open(f_name) as f:
        content = json.load(f)
    res = [['key', 'value', 'confidence']]
    for k, v in content.items():
        if ' ' in k:
            continue
        if '.' not in k:
            continue
        res.append([k, v['value'], v['confidence']])
    with open(out_name, 'w') as f:
        print(res[0])
        print(res[1])
        txt = ''
        for l in res:
            txt += '\t'.join([str(el) for el in l]) + '\n'
        f.write(txt)

    

extract_tsv('domains.json', 'domains.tsv')
extract_tsv('urls.json', 'urls.tsv')
