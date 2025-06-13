import requests
from bs4 import BeautifulSoup
import logging
import main

TARGET_CITY = "Нижний Новгород"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_networkly():
    base_url = "https://networkly.app"
    events_url = "https://networkly.app/event?"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept-Language': 'ru-RU,ru;q=0.9'
    }
    events = []
    
    try:
        response = requests.get(events_url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        event_cards = soup.select('article.event-item.card')
        
        for card in event_cards:
            try:              
                title_elem = card.find('h2').find('a')
                title = title_elem.get_text(strip=True)
                event_url = base_url + title_elem['href']
                
                event_response = requests.get(event_url, headers=headers, timeout=15)
                event_soup = BeautifulSoup(event_response.text, 'html.parser')
               
                official_site_url = None
                nav_block = event_soup.find('nav', class_='navbar sticky-bottom bg-transparent')
                if nav_block:
                    container = nav_block.find('div', class_='container-fluid')
                    if container:
                        site_link = container.find('a', class_='btn-primary', href=True)
                        if site_link:
                            official_site_url = site_link['href']
                
                final_url = official_site_url if official_site_url else event_url

                date_info = event_soup.find('span', class_='date')
                date_str = date_info.get_text(strip=True)[4:] if date_info else "Дата не указана"
                
                location = None
                for row in event_soup.select('table.event-info tr'):
                    if TARGET_CITY in row.get_text():
                        location = row.get_text(strip=True)
                        break
                
                if not location or TARGET_CITY not in location:
                    continue

                description_html = []
                event_info_table = event_soup.find('table', class_='event-info')
                
                if event_info_table:
                    current_element = event_info_table.find_next_sibling()
                    skip_first = True
                    
                    while current_element and current_element.name != 'div' and not current_element.get('id'):
                        if current_element.name == 'p':
                            if skip_first and 'mt-3' in current_element.get('class', []):
                                skip_first = False
                                current_element = current_element.find_next_sibling()
                                continue
                            if current_element.get_text(strip=True):
                                description_html.append(str(current_element))
                        current_element = current_element.find_next_sibling()
                
                raw_html = ''.join(description_html)
                full_description = main.clean_html(raw_html) if raw_html else ""
              
                text_content = ' '.join(p.get_text(strip=False) for p in BeautifulSoup(raw_html, 'html.parser').find_all('p'))
                short_description = text_content[:200] + ('...' if len(text_content) > 200 else '')

                events.append({
                    "title": title,
                    "date": date_str,
                    "location": location,
                    "short_description": short_description,
                    "full_description": full_description,
                    "url": final_url,
                    "source": "networkly.app"
                })
        
            except Exception as e:
                logger.error(f"Ошибка обработки {event_url}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Ошибка парсинга networkly.app: {str(e)}")
    
    return events