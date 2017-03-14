"""Imports"""
import threading
import time
import re
from urllib.request import urlopen

import ujson


def check_item(item, tab, search_item):
    """Checks item against search_item."""

    item_name = item['name']
    item_typeline = item['typeLine']
    league = item['league']
    note = item.get('note')
    x_coord = str(item['x'])
    y_coord = str(item['y'])

    if search_item['league'] != league:
        return False

    if search_item['name'] in item_name:
        name = re.sub('<.*>', '', item_name)
    elif search_item['name'] in item_typeline:
        name = re.sub('<.*>', '', item_typeline)
    else:
        return False

    price = note if note else tab

    if bool(re.search(r'^~(price|b\/o) [0-9]+ [a-z]+$', price)):
        price_parts = price.split(' ')
        price_quantity = int(price_parts[1])
        price_type = price_parts[2]
        price_string = str(price_quantity) + " " + price_type
    else:
        return False

    if (search_item['price_type'] and
            search_item['price_type'] != price_type):
        return False

    if (search_item['price_type'] and
            search_item['price_quantity'] and
            search_item['price_quantity'] < price_quantity):
        return False

    ret = ujson.dumps(
        {
            "name": name,
            "price": price_string,
            "league": league,
            "x": x_coord,
            "y": y_coord
        })
    return ret


def parse_stashes(stashes, searches):
    """Parses stashes."""

    for stash in stashes:
        character_name = stash['lastCharacterName']
        tab = stash['stash']
        items = stash['items']

        for item in items:
            for search in searches:
                found_item = check_item(item, tab, search)
                if found_item:
                    break

            if not found_item:
                continue

            found_item = ujson.loads(found_item)
            print(
                found_item['price'], "\t"
                "@" + character_name,
                "I would like to buy your", found_item['name'],
                "listed for", found_item['price'],
                "in", found_item['league'],
                "(tab:" + tab, found_item['x'] + "x," + found_item['y'] + "y" + ").")
            print('\a', end="")


def live_indexing(change_id, searches):
    """Indexing from current change_id."""

    start_time = time.time()

    url = 'http://api.pathofexile.com/public-stash-tabs?id=' + change_id
    request = urlopen(url)
    data = ujson.loads(request.read())

    new_thread = threading.Thread(
        target=parse_stashes, args=(data['stashes'], searches))
    new_thread.start()

    download_duration = (time.time() - start_time)
    if download_duration < 1.0:
        time.sleep(1.0 - download_duration)

    live_indexing(data['next_change_id'], searches)


def main():
    """Main"""

    with open('searches.json') as searches_file:
        searches_data = ujson.loads(searches_file.read())

    searches = searches_data['searches']

    url = 'http://api.poe.ninja/api/Data/GetStats'
    request = urlopen(url)
    data = ujson.loads(request.read())

    live_indexing(data['nextChangeId'], searches)


if __name__ == "__main__":
    main()
