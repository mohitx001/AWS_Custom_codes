import requests
import re

# open the file
with open("keywords.txt", "r") as file:
    # create a list of keywords
    keywords = [line.strip() for line in file]

# iterate over each keyword
for keyword in keywords:
    # search for a keyword using Bing
    response = requests.get(f"https://www.bing.com/search?q={keyword}")

    # get the response text
    text = response.text

    # find the first HTTPS website using a regular expression
    pattern = r"https://[^\s\"]+"
    match = re.search(pattern, text)

    # get the URL of the website
    if match:
        url = match.group()
    else:
        url = None

    print(f"Keyword: {keyword}, URL: {url}")