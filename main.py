from flask import Flask, render_template, redirect, url_for, request, send_from_directory
from pymongo import MongoClient
from bs4 import BeautifulSoup
import logging
import re
from datetime import datetime, timedelta
import locale
from parser import parser_it52, parser_ict2go, parser_networkly
# locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')  # для Linux/macOS
locale.setlocale(locale.LC_TIME, 'Russian_Russia.1251')  # для Windows

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def clean_html(html):
    """Очистка HTML от потенциально опасных тегов"""
    if not html:
        return ""

    allowed_tags = ['p', 'br', 'ul', 'ol', 'li', 'strong', 'em', 'a', 'div', 'span']
    soup = BeautifulSoup(html, 'html.parser')

    for tag in soup.find_all(True):
        if tag.name not in allowed_tags:
            tag.decompose()

    for tag in soup.find_all(True):
        if tag.name == 'a':
            attrs = {'href': tag.get('href', '')}
            tag.attrs = attrs
        else:
            tag.attrs = {}
    return str(soup)


def save_to_mongo(events):
    if collection is None:
        logger.error("MongoDB не подключена")
        return 0

    new_count = 0
    for event in events:
        try:
            if collection.find_one({"title": event["title"]}) is None:
                collection.insert_one(event)
                new_count += 1
            else:
                logger.info(f"Мероприятие '{event['title']}' уже существует, пропускаем")

        except Exception as e:
            logger.error(f"Ошибка сохранения: {e}")
    return new_count

@app.route("/")
def index():
    try:
        keyword = request.args.get("q", "").lower()
        date_filter = request.args.get("date_filter", "")
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        query = {}

        if keyword:
            query["$or"] = [
                {"title": {"$regex": keyword, "$options": "i"}},
                {"short_description": {"$regex": keyword, "$options": "i"}},
                {"full_description": {"$regex": keyword, "$options": "i"}}
            ]

        raw_events = list(collection.find(query).sort("scraped_at", -1)) if collection is not None else []

        filtered_events = []
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, "%Y-%m-%d")
                for event in raw_events:
                    event_date = parse_normalized_date(event.get("date") or event.get("date_str", ""))
                    if event_date and event_date.date() == filter_date.date():
                        filtered_events.append(event)
            except ValueError:
                logger.warning("Неверный формат даты для фильтра")
                filtered_events = raw_events
        else:
            for event in raw_events:
                event_date = parse_normalized_date(event.get("date") or event.get("date_str", ""))
                if not event_date or event_date >= today:
                    filtered_events.append(event)

        return render_template(
            "index.html",
            events=filtered_events,
            keyword=keyword,
            date_filter=date_filter,
            current_year=today.year
        )

    except Exception as e:
        logger.error(f"Ошибка загрузки: {e}")
        return render_template("error.html", message="Ошибка загрузки данных")

@app.route("/update")
def update():
    if collection is not None:
        collection.delete_many({})
    events = parser_it52.parse_it52() + parser_ict2go.parse_ict2go() + parser_networkly.parse_networkly()
    added = save_to_mongo(events)
    logger.info(f"Добавлено {added} новых мероприятий (всего найдено: {len(events)})")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

