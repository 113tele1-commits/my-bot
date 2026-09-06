import asyncio
import json
import os
import time
import urllib.parse
import aiohttp
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

# ==============================================================================
# 1. CẤU HÌNH BOT, ADMIN, NGÂN HÀNG & API BOSSOTP.NET V4
# ==============================================================================
BOT_TOKEN = "8944424200:AAG08My8yPruCLNVmjeh27XXuhyEoHftH7E"
ADMIN_TELEGRAM_ID = 7659943604
ADMIN_USERNAME = "ZALOVIET84"

BANK_BIN = "VIB"
BANK_STK = "095541820"
BANK_OWNER = "ĐẶNG TÚ ANH"

OTP_BASE_URL = "https://bossotp.net/api/v4"
OTP_API_KEY = "sk_7u9hm9klUGoSy1hneMO4P7l05hiPrMxB"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DB_FILE = "database_bot2.json"
HISTORY_FILE = "history_bot.json"
RENTS_FILE = "active_rents.json"

user_balances = {}
user_history = {}
active_rents = {}

def load_database():
    global user_balances, user_history, active_rents
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                user_balances = {int(k): v for k, v in data.items()}
        except Exception:
            user_balances = {}
    else:
        user_balances = {}

    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                user_history = {int(k): v for k, v in data.items()}
        except Exception:
            user_history = {}
    else:
        user_history = {}

    if os.path.exists(RENTS_FILE):
        try:
            with open(RENTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                active_rents = data
        except Exception:
            active_rents = {}
    else:
        active_rents = {}

def save_database():
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(user_balances, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Lỗi lưu database: {e}")

def save_history():
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(user_history, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Lỗi lưu history: {e}")

def save_active_rents():
    try:
        with open(RENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(active_rents, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Lỗi lưu active_rents: {e}")

load_database()

def get_user_balance(user_id: int) -> int:
    if user_id not in user_balances:
        user_balances[user_id] = 0
        save_database()
    return user_balances.get(user_id, 0)

def set_user_balance(user_id: int, amount: int):
    user_balances[user_id] = amount
    save_database()

def add_user_history(user_id: int, service_name: str, phone: str, price: int, result_text: str):
    if user_id not in user_history:
        user_history[user_id] = []
    
    time_str = time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())
    user_history[user_id].append({
        "time": time_str,
        "service": service_name,
        "phone": phone,
        "price": price,
        "result": result_text
    })
    save_history()

class RentStates(StatesGroup):
    waiting_for_amount = State()

def calculate_selling_price(service_name: str, original_price: int) -> int:
    name_lower = service_name.lower()
    if "zalo" in name_lower or "telegram" in name_lower or "tele" in name_lower:
        return original_price + 10000
    else:
        return original_price + 3000

def categorize_service(name: str) -> str:
    n = name.lower()
    if "zalo" in n:
        return "zalo"
    elif "tele" in n or "telegram" in n:
        return "telegram"
    
    shop_keywords = ["shopee", "lazada", "chotot", "chợ tốt", "tiki", "sendo", "tiktokshop", "shop", "shopping", "amazon", "ebay", "taobao", "1688", "temu", "shein", "alibaba"]
    if any(k in n for k in shop_keywords):
        return "shop"
        
    game_keywords = ["game", "play", "steam", "garena", "pubg", "freefire", "ff", "roblox", "liên quân", "lienquan"]
    if any(k in n for k in game_keywords):
        return "game"
        
    social_keywords = ["tiktok", "facebook", "fb", "instagram", "ig", "threads", "twitter", "x", "lotus", "louchat", "wechat", "whatsapp", "wahat", "mmlive", "viber"]
    if any(k in n for k in social_keywords):
        return "social"
    else:
        return "others"

def get_display_name(name: str) -> str:
    name_lower = name.lower()
    if "zalo" in name_lower and ("doi" in name_lower or "sdt" in name_lower or "6020" in name_lower):
        return "Zalo Đổi Số Điện Thoại"
    elif "zalo" in name_lower and ("5k" in name_lower or "tao" in name_lower or "dk" in name_lower):
        return "Tạo Tài Khoản Zalo"
    return name

def main_reply_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="📱 Thuê Số")
    builder.button(text="💳 Nạp Tiền")
    builder.button(text="💰 Số Dư")
    builder.button(text="🛠 CSKH")
    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True)

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    if user_id not in user_balances:
        user_balances[user_id] = 0
        save_database()

    caption = (
        f"🤖 **HỆ THỐNG THUÊ SIM NHẬN MÃ OTP TỰ ĐỘNG**\n\n"
        f"🌟 *Dịch vụ uy tín, tốc độ cao, hoạt động ổn định 24/7.*\n"
        f"📌 **Hướng dẫn nhanh:**\n"
        f"1️⃣ Bấm **Nạp Tiền** để quét mã QR thanh toán.\n"
        f"2️⃣ Bấm **Thuê Số** và chọn dịch vụ cần nhận OTP.\n"
        f"3️⃣ Bấm nút gửi cú pháp tương ứng."
    )
    await message.answer(caption, parse_mode="Markdown", reply_markup=main_reply_keyboard())

@dp.message(Command("info"))
async def admin_get_user_info(message: types.Message):
    if message.from_user.id != ADMIN_TELEGRAM_ID:
        await message.answer("❌ Bạn không có quyền sử dụng lệnh này!")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ Sai cú pháp! Mẫu chuẩn: `/info [ID_khách]`", parse_mode="Markdown")
        return
    
    try:
        target_id = int(parts[1])
    except ValueError:
        await message.answer("❌ ID khách hàng phải là số nguyên!")
        return
    
    balance = get_user_balance(target_id)
    
    try:
        chat = await bot.get_chat(target_id)
        name = chat.full_name
        username = f"@{chat.username}" if chat.username else "Không có"
    except Exception:
        name = "Không xác định (Chưa tương tác trực tiếp)"
        username = "Không có"
    
    text = (
        f"👤 **THÔNG TIN TÀI KHOẢN TELEGRAM:**\n\n"
        f"🆔 ID: `{target_id}`\n"
        f"📛 Tên: {name}\n"
        f"🔗 Username: {username}\n"
        f"💰 Số dư trong bot: **{balance:,}đ**"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("check"))
async def admin_check_all_users(message: types.Message):
    if message.from_user.id != ADMIN_TELEGRAM_ID:
        await message.answer("❌ Bạn không có quyền dùng lệnh này!")
        return
    
    if not user_balances:
        await message.answer("📂 Database hiện đang trống, chưa có khách nào lưu số dư.")
        return
    
    text = "📋 **DANH SÁCH SỐ DƯ KHÁCH HÀNG TRONG BOT:**\n\n"
    for uid, bal in user_balances.items():
        text += f"👤 ID: `{uid}` — Số dư: **{bal:,}đ**\n"
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("lichsu"))
async def admin_view_user_history(message: types.Message):
    if message.from_user.id != ADMIN_TELEGRAM_ID:
        await message.answer("❌ Bạn không có quyền sử dụng lệnh này!")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ Sai cú pháp! Mẫu chuẩn: `/lichsu [ID_khách]`", parse_mode="Markdown")
        return
    
    try:
        target_id = int(parts[1])
    except ValueError:
        await message.answer("❌ ID khách hàng phải là số nguyên!")
        return
    
    if target_id not in user_history or not user_history[target_id]:
        await message.answer(f"📂 Khách hàng `ID: {target_id}` chưa có lịch sử mua dịch vụ nào.", parse_mode="Markdown")
        return
    
    history_list = user_history[target_id]
    text = f"📜 **LỊCH SỬ GIAO DỊCH CỦA KHÁCH `ID: {target_id}`:**\n\n"
    for idx, item in enumerate(history_list[-15:], 1):
        text += f"🔹 #{idx} - {item['time']}\n📱 {item['service']} | 📞 `{item['phone']}` | Giá: `{item['price']:,}đ`\n💬 Kết quả: {item['result']}\n--------------------\n"
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("cong"))
async def admin_add_balance_manual(message: types.Message):
    if message.from_user.id != ADMIN_TELEGRAM_ID:
        await message.answer("❌ Không có quyền!")
        return
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("❌ Sai cú pháp! Dùng: `/cong [ID] [Số_tiền]`")
        return
    try:
        target_id, amount = int(parts[1]), int(parts[2].replace(".", "").replace(",", ""))
    except ValueError:
        await message.answer("❌ Sai định dạng số!")
        return
    new_bal = get_user_balance(target_id) + amount
    set_user_balance(target_id, new_bal)
    await message.answer(f"✅ Đã cộng {amount:,}đ cho `ID: {target_id}`. Số dư mới: **{new_bal:,}đ**")
    try:
        await bot.send_message(target_id, f"🎉 Bạn được Admin cộng **{amount:,}đ**. Số dư mới: **{new_bal:,}đ**")
    except:
        pass

