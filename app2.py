from flask import Flask, request, render_template, send_file
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

def fetch_pages(url, max_results):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    results = []
    try:
        driver.get(url)
        time.sleep(5)
        
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        while len(results) < max_results:
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
            time.sleep(5)
            
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            articles = soup.find_all('article', class_='yQDlj3B5DI5YO8c8Ulio')

            for article in articles:
                title_tag = article.find('h2', class_='LnpumSThxEWMIsDdAT17')
                title = title_tag.get_text(strip=True) if title_tag else "N/A"
                link_tag = article.find('a', href=True, class_='Rn_JXVtoPVAFyGkcaXyK')
                link = link_tag['href'] if link_tag else "N/A"
                snippet_tag = article.find('div', class_='OgdwYG6KE2qthn9XQWFC')
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else "N/A"

                results.append({
                    'Title': title,
                    'Link': link,
                    'Snippet': snippet
                })
                
                if len(results) >= max_results:
                    break
    finally:
        driver.quit()
    
    return results

def count_keywords(text, keywords):
    count = 0
    for keyword in keywords:
        count += text.lower().count(keyword.lower())
    return count

def parse_search_results(results, keywords):
    parsed_results = []
    for result in results:
        title = result['Title']
        link = result['Link']
        snippet = result['Snippet']

        keyword_count = count_keywords(title + " " + snippet, keywords)

        parsed_results.append({
            'Title': title,
            'Link': link,
            'Snippet': snippet,
            'Keyword Count': keyword_count
        })

    return parsed_results

def save_to_excel(data, output_file):
    df = pd.DataFrame(data)
    df.to_excel(output_file, index=False, engine='openpyxl')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form['query']
    max_results = int(request.form['max_results'])
    keywords = request.form['keywords'].split(',')
    
    url = f'https://duckduckgo.com/?t=h_&q={query}&ia=web'
    raw_results = fetch_pages(url, max_results)
    search_results = parse_search_results(raw_results, keywords)
    output_file = 'search_results.xlsx'
    save_to_excel(search_results, output_file)
    
    return send_file(output_file, as_attachment=True, download_name='search_results.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

if __name__ == '__main__':
    app.run(debug=True)
