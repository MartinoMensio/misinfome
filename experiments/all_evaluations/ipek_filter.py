import pandas as pd


df = pd.read_table('joined_tables.tsv', parse_dates=['publish_date', 'review_date'], date_parser=lambda col: pd.to_datetime(col, utc=True, errors = 'coerce'), dtype={'normalised_value': float})
selection = df[df['lang'] == 'en']

selection.to_csv('joined_en.tsv', sep='\t')

excluded_domains = ['twitter.com', 'facebook.com', 'youtu.be', 'youtube.com',
                    'instagram.com', 'c-span.org', 'climatefeedback.org',
                    'washingtonpost.com', 'snopes.com', 'reddit', 'boredpanda.com',
                    'eurosport.com', 'bit.ly', 'factba.se', 'factcheck.org',
                    'fastcompany.com', 'forbes.com', 'justice.gov', 'kznhealth.gov.za',
                    'whitehouse.gov', 'yahoo.com', 'vimeo.com', 'redd.it', 'reddit.com', 'redice.tv',
                    'rollingstone.com', 'politico.com', 'ancient-code.com',
                    'biliyomuydun.com', 'change.org', 'en.wikipedia.org', 'google.com', 'googlesightseeing.com',
                    'redd.it', 'soundcloud.com', 'webcache.googleusercontent.com',
                    'vimeo.com', 'wellahealth.com', '12up.com', '24sante.com',
                    '01easylife.com', '90min.com', 'abcnews.go.com',
                    'abundanthope.net', 'adonis49.wordpress.com', 'archive.is', 'archive.org', 'archives.org',
                    'archive.today', 'balls.ie', 'birgun.net', 'celebritiesbuzz.com.gh',
                    'chicagotribune.com', 'cole.house.gov', 'drive.google.com',
                    'dw.com', 'epa.gov', 'on.fb.me', 'plus.google.com',
                    'realclimatescience.com', 'realfarmacy.com', 'rearfront.com',
                    'rtvm.gov.ph', 'scienceinfo.news', 'hollywoodreporter.com', 'indiatodaydailynews.blogspot.com',
                    'house.gov', 'scribd.com', 'bloom.bg', 'indiatoday.in', 'politifact.com']