@dp.message(Command("tru"))
async def admin_sub_balance_manual(message: types.Message):
    if message.from_user.id != ADMIN_TELEGRAM_ID:
        await message.answer("❌ Không có quyền!")
        return
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("❌ Sai cú pháp! Dùng: `/tru [ID] [Số_tiền]`")
        return
    try:
        target_id, amount = int(parts[1]), int(parts[2].replace(".", "").replace(",", ""))
    except ValueError:
        await message.answer("❌ Sai định dạng số!")
        return
    new_bal = max(0, get_user_balance(target_id) - amount)
    set_user_balance(target_id, new_bal)
    await message.answer(f"✅ Đã trừ {amount:,}đ của `ID: {target_id}`. Số dư mới: **{new_bal:,}đ**")
    try:
        await bot.send_message(target_id, f"⚠️ Bạn bị Admin trừ **{amount:,}đ**. Số dư mới: **{new_bal:,}đ**")
    except:
        pass

@dp.message(F.text.startswith("📱 Thuê Số"))
async def menu_rent_otp(message: types.Message, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="📱 Zalo", callback_data="group_zalo"),
        types.InlineKeyboardButton(text="✈️ Telegram", callback_data="group_telegram")
    )
    builder.row(
        types.InlineKeyboardButton(text="🌐 Mạng Xã Hội Khác", callback_data="group_social"),
        types.InlineKeyboardButton(text="🎮 OTP Game", callback_data="group_game")
    )
    builder.row(
        types.InlineKeyboardButton(text="🛒 OTP Sàn Mua Sắm", callback_data="group_shop"),
        types.InlineKeyboardButton(text="📁 DV Khác", callback_data="group_others")
    )
    await message.answer("📂 **CHỌN DANH MỤC DỊCH VỤ NHẬN OTP**", parse_mode="Markdown", reply_markup=builder.as_markup())

