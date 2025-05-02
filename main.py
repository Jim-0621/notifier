import os
from datetime import timedelta, datetime
import requests
import json
import time
from pypinyin import lazy_pinyin

import schedule

# 配置
API_KEY = "2e2eeb1703da4949988b5bd59c2aaf2e"  # 和风天气 API Key
CITIES = {
    "TcKAYAx3b4XFf3xJmJ6NDP": {"city_name": "钱塘", "city_id": "101210111"},
    "SrPBHD3H7pQwstdXZWsKC3": {"city_name": "温岭", "city_id": "101210607"}
}
BARK_KEYS = list(CITIES.keys())  # 获取所有Bark密钥
TEMP_RECORD_FILE = "temperature_record.json"  # 保存温度记录的文件

# 获取当天的天气信息
def get_weather(city_id):
    """获取指定城市的天气信息，包括最高温度"""
    url = f"https://devapi.qweather.com/v7/weather/3d?location={city_id}&key={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # 如果返回的状态码不是200，抛出异常
        data = response.json()

        if "daily" in data:
            daily_weather = data["daily"][0]  # 获取当天的天气数据
            weather_text = daily_weather["textDay"]  # 白天的天气情况
            min_temp = daily_weather["tempMin"]  # 最低温度
            max_temp = daily_weather["tempMax"]  # 最高温度
            weather_icon = daily_weather.get("iconDay", "100")  # 获取白天气象图标
            return weather_text, min_temp, max_temp, weather_icon
        else:
            return "天气数据获取失败", None, None, "100"  # 默认图标
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return "天气数据获取失败", None, None, "100"

# 保存当天的最高温度
def save_max_temp(key, max_temp):
    """保存城市当天的最高气温到文件"""
    try:
        # 读取现有的温度记录文件
        if not os.path.exists(TEMP_RECORD_FILE):
            temperature_record = {}
        else:
            with open(TEMP_RECORD_FILE, "r", encoding="utf-8") as f:  # 指定UTF-8编码
                temperature_record = json.load(f)

        # 保存最高温度
        city_name = CITIES[key]["city_name"]
        temperature_record[city_name] = {"max_temp": max_temp, "date": datetime.now().strftime('%Y-%m-%d')}

        # 将记录保存到文件
        with open(TEMP_RECORD_FILE, "w", encoding="utf-8") as f:  # 指定UTF-8编码
            json.dump(temperature_record, f, ensure_ascii=False, indent=4)

    except Exception as e:
        print(f"保存温度失败: {e}")

# 计算温度变化并生成消息
def calculate_temperature_change(key, today_max_temp):
    """计算今天与昨天的温度变化"""
    try:
        # 读取温度记录文件
        if os.path.exists(TEMP_RECORD_FILE):
            with open(TEMP_RECORD_FILE, "r", encoding="utf-8") as f:  # 使用UTF-8编码读取
                temperature_record = json.load(f)

            city_name = CITIES[key]["city_name"]
            if city_name in temperature_record:
                # 获取该城市的记录
                city_record = temperature_record[city_name]
                yesterday_max_temp = city_record.get("max_temp")
                record_date = city_record.get("date")

                # 获取昨天的日期
                yesterday_date = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')

                # 只有当记录的日期是昨天时才进行温度变化计算
                if record_date == yesterday_date and yesterday_max_temp is not None:
                    temp_change = int(today_max_temp) - int(yesterday_max_temp)
                    if temp_change > 0:
                        return f"今天比昨天暖了 {temp_change}°C"
                    elif temp_change < 0:
                        return f"今天比昨天冷了 {-temp_change}°C"
                    else:
                        return "今天和昨天气温相同"
    except Exception as e:
        print(f"读取温度记录失败: {e}")

    return "


# 发送Bark通知
def send_bark_notification():
    """发送Bark天气通知，展示温度变化"""
    for key in BARK_KEYS:
        city_data = CITIES[key]  # 获取城市的名称和ID
        city_name = city_data["city_name"]
        city_id = city_data["city_id"]
        weather_text, min_temp, max_temp, weather_icon = get_weather(city_id)  # 获取天气信息
        local_icon_url = f"https://a.hecdn.net/img/common/icon/202106d/{weather_icon}.png"

        # 计算温度变化
        temp_change_message = calculate_temperature_change(key, max_temp)

        # 保存今天的最高温度
        save_max_temp(key, max_temp)

        # 拼接消息
        message = f"{min_temp}°C ~ {max_temp}°C. {temp_change_message}"

        location_weather = f"https://www.qweather.com/weather/{''.join(lazy_pinyin(city_name))}-{city_id}.html"
        bark_url = f"https://api.day.app/{key}/{city_name} {weather_text}/{message}?icon={local_icon_url}&isArchive=1&url={location_weather}"
        try:
            response = requests.get(bark_url)
            response.raise_for_status()  # 确保请求成功
            print(f"发送天气通知: {city_name} {message}")
        except requests.exceptions.RequestException as e:
            print(f"发送通知失败: {e}")

# 定时任务，定时发送天气通知
def run_weather_scheduler():
    """每天定时发送天气通知"""
    schedule.every().day.at("06:00").do(send_bark_notification)
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次任务

if __name__ == "__main__":
    # 启动定时任务
    # run_weather_scheduler()

    send_bark_notification()  # 立刻发送天气通知（可选择使用）
