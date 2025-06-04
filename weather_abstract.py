import requests
from bs4 import BeautifulSoup
from pypinyin import lazy_pinyin

# ========== 城市信息直接写在代码中 ==========
CITIES = {
    "TcKAYAx3b4XFf3xJmJ6NDP": {"city_name": "钱塘", "city_id": "101210111"},
    "SrPBHD3H7pQwstdXZWsKC3": {"city_name": "官渡", "city_id": "101290115"}
}

# ========== 抓取天气摘要并推送 ==========
def fetch_weather_summary(city_name, city_id):
    pinyin = ''.join(lazy_pinyin(city_name)).lower()
    url = f"https://www.qweather.com/weather/{pinyin}-{city_id}.html"

    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        # 获取天气摘要
        div = soup.find("div", class_="current-abstract")
        if div:
            summary = div.get_text(strip=True)
        else:
            summary = "未找到天气摘要"

        # 获取图标 URL
        icon_img_tag = soup.find("div", class_="current-live__item").find("img")
        icon_url = icon_img_tag["src"] if icon_img_tag else "https://a.hecdn.net/img/common/icon/202106d/501.png"  # 默认图标

        return summary, icon_url, url
    except Exception as e:
        print(f"[摘要抓取] 失败: {e}")
        return "天气摘要抓取失败", "https://a.hecdn.net/img/common/icon/202106d/501.png", url

def send_weather_summary_notification():
    for key, city in CITIES.items():
        summary, icon_url, url = fetch_weather_summary(city["city_name"], city["city_id"])
        bark_url = f"https://api.day.app/{key}/{city['city_name']} 天气摘要/{summary}?icon={icon_url}&isArchive=1&url={url}"

        try:
            requests.get(bark_url).raise_for_status()
            print(f"[摘要通知] 已发送：{summary}")
        except Exception as e:
            print(f"[摘要通知] 发送失败: {e}")

# ========== 主流程 ==========
if __name__ == "__main__":
    send_weather_summary_notification()