@dp.message(F.text.startswith("💳 Nạp Tiền"))
async def menu_deposit(message: types.Message, state: FSMContext):
    await state.set_state(RentStates.waiting_for_amount)
    await message.answer("💳 **NẠP TIỀN TỰ ĐỘNG QUA MÃ QR**\n\nVui lòng nhập số tiền muốn nạp (Ví dụ: `50000`):", parse_mode="Markdown")

@dp.message(F.text.startswith("💰 Số Dư"))
async def menu_balance(message: types.Message):
    balance = get_user_balance(message.from_user.id)
    await message.answer(f"💰 Số dư tài khoản thực tế của bạn: **{balance:,} VNĐ**", parse_mode="Markdown", reply_markup=main_reply_keyboard())

@dp.message(F.text.startswith("🛠 CSKH"))
async def menu_cskh(message: types.Message):
    await message.answer(f"🛠 Hỗ trợ khách hàng: Liên hệ Admin **@{ADMIN_USERNAME}**", parse_mode="Markdown", reply_markup=main_reply_keyboard())

@dp.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer("🤖 **HỆ THỐNG THUÊ SIM NHẬN MÃ OTP TỰ ĐỘNG**", parse_mode="Markdown", reply_markup=main_reply_keyboard())

@dp.callback_query(F.data.startswith("group_"))
async def handle_service_groups(callback: types.CallbackQuery):
    target_group = callback.data.split("_")[1]
    await callback.answer("⏳ Đang tải danh sách dịch vụ từ API v4...", show_alert=False)

    url = f"{OTP_BASE_URL}/service-manager/services"
    services_list = []
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    res_json = await response.json()
                    if isinstance(res_json, list):
                        services_list = res_json
        except Exception as e:
            print(f"Lỗi gọi API services: {e}")

    builder = InlineKeyboardBuilder()
    count = 0

    if services_list:
        for s in services_list:
            name = s.get("name", "Dịch vụ")
            s_id = s.get("_id")
            orig_price = s.get("price", 3000)
            group = categorize_service(name)
             
            if group == target_group:
                selling_price = calculate_selling_price(name, orig_price)
                display_name = get_display_name(name)

                builder.row(types.InlineKeyboardButton(
                    text=f"{display_name} ({selling_price:,}đ)", 
                    callback_data=f"buysim_{s_id}_{selling_price}"
                ))
                count += 1

    if count == 0:
        builder.row(types.InlineKeyboardButton(text="⚠️ Mục này hiện chưa có dịch vụ nào", callback_data="back_to_main"))

    builder.row(types.InlineKeyboardButton(text="◀️ Quay lại", callback_data="back_to_main"))
    msg = f"📋 **DANH SÁCH DỊCH VỤ ({target_group.upper()})**\n\nBấm chọn dịch vụ tương ứng bên dưới:"
    try:
        await callback.message.edit_text(msg, parse_mode="Markdown", reply_markup=builder.as_markup())
    except Exception:
        await callback.message.answer(msg, parse_mode="Markdown", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("buysim_"))
