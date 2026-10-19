import requests
import json
import time

# Leave these blank as requested
BOT_TOKEN = "8743516934:AAF-mF_BVSwLuLpKdJqS90dUaL4AEdnQl4k"
EXTERNAL_API_URL = "https://sra-cybertech-pvt-ltd-api-gateway.duckdns.org/aadhar-info?key=SRA-642B561881DF6062&aadhar=845349590962"   # e.g. "http://127.0.0.1:8000/lookup"

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

# Simple in-memory state to know when we are waiting for a 12-digit number
waiting_for_number = {}


def get_updates(offset=None):
    url = BASE_URL + "getUpdates"
    params = {"timeout": 30}
    if offset is not None:
        params["offset"] = offset
    try:
        response = requests.get(url, params=params, timeout=35)
        return response.json()
    except Exception as e:
        print(f"Error in get_updates: {e}")
        return {"ok": False}


def send_message(chat_id, text, reply_markup=None, parse_mode=None):
    url = BASE_URL + "sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    if reply_markup is not None:
        payload["reply_markup"] = json.dumps(reply_markup)
    if parse_mode is not None:
        payload["parse_mode"] = parse_mode
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Error sending message: {e}")


def main():
    print("Bot started (long polling)...")
    offset = None

    while True:
        updates = get_updates(offset)

        if not updates.get("ok"):
            time.sleep(2)
            continue

        for update in updates.get("result", []):
            offset = update["update_id"] + 1

            if "message" not in update:
                continue

            message = update["message"]
            chat_id = message["chat"]["id"]
            text = message.get("text", "").strip()

            # /start command
            if text == "/start":
                waiting_for_number.pop(chat_id, None)
                keyboard = {
                    "keyboard": [[{"text": "🪪 aadhaar look up"}]],
                    "resize_keyboard": True,
                    "one_time_keyboard": False
                }
                welcome = (
                    "Welcome!\n\n"
                    "This is an educational Telegram bot example.\n"
                    "Press the button below to continue."
                )
                send_message(chat_id, welcome, reply_markup=keyboard)
                continue

            # Button pressed
            if text == "🪪 aadhaar look up":
                waiting_for_number[chat_id] = True
                send_message(chat_id, "🪪send 12 digit number:")
                continue

            # User is expected to send a 12-digit number
            if waiting_for_number.get(chat_id):
                if text.isdigit() and len(text) == 12:
                    # Call external API (dummy)
                    try:
                        if not EXTERNAL_API_URL:
                            send_message(chat_id, "EXTERNAL_API_URL is empty. Please set it first.")
                        else:
                            # Example GET request – change to POST if your API needs it
                            api_response = requests.get(
                                EXTERNAL_API_URL,
                                params={"number": text},
                                timeout=10
                            )
                            api_response.raise_for_status()
                            data = api_response.json()

                            # Pretty format inside <pre>
                            formatted = json.dumps(data, indent=2, ensure_ascii=False)
                            send_message(
                                chat_id,
                                f"<pre>{formatted}</pre>",
                                parse_mode="HTML"
                            )
                    except Exception as e:
                        send_message(chat_id, f"API error: {str(e)}")
                    finally:
                        waiting_for_number.pop(chat_id, None)
                else:
                    send_message(
                        chat_id,
                        "Invalid input.\nPlease send exactly 12 digits (0-9 only)."
                    )
                continue

        time.sleep(1)


if __name__ == "__main__":
    main()
