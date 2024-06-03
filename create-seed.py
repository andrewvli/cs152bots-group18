def create_seed(filename):
    with open(filename) as f:
        for line in f:
            line = line.strip()
            print(f'INSERT INTO blacklisted_links (blacklisted_link) VALUES (\'https://{line}\');')

create_seed('cryptoscamdb-blacklist.txt')