async def handle_buy_sim(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    service_id = parts[1]
    price = int(parts[2])

    user_id = callback.from_user.id
    balance = get_user_balance(user_id)
    
    if balance < price:
        await callback.answer(f"❌ Số dư không đủ! Cần ít nhất {price:,}đ.", show_alert=True)
        return

    await callback.answer("⏳ Đang kết nối lấy số...", show_alert=False)
    await asyncio.sleep(1)

    service_name = "Dịch vụ OTP"
    url_services = f"{OTP_BASE_URL}/service-manager/services"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url_services, timeout=5) as resp:
                if resp.status == 200:
                    lst = await resp.json()
                    for item in lst:
                        if item.get("_id") == service_id:
                            service_name = get_display_name(item.get("name", "Dịch vụ"))
                            break
        except:
            pass

    buy_url = f"{OTP_BASE_URL}/rents/create?service_id={service_id}&api_token={OTP_API_KEY}&language=vn"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(buy_url, timeout=10) as response:
                res_text = await response.text()
                try:
                    res_data = json.loads(res_text)
                except:
                    res_data = {}

                if response.status == 200 and "number" in res_data:
                    phone = res_data.get("number")
                    rent_id = str(res_data.get("rent_id"))
                    
                    new_balance = balance - price
                    set_user_balance(user_id, new_balance)

                    active_rents[rent_id] = {
                        "user_id": user_id, 
                        "price": price, 
                        "phone": phone, 
                        "service_name": service_name,
                        "time": time.time()
                    }
                    save_active_rents()

                    builder = InlineKeyboardBuilder()
                    
                    # Cấu hình riêng cho Zalo Đổi Số Điện Thoại gồm đúng 3 ô nút bấm
                    if "Đổi Số Điện Thoại" in service_name:
                        builder.row(
                            types.InlineKeyboardButton(text="📤 Zalo gửi 6020", callback_data=f"sendsms_{rent_id}_6020_zalo"),
                            types.InlineKeyboardButton(text="📤 Zalo gửi 8066", callback_data=f"sendsms_{rent_id}_8066_zalo")
                        )
                        builder.row(
                            types.InlineKeyboardButton(text="📤 Zalo doi sdt gửi 6020", callback_data=f"sendsms_{rent_id}_6020_zalo doi sdt")
                        )
                    else:
                        # Các dịch vụ khác dùng 2 nút zalo mặc định
                        builder.row(
                            types.InlineKeyboardButton(text="📤 zalo gửi 8500", callback_data=f"sendsms_{rent_id}_8500_zalo"),
                            types.InlineKeyboardButton(text="📤 zalo gửi 7539", callback_data=f"sendsms_{rent_id}_7539_zalo")
                        )

                    msg = (
                        f"📱 **Số của bạn:** `{phone}`\n"
                        f"💵 **Giá thuê:** `{price:,}đ`\n\n"
                        f"👉 *Bấm chọn 1 trong các nút cú pháp bên dưới để gửi tin nhắn.*\n"
                        f"⏳ *Đang tự động chờ mã OTP...*"
                    )
                    try:
                        await callback.message.answer(msg, parse_mode="Markdown", reply_markup=builder.as_markup())
                    except Exception:
                        pass
                    return
                else:
                    err_code = res_data.get("code") or res_data.get("error") or ""
                    if "NO_NUMBER_AVAILABLE" in str(err_code):
                        await callback.message.answer(f"❌ Dịch vụ này tạm hết số!", parse_mode="Markdown")
                    else:
                        await callback.message.answer(f"❌ Không thể thuê số: `{err_code}`", parse_mode="Markdown")
        except Exception as e:
            await callback.message.answer(f"❌ Lỗi kết nối API: `{e}`", parse_mode="Markdown")

