import sqlite3
import random
import re
import Levenshtein
import logging
from sklearn.metrics import confusion_matrix, classification_report

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

# Function to get top sites from the database
def get_top_sites(limit=10000):
    logging.debug(f"Fetching top {limit} sites from the database.")
    conn = sqlite3.connect('mod_db.sqlite')
    cursor = conn.cursor()
    cursor.execute('SELECT site FROM tranco_top_sites ORDER BY rank LIMIT ?', (limit,))
    top_sites = [row[0] for row in cursor.fetchall()]
    conn.close()
    return top_sites

top_sites = get_top_sites()
logging.info(f"Retrieved {len(top_sites)} top sites.")

# Function to modify a URL to simulate a flagged site
def modify_url(url):
    modifications = [
        lambda u: u.replace('a', '@'),
        lambda u: u.replace('e', '3'),
        lambda u: u.replace('i', '1'),
        lambda u: u.replace('o', '0'),
        lambda u: u + '.xyz',
        lambda u: u.replace('com', 'cm')
    ]
    return random.choice(modifications)(url)

# Generate flagged URLs
def generate_flagged_urls(top_sites, count=1000):
    logging.debug(f"Generating {count} flagged URLs.")
    return [modify_url(site) for site in random.sample(top_sites, count)]

flagged_urls = generate_flagged_urls(top_sites)
logging.info(f"Generated {len(flagged_urls)} flagged URLs.")

# Generate safe URLs
def generate_safe_urls(top_sites, count=1000):
    logging.debug(f"Generating {count} safe URLs.")
    return random.sample(top_sites, count)

safe_urls = generate_safe_urls(top_sites)
logging.info(f"Generated {len(safe_urls)} safe URLs.")

# Combine flagged and safe URLs into test cases
test_cases = [(url, True) for url in flagged_urls] + [(url, False) for url in safe_urls]

# Shuffle the test cases
random.shuffle(test_cases)
logging.info(f"Shuffled the test cases.")

# Collect results
true_labels = []
predicted_labels = []

# Function to extract domain from URL
def extract_domain(url):
    match = re.match(r'(https?://)?(www\.)?([^/]+)', url)
    return match.group(3) if match else url

# Function to check domain similarity
def domain_similarity(domain1, domain2):
    return Levenshtein.ratio(domain1, domain2)

def check_domain_similarity(db_cursor, urls):
    try:
        logging.debug(f"Checking domain similarity for URLs: {urls}")
        db_cursor.execute('SELECT site FROM tranco_top_sites')
        top_sites = db_cursor.fetchall()
        top_sites = [site[0] for site in top_sites]

        similar_sites = []
        for url in urls:
            domain = extract_domain(url)
            for top_site in top_sites:
                if domain_similarity(domain, top_site) > 0.7:  # similarity threshold
                    similar_sites.append(top_site)
        # sort by similarity
        similar_sites = sorted(similar_sites, key=lambda x: domain_similarity(domain, x), reverse=True)

        logging.debug(f"Similar sites found: {similar_sites}")
        return similar_sites
    except sqlite3.Error as e:
        logging.error(f"Error checking domain similarity: {e}")
        return []

def check_exact_match(db_cursor, urls):
    try:
        logging.debug(f"Checking exact match for URLs: {urls}")
        db_cursor.execute('SELECT site FROM tranco_top_sites')
        top_sites = db_cursor.fetchall()
        top_sites = [site[0] for site in top_sites]

        for url in urls:
            domain = extract_domain(url)
            if domain in top_sites:
                logging.debug(f"Exact match found: {domain}")
                return True

        logging.debug(f"No exact match found for: {urls}")
        return False
    except sqlite3.Error as e:
        logging.error(f"Error checking exact match: {e}")
        return False

# Function to run the tests
def run_tests(test_cases):
    logging.info(f"Running tests with {len(test_cases)} cases.")
    conn = sqlite3.connect('mod_db.sqlite')
    cursor = conn.cursor()

    for i, (url, expected) in enumerate(test_cases):
        logging.debug(f"Testing URL {i+1}/{len(test_cases)}: {url}")
        exact_match = check_exact_match(cursor, [url])
        flagged = False

        if not exact_match:
            similar_sites = check_domain_similarity(cursor, [url])
            flagged = bool(similar_sites)

        true_labels.append(expected)
        predicted_labels.append(flagged)
    
    conn.close()

# Run the tests
run_tests(test_cases)

# Generate confusion matrix and classification report
conf_matrix = confusion_matrix(true_labels, predicted_labels)
report = classification_report(true_labels, predicted_labels, target_names=["Not Flagged", "Flagged"])

logging.info("Confusion Matrix:")
logging.info(conf_matrix)
logging.info("\nClassification Report:")
logging.info(report)

print("Confusion Matrix:")
print(conf_matrix)
print("\nClassification Report:")
print(report)
