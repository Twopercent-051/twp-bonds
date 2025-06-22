import httpx
import json

payload = {
    # "customFilters[issue_date][from]": "2014-06-09",
    # "customFilters[issue_date][to]": "2025-06-11",
    # "customFilters[matdate][from]": "2025-06-10",
    # "customFilters[matdate][to]": "2057-08-10",
    # # ... другие параметры ...
    "customFilters[strategy][]": ["strategy1", "strategy1"],  # если несколько одинаковых, используй список
    # # ...
    # "customFilters[search_string]": "",
}

response = httpx.post("https://www.dohod.ru/assets/components/dohodbonds/connectorweb.php?action=info", data=payload)
data = json.loads(response.text)
sorted_data = sorted(data, key=lambda x: x["price_return"], reverse=True)

# Вывод первых 5 словарей
top_5 = sorted_data[:5]
for item in top_5:
    print(item)