@dp.callback_query(F.data.startswith("sendsms_"))
async def callback_send_sms_preset(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    rent_id = parts[1]
    target_num = parts[2]  # Số tổng đài (ví dụ: 6020 hoặc 8066)
    content = parts[3]    # Nội dung (ví dụ: zalo hoặc zalo doi sdt)

    if rent_id not in active_rents:
        await callback.answer("❌ Phiên thuê không tồn tại hoặc đã kết thúc!", show_alert=True)
        return

    send_url = f"{OTP_BASE_URL}/rents/send-sms?_id={rent_id}&api_token={OTP_API_KEY}&number_receiver={target_num}&sms={urllib.parse.quote(content)}"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(send_url, timeout=10) as response:
                res_text = await response.text()
                if response.status == 200:
                    await callback.answer(f"✅ Gửi thành công!", show_alert=True)
                    try:
                        await callback.message.edit_text(callback.message.text + f"\n\n✅ **Đã gửi:** `{content} gửi {target_num}`", parse_mode="Markdown")
                    except:
                        pass
                else:
                    await callback.answer(f"❌ Gửi thất bại!", show_alert=True)
                    await callback.message.answer(f"❌ Phản hồi từ hệ thống: `{res_text}`", parse_mode="Markdown")
        except Exception as e:
            await callback.answer(f"❌ Lỗi kết nối!", show_alert=True)
            await callback.message.answer(f"❌ Lỗi: `{e}`", parse_mode="Markdown")

async def check_otp_worker():
    while True:
        await asyncio.sleep(3)
        if not active_rents:
            continue
            
        current_time = time.time()
        rents_to_remove = []
        
        async with aiohttp.ClientSession() as session:
            for rent_id, info in list(active_rents.items()):
                start_time = info["time"]
                user_id = info["user_id"]
                phone = info["phone"]
                price = info["price"]
                service_name = info["service_name"]

                if current_time - start_time > 600:
                    try:
                        async with session.get(f"{OTP_BASE_URL}/rents/cancel?_id={rent_id}&api_token={OTP_API_KEY}", timeout=5) as r:
                            pass
                    except:
                        pass

                    new_bal = get_user_balance(user_id) + price
                    set_user_balance(user_id, new_bal)
                    add_user_history(user_id, service_name, phone, price, "Hết hạn 10 phút - Đã hoàn tiền")
                    try:
                        await bot.send_message(user_id, f"⏰ Hết hạn 10 phút cho số `{phone}`. Đã hoàn lại `{price:,}đ`. Số dư: `{new_bal:,}đ`", parse_mode="Markdown")
                    except:
                        pass
                    rents_to_remove.append(rent_id)
                    continue

                try:
                    async with session.get(f"{OTP_BASE_URL}/rents/check?_id={rent_id}&api_token={OTP_API_KEY}", timeout=5) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            status = data.get("status")
                            sms = data.get("sms_content", "") or data.get("message", "") or ""
                            
                            if status == "SUCCESS" or data.get("otp"):
                                otp = data.get("otp", "")
                                add_user_history(user_id, service_name, phone, price, f"Thành công - OTP: {otp}")
                                try:
                                    await bot.send_message(user_id, f"🎉 **ĐÃ CÓ KẾT QUẢ CHO SỐ `{phone}`!**\n🔑 OTP: `{otp}`\n💬 Nội dung: `{sms}`", parse_mode="Markdown")
                                except:
                                    pass
                                rents_to_remove.append(rent_id)
                except Exception as e:
                    print(f"Lỗi check OTP: {e}")
                await asyncio.sleep(1.5)

        for rid in rents_to_remove:
            if rid in active_rents:
                del active_rents[rid]
                save_active_rents()

@dp.message(RentStates.waiting_for_amount)
async def process_deposit_amount(message: types.Message, state: FSMContext):
    text_val = message.text.replace(".", "").replace(",", "").replace("đ", "").strip()
    if not text_val.isdigit():
        await message.answer("❌ Vui lòng chỉ nhập số tiền hợp lệ:")
        return
     
    amount = int(text_val)
    user_id = message.from_user.id
    await state.clear()

    content = f"NAP {user_id}"
    qr_url = f"https://img.vietqr.io/image/{BANK_BIN}-{BANK_STK}-compact2.png?amount={amount}&addInfo={content}&accountName={urllib.parse.quote(BANK_OWNER)}"

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✅ Tôi Đã Chuyển Khoản Xong", callback_data=f"user_paid_done_{amount}"))

    caption = f"📌 **QUÉT MÃ QR NẠP TIỀN**\n\n💵 Số tiền: `{amount:,}đ`\n📝 Nội dung: `{content}`"
    try:
        await message.answer_photo(photo=qr_url, caption=caption, parse_mode="Markdown", reply_markup=builder.as_markup())
    except Exception as e:
        await message.answer(f"❌ Lỗi tạo QR: {e}")

@dp.callback_query(F.data.startswith("user_paid_done_"))
async def handle_user_paid_done(callback: types.CallbackQuery):
    amount = int(callback.data.split("_")[3])
    user = callback.from_user
    await callback.answer("✅ Đã gửi yêu cầu!", show_alert=True)
    try:
        await callback.message.delete()
        await callback.message.answer(f"✅ Đã gửi yêu cầu nạp `{amount:,}đ`. Chờ Admin duyệt.")
    except:
        pass

    admin_builder = InlineKeyboardBuilder()
    admin_builder.row(
        types.InlineKeyboardButton(text=f"🟢 Cộng {amount:,}đ", callback_data=f"admin_add_{user.id}_{amount}"),
        types.InlineKeyboardButton(text=f"🔴 Từ chối", callback_data=f"admin_sub_{user.id}_{amount}")
    )
    try:
        await bot.send_message(ADMIN_TELEGRAM_ID, f"🔔 Nạp tiền từ `{user.full_name}` (`{user.id}`): **{amount:,}đ**", parse_mode="Markdown", reply_markup=admin_builder.as_markup())
    except:
        pass

@dp.callback_query(F.data.startswith("admin_add_") | F.data.startswith("admin_sub_"))
async def handle_admin_balance_actions(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_TELEGRAM_ID:
        await callback.answer("❌ Không có quyền!", show_alert=True)
        return

    parts = callback.data.split("_")
    action, target_user_id, amount = parts[1], int(parts[2]), int(parts[3])
    current_bal = get_user_balance(target_user_id)

    if action == "add":
        new_bal = current_bal + amount
        set_user_balance(target_user_id, new_bal)
        await callback.answer(f"✅ Đã cộng {amount:,}đ!", show_alert=True)
        try:
            await callback.message.edit_text(callback.message.text + f"\n\n🟢 ĐÃ DUYỆT CỘNG {amount:,}đ", reply_markup=None)
            await bot.send_message(target_user_id, f"🎉 Nạp tiền thành công +{amount:,}đ. Số dư mới: {new_bal:,}đ", reply_markup=main_reply_keyboard())
        except:
            pass
    elif action == "sub":
        await callback.answer("❌ Đã từ chối!", show_alert=True)
        try:
            await callback.message.edit_text(callback.message.text + f"\n\n🔴 ĐÃ TỪ CHỐI", reply_markup=None)
            await bot.send_message(target_user_id, f"⚠️ Yêu cầu nạp {amount:,}đ đã bị từ chối.")
        except:
            pass

async def main():
    print("---------------------------------------------------")
    print("🤖 Bot đã được cập nhật giá mới (Zalo/Tele +10k, Khác +3k)!")
    print("---------------------------------------------------")
    asyncio.create_task(check_otp_worker())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())