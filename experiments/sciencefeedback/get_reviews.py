import re
from pymongo import MongoClient

client = MongoClient()
claimreviews_collection = client['datasets_resources']['claim_reviews']

def get_claimreviews():
    domain_regexp = re.compile('.*sciencefeedback.*|.*climatefeedback.|.*healthfeedback.*')
    matches = claimreviews_collection.find({'url': domain_regexp})
    matches = [el for el in matches]
    print('found:', len(matches))
    return 

def main():
    crs = get_claimreviews()

if __name__ == "__main__":
    main()