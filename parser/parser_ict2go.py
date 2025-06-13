from flask import Flask
import requests
from bs4 import BeautifulSoup
import logging

import main

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def parse_ict2go():
    base_url = "https://ict2go.ru"
    events_url = "https://ict2go.ru/regions/Nizhny_Novgorod/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept-Language': 'ru-RU,ru;q=0.9'
    }
    events = []
    
    try:
        response = requests.get(events_url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        event_links = soup.select('a.event-title[href^="/events/"]')
        
        for link in event_links:
            try:
                event_url = base_url + link['href']
                title = link.get_text(strip=True)
                
                event_response = requests.get(event_url, headers=headers, timeout=15)
                event_response.raise_for_status()
                event_soup = BeautifulSoup(event_response.text, 'html.parser')
                
                official_site_url = None
                event_links_div = event_soup.find('div', class_='event-links')
                if event_links_div:
                    site_link = event_links_div.find('a', href=True, string=lambda t: t and 'Сайт мероприятия' in t)
                    if site_link:
                        official_site_url = site_link['href']
                
                final_url = official_site_url if official_site_url else event_url

                page_title = event_soup.find('h1', class_='event-h1')
                if page_title:
                    title = page_title.get_text(strip=True)
                
                date_info = ""
                date_div = event_soup.find('div', class_='event-info')
                if date_div:
                    date_p = date_div.find('p', class_='date-info')
                    if date_p:
                        date_info = date_p.get_text(strip=True)
                        date_info = date_info.replace("Дата проведения:", "").strip()
                
                location = ""
                place_div = event_soup.find('div', class_='event-info')
                if place_div:
                    place_p = place_div.find('p', class_='place-info')
                    if place_p:
                        place_text = place_p.get_text(" ", strip=True)
                        location = place_text.replace("Место проведения:", "").strip() if place_text else "Место не указано"

                
                full_description = ""
                short_description = ""
                desc_div = event_soup.find('div', class_='tab-item description-info')
                if desc_div:
                    full_description = main.clean_html(str(desc_div))
                    text_content = desc_div.get_text(strip=False)
                    short_description = text_content[:200] + ('...' if len(text_content) > 200 else '')
                
                events.append({
                    "title": title,
                    "date": date_info,
                    "location": location,
                    "short_description": short_description,
                    "full_description": full_description,
                    "url": final_url,
                    "source": "ict2go.ru"
                })
            
            except Exception as e:
                logger.error(f"Ошибка обработки {event_url}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Ошибка парсинга: {str(e)}")
    
    return events