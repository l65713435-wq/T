import requests
import time
import random
import re

ROOM_ID = "405432031"
API_TOKEN = "a67648f5ed3aaca6f1492c081849f533"

OMIKUJI_TABLE = [
    ("大吉 🎉 とても良いことが起こりそう！", 1800),
    ("中吉 😊 良いことが期待できそう！", 2000),
    ("小吉 🙂 ちょっと良いことがあるかも。", 2000),
    ("吉 😌 平穏な一日になりそう。", 1800),
    ("末吉 😅 少し注意が必要かも。", 1500),
    ("凶 😨 気をつけて行動しましょう。", 700),
    ("大凶 😱 今日は慎重に…！", 150),
    ("超大吉 🌈 最高の運勢！何をやっても成功する1日！", 35),
    ("伝説の吉 🦄 幻の運勢を引き当てました…！", 10),
    ("バグ吉 🐛 何かバグが起きるかも？", 5)
]

def omikuji_draw():
    population = [item[0] for item in OMIKUJI_TABLE]
    weights = [item[1] for item in OMIKUJI_TABLE]
    return random.choices(population, weights=weights, k=1)[0]

def send_message(message):
    url = f"https://api.chatwork.com/v2/rooms/{ROOM_ID}/messages"
    headers = {"X-ChatWorkToken": API_TOKEN}
    payload = {"body": message}
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        print(f"[send_message] status:{response.status_code}, res:{response.text}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"send_message error: {e}")
        return {}

def get_room_members():
    url = f"https://api.chatwork.com/v2/rooms/{ROOM_ID}/members"
    headers = {"X-ChatWorkToken": API_TOKEN}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"[get_room_members] status:{response.status_code}, res:{response.text}")
        response.raise_for_status()
        members = response.json()
        if not isinstance(members, list):
            print("[get_room_members] メンバーリストがリストでない:", members)
            return []
        return members
    except Exception as e:
        print(f"get_room_members error: {e}")
        return []

def update_permission(account_id, role="reader"):
    url = f"https://api.chatwork.com/v2/rooms/{ROOM_ID}/members/{account_id}"
    headers = {
        "X-ChatWorkToken": API_TOKEN,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {"role": role}
    try:
        response = requests.put(url, headers=headers, data=payload, timeout=10)
        print(f"[update_permission] status:{response.status_code}, res:{response.text}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"update_permission error: {e}")
        return {}

def main():
    print("Chatwork Kill & Omikuji Bot is running...")

    checked_message_ids = set()
    kill_pattern = re.compile(r'^/kill\s+(.+)$')
    omikuji_pattern = re.compile(r'^/omikuji$')

    while True:
        url = f"https://api.chatwork.com/v2/rooms/{ROOM_ID}/messages?force=1"
        headers = {"X-ChatWorkToken": API_TOKEN}
        try:
            res = requests.get(url, headers=headers, timeout=10)
            print(f"[get_messages] status:{res.status_code}, res:{res.text[:300]}")
            res.raise_for_status()
            messages = res.json()
            if not isinstance(messages, list):
                print("[get_messages] メッセージがリストでない:", messages)
                time.sleep(5)
                continue
        except Exception as e:
            print(f"messages get error: {e}")
            time.sleep(5)
            continue

        for msg in reversed(messages):
            message_id = msg.get("message_id")
            if message_id in checked_message_ids:
                continue
            checked_message_ids.add(message_id)
            body = msg.get("body", "").strip()
            print(f"[message] id:{message_id}, body:'{body}'")

            # /killコマンド
            kill_match = kill_pattern.match(body)
            if kill_match:
                username = kill_match.group(1).strip()
                print(f"[kill] username: '{username}'")
                members = get_room_members()
                if not members:
                    send_message("メンバー一覧の取得に失敗しました。")
                    continue
                # 完全一致優先、なければ部分一致
                target_id = None
                username_lower = username.replace(" ", "").lower()
                for m in members:
                    name = m.get("name", "")
                    name_lower = name.replace(" ", "").lower()
                    if username_lower == name_lower:
                        target_id = m["account_id"]
                        break
                if not target_id:
                    for m in members:
                        name = m.get("name", "")
                        name_lower = name.replace(" ", "").lower()
                        if username_lower in name_lower:
                            target_id = m["account_id"]
                            break
                if not target_id:
                    send_message(f"ユーザー「{username}」が見つかりませんでした。")
                    continue

                result = update_permission(target_id, "reader")
                if isinstance(result, dict) and result.get("role") == "reader":
                    send_message(f"ユーザー「{username}」の権限を閲覧のみに変更しました。")
                else:
                    send_message(f"ユーザー「{username}」の権限変更に失敗しました。詳細: {result}")

            # /omikujiコマンド
            if omikuji_pattern.match(body):
                result = omikuji_draw()
                send_message(f"【おみくじの結果】\n{result}")

        time.sleep(5)

if __name__ == "__main__":
    main()