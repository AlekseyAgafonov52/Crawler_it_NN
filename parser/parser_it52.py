from flask import Flask
import requests
from bs4 import BeautifulSoup
import logging
import main

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def parse_it52():
    url = "https://www.it52.info/events"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept-Language': 'ru-RU,ru;q=0.9'
    }
    events = []
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        event_panels = soup.select('div.panel-body')
        
        for panel in event_panels:
            try:
                title_elem = panel.select_one('h2.event-header a')
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                event_url = "https://www.it52.info" + title_elem['href']
                
                date_elem = panel.select_one('span[title="Время проведения"]')
                date_str = date_elem.get_text(strip=True).replace('►', '') if date_elem else "Дата не указана"
                
                location_elem = panel.select_one('span[title="Место проведения"]')
                location = location_elem.get_text(strip=True).replace('►', '') if location_elem else "Место не указано"
                
                desc_elem = panel.select_one('div.event-description') or panel.select_one('p.event-about')
                full_description = ""
                short_description = ""
                if desc_elem:
                    full_description = main.clean_html(str(desc_elem))
                    text_content = desc_elem.get_text(strip=False)
                    short_description = text_content[:200] + ('...' if len(text_content) > 200 else '')
            
                events.append({
                    "title": title,
                    "date_str": date_str,
                    "location": location,
                    "short_description": short_description,
                    "full_description": full_description,
                    "url": event_url,
                    "source": "it52.info"
                })
                
            except Exception as e:
                logger.error(f"Ошибка обработки карточки: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Ошибка парсинга it52.info: {e}")
    
    return events
