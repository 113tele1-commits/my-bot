import asyncio
import json
import os
import random
import string
import urllib.parse
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ==============================================================================
# 1. CẤU HÌNH BOT VÀ THÔNG TIN ADMIN & NGÂN HÀNG
# ==============================================================================
BOT_TOKEN = "8889542417:AAF3322hy3cJFLuq2YoX00O5j8dGQhDdlR4"

# ID Telegram của Admin
ADMIN_ID = 7659943604

# Username Telegram của Admin (không chứa dấu @)
ADMIN_USERNAME = "ZALOVIET84"

BANK_INFO = {
    "bank_id": "VIB",
    "account_no": "095541820",
    "account_name": "ĐẶNG TÚ ANH"
}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# File lưu dữ liệu số dư của khách hàng
DB_FILE = "database.json"

def load_data():
    """Đọc dữ liệu số dư từ file JSON"""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {int(k): v for k, v in data.items()}
        except Exception:
            return {}
    return {}

def save_data():
    """Ghi dữ liệu số dư hiện tại ra file JSON"""
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(user_balances, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Lỗi lưu database: {e}")

# Biến lưu trữ số dư (Được load sẵn từ file)
user_balances = load_data()

# Định nghĩa trạng thái FSM để nhập số tiền nạp
class DepositState(StatesGroup):
    waiting_for_amount = State()

def generate_order_id():
    return "OD-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# ==============================================================================
# 2. CẤU TRÚC BẢNG GIÁ SẢN PHẨM
# ==============================================================================
PRODUCT_CATEGORIES = {
    "p1": {
        "name": "📱 Mua Zalo Đã Định Danh",
        "description": "Bảng giá danh sách tài khoản **Zalo Đã Xác Thực / Định Danh**:",
        "items": [
            {"id": "p1_1", "btn_name": "Gói 1: Zalo Đã Xác Thực", "detail_name": "Zalo Đã Xác Thực (BH khóa 24h + Proxy)", "price": 550000},
            {"id": "p1_2", "btn_name": "Gói 2: Zalo 6T ➡️ 11T", "detail_name": "Zalo 6T ➡️ 11T Đã Xác Thực (BH 24h + Proxy)", "price": 780000},
            {"id": "p1_3", "btn_name": "Gói 3: Zalo Dùng Ngay", "detail_name": "Zalo Dùng Ngay Không Ngâm (BH 48h + Proxy)", "price": 860000},
            {"id": "p1_4", "btn_name": "Gói 4: Zalo 1T ➡️ 10 Năm", "detail_name": "Zalo 1T ➡️ 10 Năm Đã Xác Thực (BH 48h + Proxy)", "price": 960000},
            {"id": "p1_5", "btn_name": "Gói 5: Zalo 1T-10N + Bài Đăng", "detail_name": "Zalo 1T ➡️ 10 Năm + Bài Đăng (Hàng Đặt Trước)", "price": 1100000},
            {"id": "p1_6", "btn_name": "Gói 6: Zalo Ko Báo Xấu", "detail_name": "Zalo Không Bao Giờ Báo Xấu (+ Proxy) Bảo Hành 72h", "price": 1500000},
        ]
    },
    "p_zalo_bh": {
        "name": "✅ Gói Zalo Bảo Hành 1 Tháng",
        "description": "🛡 **Chính sách bảo hành:** Trong vòng 1 tháng cứ bay hoặc lỗi là đổi\n💬 **Hỗ trợ:** 24/24\n\nBảng giá chi tiết:",
        "items": [
            {"id": "pz_1", "btn_name": "Zalo tuần (115 USDT)", "detail_name": "Gói Zalo tuần (115 USDT - BH 1 Tháng, 24/24)", "price": 2990000},
            {"id": "pz_2", "btn_name": "Zalo tháng (153 USDT)", "detail_name": "Gói Zalo tháng (153 USDT - BH 1 Tháng, 24/24)", "price": 3978000},
            {"id": "pz_3", "btn_name": "Zalo năm (230 USDT)", "detail_name": "Gói Zalo năm (230 USDT - BH 1 Tháng, 24/24)", "price": 5980000},
        ]
    },
    "p2": {
        "name": "📘 Mua Fb Nhiều Bài Viết bb",
        "description": "Bảng giá danh sách tài khoản **Facebook Nhiều Bài Viết / Bạn Bè**:\n\n🔗 **Link xem mẫu:**\n• Gói 2: https://www.facebook.com/profile.php?id=61585342655320\n• Gói 3: https://www.facebook.com/profile.php?id=61578721646127\n• Gói 4: https://www.facebook.com/profile.php?id=61584137975348\n• Gói 5: https://www.facebook.com/profile.php?id=61552506553219\n• FB Cổ Tích Xanh: https://t.me/HongAnVN/15",
        "items": [
            {"id": "p2_1", "btn_name": "Gói 1: FB Clone Trắng", "detail_name": "FB Clone Trắng", "price": 50000},
            {"id": "p2_2", "btn_name": "Gói 2: FB 1-200 BB (15-20 BV)", "detail_name": "FB 1-200 BB | 15-20 BV (Có Link Mẫu)", "price": 150000},
            {"id": "p2_3", "btn_name": "Gói 3: FB Acc Việt (15-25 BV)", "detail_name": "FB Acc Việt | 15-25 BV (Có Link Mẫu)", "price": 200000},
            {"id": "p2_4", "btn_name": "Gói 4: FB Mẫu 15-50 BV", "detail_name": "FB Mẫu 15-50 BV (Có Link Mẫu)", "price": 450000},
            {"id": "p2_5", "btn_name": "Gói 5: FB Trên 1k-2k BB", "detail_name": "FB Trên 1k-2k Bạn Bè (Có Link Mẫu)", "price": 450000},
            {"id": "p2_6", "btn_name": "Gói 6: FB Cổ Tích Xanh", "detail_name": "FB Cổ Lâu Năm Tích Xanh", "price": 2500000},
        ]
    },
    "p3": {
        "name": "🎵 Mua Tài Khoản Tiktok",
        "description": "Bảng giá danh sách **Tài Khoản Tiktok**:",
        "items": [
            {"id": "p3_1", "btn_name": "Gói 1: Tiktok Trắng", "detail_name": "Tiktok Trắng (Đã Khai Thần)", "price": 50000},
            {"id": "p3_2", "btn_name": "Gói 2: Tiktok 1k Follow (Live)", "detail_name": "Tiktok 1.000 Follower (Đã Bật Live)", "price": 400000},
            {"id": "p3_3", "btn_name": "Gói 3: Tiktok Shop / MCN", "detail_name": "Tiktok Shop / Bật MCN Chuẩn", "price": 600000},
        ]
    },
    "p4": {
        "name": "🏦 Mua Ngân Hàng Bank Ảo",
        "description": "✅ **HỒNG ÂN THỊNH VƯỢNG** ✅\nCUNG CẤP BANK - BÁN BANK SLL\n🏦 VPBANK - VIKKI - SEA - TPBANK - MYVIB - ACB - PGBANK - EXIM - MSB,...\n\n💠 **BẢO HÀNH, HỖ TRỢ SIM SỐ**\n💠 **NHẬN CHẠY FULL NGÂN HÀNG, BANK THEO TÊN, THEO Y/C**\n🛡 *Bảo Hành Trọn Đời đối với bank thật | Bao Back Lưu kí sim cho khách hàng*",
        "items": [
            {"id": "p4_1", "btn_name": "Gói 1: HD, Timo, Cake", "detail_name": "Bank Thật (HD bank, Timobank, Cake) [Bao Vượt Mặt]", "price": 1000000},
            {"id": "p4_2", "btn_name": "Gói 2: MB, TPB, VIB, VP, Nam Á", "detail_name": "Bank Thật (MB bank, TP bank, VIB, VP bank, Nam Á Bank) [Bao Vượt Mặt]", "price": 1500000},
            {"id": "p4_3", "btn_name": "Gói 3: Techcom, VCB, BIDV", "detail_name": "Bank Thật (Techcombank, VCB, BIDV) [Bao Vượt Mặt]", "price": 2000000},
            {"id": "p4_4", "btn_name": "Gói 4: Bank Ảo Theo Tên Lẻ", "detail_name": "Bank Ảo Theo Tên Bào Game (Lẻ 1tr/1)", "price": 1000000},
            {"id": "p4_5", "btn_name": "Gói 5: Bank Ảo Theo Tên SLL", "detail_name": "Bank Ảo Theo Tên SLL (Trên 5 Bank - 500k/1)", "price": 500000},
            {"id": "p4_6", "btn_name": "Gói 6: Full Bank + Crypto", "detail_name": "Full Bộ Bank + Crypto (Binance, Bybit, OKX)", "price": 3000000},
        ]
    },
    "p5": {
        "name": "✈️ Mua telegram",
        "description": "Bảng giá danh sách **Tài Khoản Telegram**:",
        "items": [
            {"id": "p5_1", "btn_name": "Gói 1: Telegram SLL (Combo 100 Acc)", "detail_name": "Telegram SLL (Combo 100 Acc)", "price": 2500000},
            {"id": "p5_2", "btn_name": "Gói 2: Telegram Thường", "detail_name": "Telegram Thường", "price": 40000},
            {"id": "p5_3", "btn_name": "Gói 3: Telegram BH 30 Ngày", "detail_name": "Telegram Bảo Hành 30 Ngày (Die Đổi Mới)", "price": 100000},
            {"id": "p5_4", "btn_name": "Gói 4: Telegram Premium 3 Tháng", "detail_name": "Telegram Nâng Cấp Premium 3 Tháng", "price": 500000},
        ]
    }
}

# ==============================================================================
# 3. LỆNH VÀ NÚT XỬ LÝ CỘNG / TRỪ TIỀN CHO ADMIN
# ==============================================================================
@dp.message(F.text.startswith("/cong") | F.caption.startswith("/cong"))
async def cmd_add_balance(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Bạn không có quyền sử dụng lệnh này!")
        return

    text_data = message.text or message.caption or ""
    try:
        args = text_data.split()
        target_user_id = int(args[1])
        amount = int(args[2])

        user_balances[target_user_id] = user_balances.get(target_user_id, 0) + amount
        save_data()
        current_bal = user_balances[target_user_id]

        await message.answer(
            f"✅ **ĐÃ CỘNG TIỀN THÀNH CÔNG!**\n\n"
            f"👤 User ID: `{target_user_id}`\n"
            f"💵 Số tiền cộng: +`{amount:,}đ`\n"
            f"💰 Số dư mới của khách: `{current_bal:,}đ`",
            parse_mode="Markdown"
        )

        try:
            await bot.send_message(
                chat_id=target_user_id,
                text=(
                    f"🎉 **NẠP TIỀN THÀNH CÔNG!**\n\n"
                    f"💵 Số tiền: +`{amount:,}đ`\n"
                    f"💰 Số dư hiện tại: `{current_bal:,}đ`\n\n"
                    f"✨ Cảm ơn bạn đã sử dụng dịch vụ!"
                ),
                parse_mode="Markdown"
            )
        except Exception:
            pass
    except Exception:
        await message.answer("❌ **Cú pháp sai!** Vui lòng dùng:\n`/cong <ID_KHACH> <SO_TIEN>`", parse_mode="Markdown")

@dp.message(F.text.startswith("/tru") | F.caption.startswith("/tru"))
async def cmd_sub_balance(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Bạn không có quyền sử dụng lệnh này!")
        return

    text_data = message.text or message.caption or ""
    try:
        args = text_data.split()
        target_user_id = int(args[1])
        amount = int(args[2])

        current_bal = user_balances.get(target_user_id, 0)
        new_bal = max(0, current_bal - amount)
        user_balances[target_user_id] = new_bal
        save_data()

        await message.answer(
            f"✅ **ĐÃ TRỪ TIỀN THÀNH CÔNG!**\n\n"
            f"👤 User ID: `{target_user_id}`\n"
            f"💵 Số tiền trừ: -`{amount:,}đ`\n"
            f"💰 Số dư mới của khách: `{new_bal:,}đ`",
            parse_mode="Markdown"
        )

        try:
            await bot.send_message(
                chat_id=target_user_id,
                text=(
                    f"⚠️ **THÔNG BÁO BIẾN ĐỘNG SỐ DƯ!**\n\n"
                    f"💵 Số dư của bạn đã bị trừ: -`{amount:,}đ`\n"
                    f"💰 Số dư hiện tại: `{new_bal:,}đ`\n\n"
                    f"✨ Liên hệ Admin nếu bạn có thắc mắc."
                ),
                parse_mode="Markdown"
            )
        except Exception:
            pass
    except Exception:
        await message.answer("❌ **Cú pháp sai!** Vui lòng dùng:\n`/tru <ID_KHACH> <SO_TIEN>`", parse_mode="Markdown")

# Xử lý khi Admin bấm nút Cộng tiền nhanh trên tin nhắn
@dp.callback_query(F.data.startswith("adm_cong_"))
async def admin_inline_cong(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Bạn không có quyền!", show_alert=True)
        return

    parts = callback.data.split("_")
    target_user_id = int(parts[2])
    amount = int(parts[3])

    user_balances[target_user_id] = user_balances.get(target_user_id, 0) + amount
    save_data()
    current_bal = user_balances[target_user_id]

    await callback.answer(f"✅ Đã cộng thành công {amount:,}đ cho khách!", show_alert=True)

    # Cập nhật lại tin nhắn thông báo của admin cho gọn
    new_text = callback.message.text + f"\n\n🟢 **ĐÃ XỬ LÝ:** Đã cộng thành công `{amount:,}đ` (Số dư mới: `{current_bal:,}đ`)"
    try:
        await callback.message.edit_text(new_text, parse_mode="Markdown", reply_markup=None)
    except Exception:
        pass

    # Gửi tin báo về cho khách
    try:
        await bot.send_message(
            chat_id=target_user_id,
            text=(
                f"🎉 **NẠP TIỀN THÀNH CÔNG!**\n\n"
                f"💵 Số tiền: +`{amount:,}đ`\n"
                f"💰 Số dư hiện tại: `{current_bal:,}đ`\n\n"
                f"✨ Cảm ơn bạn đã sử dụng dịch vụ!"
            ),
            parse_mode="Markdown"
        )
    except Exception:
        pass

# Xử lý khi Admin bấm nút Trừ tiền nhanh trên tin nhắn
@dp.callback_query(F.data.startswith("adm_tru_"))
async def admin_inline_tru(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Bạn không có quyền!", show_alert=True)
        return

    parts = callback.data.split("_")
    target_user_id = int(parts[2])
    amount = int(parts[3])

    current_bal = user_balances.get(target_user_id, 0)
    new_bal = max(0, current_bal - amount)
    user_balances[target_user_id] = new_bal
    save_data()

    await callback.answer(f"✅ Đã trừ {amount:,}đ của khách!", show_alert=True)

    new_text = callback.message.text + f"\n\n🔴 **ĐÃ XỬ LÝ:** Đã trừ `{amount:,}đ` (Số dư mới: `{new_bal:,}đ`)"
    try:
        await callback.message.edit_text(new_text, parse_mode="Markdown", reply_markup=None)
    except Exception:
        pass

    try:
        await bot.send_message(
            chat_id=target_user_id,
            text=(
                f"⚠️ **THÔNG BÁO BIẾN ĐỘNG SỐ DƯ!**\n\n"
                f"💵 Số dư của bạn đã bị trừ: -`{amount:,}đ`\n"
                f"💰 Số dư hiện tại: `{new_bal:,}đ`\n\n"
                f"✨ Liên hệ Admin nếu bạn có thắc mắc."
            ),
            parse_mode="Markdown"
        )
    except Exception:
        pass

# ==============================================================================
# 4. KEYBOARD & MAIN HANDLERS
# ==============================================================================
def get_user_balance(user_id: int) -> int:
    return user_balances.get(user_id, 0)

def main_menu_keyboard(user_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="📱 Mua Zalo Đã Định Danh", callback_data="select_p1")
    builder.button(text="✅ Gói Zalo Bảo Hành 1 Tháng", callback_data="select_p_zalo_bh")
    builder.button(text="📘 Mua Fb Nhiều Bài Viết bb", callback_data="select_p2")
    builder.button(text="🎵 Mua Tài Khoản Tiktok", callback_data="select_p3")
    builder.button(text="🏦 Mua Ngân Hàng Bank Ảo", callback_data="select_p4")
    builder.button(text="✈️ Mua telegram", callback_data="select_p5")
    builder.adjust(1)
    
    balance = get_user_balance(user_id)
    builder.row(
        types.InlineKeyboardButton(text="💳 Nạp tiền", callback_data="deposit_direct"),
        types.InlineKeyboardButton(text=f"👤 Số dư: {balance:,}đ", callback_data="check_balance")
    )
    builder.row(
        types.InlineKeyboardButton(text="📜 Lịch sử mua hàng", callback_data="history"),
        types.InlineKeyboardButton(text="🛠 Hỗ trợ / CSKH", url=f"https://t.me/{ADMIN_USERNAME}")
    )
    return builder.as_markup()

def sub_items_keyboard(cat_key: str):
    builder = InlineKeyboardBuilder()
    cat_data = PRODUCT_CATEGORIES.get(cat_key)
    if cat_data:
        for item in cat_data["items"]:
            builder.button(text=f"🛒 {item['btn_name']} | {item['price']:,}đ", callback_data=f"buyitem_{item['id']}")
    builder.adjust(1)
    builder.row(types.InlineKeyboardButton(text="◀️ Quay lại Menu Chính", callback_data="back_to_main"))
    return builder.as_markup()

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    if user_id not in user_balances:
        user_balances[user_id] = 0
        save_data()

    caption = f"👋 **Chào mừng {message.from_user.full_name} đến với Shop Tự Động!**\n\n✨ Hệ thống cung cấp các dịch vụ chất lượng cao.\n👇 Vui lòng lựa chọn dịch vụ hoặc nạp tiền bên dưới:"
    await message.answer(caption, parse_mode="Markdown", reply_markup=main_menu_keyboard(user_id))

@dp.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    caption = f"👋 **Chào mừng {callback.from_user.full_name} đến với Shop Tự Động!**\n\n✨ Hệ thống cung cấp các dịch vụ chất lượng cao.\n👇 Vui lòng lựa chọn dịch vụ hoặc nạp tiền bên dưới:"
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(caption, parse_mode="Markdown", reply_markup=main_menu_keyboard(callback.from_user.id), disable_web_page_preview=True)

@dp.callback_query(F.data.startswith("select_"))
async def handle_select_category(callback: types.CallbackQuery):
    cat_key = callback.data.replace("select_", "")
    cat_data = PRODUCT_CATEGORIES.get(cat_key)
    if not cat_data:
        await callback.answer("❌ Mục này chưa có sản phẩm!", show_alert=True)
        return

    price_list_text = f"=== **{cat_data['name']}** ===\n\n{cat_data['description']}\n\n📋 **CHI TIẾT CÁC GÓI SẢN PHẨM:**\n"
    for idx, item in enumerate(cat_data["items"], 1):
        price_list_text += f"🔹 **Gói {idx}:** {item['detail_name']}\n💵 **Giá:** `{item['price']:,}đ`\n\n"
    price_list_text += "👇 **Bấm nút chọn gói tương ứng bên dưới để mua:**"

    try:
        await callback.message.edit_text(price_list_text, parse_mode="Markdown", reply_markup=sub_items_keyboard(cat_key), disable_web_page_preview=True)
    except Exception:
        await callback.message.delete()
        await callback.message.answer(price_list_text, parse_mode="Markdown", reply_markup=sub_items_keyboard(cat_key), disable_web_page_preview=True)

# ==============================================================================
# 5. XỬ LÝ NẠP TIỀN QUA NHẬP SỐ TIỀN
# ==============================================================================
@dp.callback_query(F.data == "deposit_direct")
async def handle_deposit_direct(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(DepositState.waiting_for_amount)
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="◀️ Quay lại Menu Chính", callback_data="back_to_main"))
    
    text = (
        "💳 **NẠP TIỀN TỰ ĐỘNG QUA MÃ QR**\n\n"
        "Vui lòng nhập số tiền bạn muốn nạp (Ví dụ: `50000`, `100000`, `200000`):"
    )
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(text, parse_mode="Markdown", reply_markup=builder.as_markup())

@dp.message(DepositState.waiting_for_amount)
async def process_deposit_amount(message: types.Message, state: FSMContext):
    text = message.text.strip().replace(".", "").replace(",", "")
    if not text.isdigit():
        await message.answer("❌ Số tiền không hợp lệ! Vui lòng chỉ nhập các chữ số (Ví dụ: `100000`).", parse_mode="Markdown")
        return

    amount = int(text)
    if amount <= 0:
        await message.answer("❌ Số tiền phải lớn hơn 0!", parse_mode="Markdown")
        return

    await state.clear()
    user_id = message.from_user.id
    memo = f"NAP {user_id}"
    
    qr_url = f"https://img.vietqr.io/image/{BANK_INFO['bank_id']}-{BANK_INFO['account_no']}-compact2.png?amount={amount}&addInfo={memo}&accountName={urllib.parse.quote(BANK_INFO['account_name'])}"
    
    caption = (
        "💳 **THÔNG TIN CHUYỂN KHOẢN NẠP TIỀN**\n\n"
        f"📌 **Ngân hàng:** {BANK_INFO['bank_id']} (Ngân hàng Quốc Tế)\n"
        f"📌 **Số tài khoản:** `{BANK_INFO['account_no']}`\n"
        f"📌 **Chủ tài khoản:** {BANK_INFO['account_name']}\n"
        f"📌 **Số tiền nạp:** `{amount:,}đ`\n"
        f"📌 **Nội dung chuyển khoản (BẮT BUỘC):** `{memo}`\n\n"
        "⚠️ *Lưu ý:* Vui lòng chuyển khoản đúng số tiền và nội dung ở trên, sau đó bấm nút xác nhận bên dưới!"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✅ Tôi đã chuyển khoản", callback_data=f"xac_nhan_nap_{user_id}_{amount}"))
    builder.row(types.InlineKeyboardButton(text="◀️ Quay lại Menu Chính", callback_data="back_to_main"))
    
    await message.answer_photo(photo=qr_url, caption=caption, parse_mode="Markdown", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("xac_nhan_nap_"))
async def handle_confirm_deposit(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    user_id = int(parts[3])
    amount = int(parts[4]) if len(parts) > 4 else 0
    
    user = callback.from_user
    user_full_name = user.full_name
    username = f"@{user.username}" if user.username else "Không có Username"

    await callback.answer("✅ Đã gửi yêu cầu xác nhận nạp tiền đến Admin!", show_alert=True)

    await callback.message.edit_caption(
        caption=(
            "⏳ **ĐÃ GỬI YÊU CẦU XÁC NHẬN NẠP TIỀN!**\n\n"
            "Hệ thống đã gửi thông báo đến Admin. Vui lòng đợi trong giây lát, Admin sẽ kiểm tra và cộng tiền cho bạn sớm nhất."
        ),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="◀️ Quay lại Menu Chính", callback_data="back_to_main")).as_markup()
    )

    try:
        admin_deposit_msg = (
            "🚨 **CÓ YÊU CẦU XÁC NHẬN NẠP TIỀN MỚI!**\n\n"
            f"👤 **Khách hàng:** {user_full_name}\n"
            f"🔗 **Username:** {username}\n"
            f"🆔 **ID Telegram của khách:** `{user_id}`\n"
            f"💵 **Số tiền khách muốn nạp:** `{amount:,}đ`\n"
            f"📝 **Nội dung chuyển khoản:** `NAP {user_id}`"
        )
        
        # Thêm nút Cộng tiền và Trừ tiền trực tiếp ngay dưới tin nhắn thông báo của Admin
        admin_kb = InlineKeyboardBuilder()
        admin_kb.row(
            types.InlineKeyboardButton(text=f"🟢 Cộng {amount:,}đ", callback_data=f"adm_cong_{user_id}_{amount}"),
            types.InlineKeyboardButton(text=f"🔴 Trừ {amount:,}đ", callback_data=f"adm_tru_{user_id}_{amount}")
        )

        await bot.send_message(chat_id=ADMIN_ID, text=admin_deposit_msg, parse_mode="Markdown", reply_markup=admin_kb.as_markup())
    except Exception as e:
        print(f"Lỗi gửi thông báo nạp tiền cho Admin: {e}")

# ==============================================================================
# 6. XỬ LÝ MUA HÀNG VÀ TỰ ĐỘNG BẮN THÔNG BÁO VỀ TELEGRAM ADMIN
# ==============================================================================
@dp.callback_query(F.data.startswith("buyitem_"))
async def handle_buy_sub_item(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_full_name = callback.from_user.full_name
    username = f"@{callback.from_user.username}" if callback.from_user.username else "Không có Username"
    
    item_id = callback.data.replace("buyitem_", "")
    target_item = None
    for cat in PRODUCT_CATEGORIES.values():
        for item in cat["items"]:
            if item["id"] == item_id:
                target_item = item
                break

    if not target_item:
        await callback.answer("❌ Sản phẩm không tồn tại!", show_alert=True)
        return

    current_balance = get_user_balance(user_id)
    price = target_item["price"]

    if current_balance < price:
        await callback.answer(f"❌ Số dư không đủ!\nSố dư hiện tại: {current_balance:,}đ\nGiá sản phẩm: {price:,}đ\nVui lòng nạp thêm tiền.", show_alert=True)
    else:
        user_balances[user_id] -= price
        save_data()
        order_id = generate_order_id()
        
        await callback.answer("🎉 Mua thành công! Vui lòng kiểm tra tin nhắn bên dưới.", show_alert=False)

        prefilled_text = f"Chào Admin, tôi vừa mua đơn hàng {order_id} ({target_item['detail_name']}). Vui lòng giao hàng cho tôi!"
        encoded_text = urllib.parse.quote(prefilled_text)
        admin_link = f"https://t.me/{ADMIN_USERNAME}?text={encoded_text}"

        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="📩 Nhắn tin Admin để nhận hàng", url=admin_link))
        builder.row(types.InlineKeyboardButton(text="◀️ Quay lại Menu Chính", callback_data="back_to_main"))

        customer_msg = (
            f"🎉 **ĐÃ MUA HÀNG THÀNH CÔNG!**\n\n"
            f"📦 **Sản phẩm:** {target_item['detail_name']}\n"
            f"💵 **Giá tiền:** `{price:,}đ`\n"
            f"🧾 **Mã đơn hàng:** `{order_id}`\n"
            f"💰 **Số dư còn lại:** `{user_balances[user_id]:,}đ`\n\n"
            f"👇 **Bấm nút bên dưới để chuyển sang nhắn cho Admin nhận hàng:**"
        )
        await callback.message.answer(customer_msg, parse_mode="Markdown", reply_markup=builder.as_markup())

        try:
            admin_msg = (
                f"🚨 **THÔNG BÁO: CÓ ĐƠN HÀNG MỚI!**\n\n"
                f"🧾 **Mã đơn hàng:** `{order_id}`\n"
                f"📦 **Sản phẩm mua:** {target_item['detail_name']}\n"
                f"💵 **Số tiền đã trừ:** `{price:,}đ`\n"
                f"-----------------------------------\n"
                f"👤 **THÔNG TIN KHÁCH HÀNG:**\n"
                f"• Họ tên: {user_full_name}\n"
                f"• Username: {username}\n"
                f"• ID Telegram: `{user_id}`"
            )
            await bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown")
        except Exception as e:
            print(f"Lỗi gửi thông báo cho Admin: {e}")

@dp.callback_query(F.data == "check_balance")
async def handle_check_balance(callback: types.CallbackQuery):
    balance = get_user_balance(callback.from_user.id)
    await callback.answer(f"💰 Số dư hiện tại của bạn: {balance:,} VNĐ", show_alert=True)

@dp.callback_query(F.data == "history")
async def handle_history(callback: types.CallbackQuery):
    await callback.answer("📜 Bạn chưa có lịch sử giao dịch nào.", show_alert=True)

# ==============================================================================
# 7. RUN BOT
# ==============================================================================
async def main():
    print("-----------------------------------")
    print("Bot đang chạy thành công với nút nạp tiền trực tiếp!")
    print("-----------------------------------")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())