from telethon import TelegramClient, events
from telethon.tl.types import Chat, Channel
from telethon.errors import FloodWaitError
import asyncio
import nest_asyncio
import re

# Cho phép lặp vòng lặp bất đồng bộ (Tránh lỗi Event loop is closed trên Python mới)
nest_asyncio.apply()

# ====== THÔNG TIN CẦN THAY BẰNG CỦA BẠN ======
api_id = 14100677
api_hash = '58dffdd527947b73760b999caf14300b'
# ================================================

# Thời gian nghỉ giữa các lượt lặp lại (giây) - Đợi lượt trước gửi xong hết rồi mới đếm ngược nghỉ
DELAY_BETWEEN_REPEATS = 60

client = TelegramClient('session_name', api_id, api_hash)

# Bộ lọc nhận diện tin nhắn: Link bài viết + chữ ok + số lần lặp (nếu có)
LINK_PATTERN = re.compile(r't\.me/([\w\d_]+)/(\d+)')
REPEAT_PATTERN = re.compile(r'ok\s*(\d+)', re.IGNORECASE)


async def get_all_group_ids():
    """Tự động quét và chỉ lấy các nhóm hợp lệ (bỏ qua kênh channel công khai)"""
    dest_ids = []
    print("🔄 Đang tự động quét danh sách nhóm của bạn...")
    try:
        async for dialog in client.iter_dialogs():
            entity = dialog.entity
            # Chỉ lấy nhóm thường (Chat) hoặc nhóm siêu lớn (Supergroup)
            if isinstance(entity, Chat) or (isinstance(entity, Channel) and entity.megagroup):
                # Bỏ qua nếu bạn đã rời nhóm hoặc bị admin cấm chat
                if entity.left or (entity.default_banned_rights and entity.default_banned_rights.send_messages):
                    continue
                dest_ids.append(dialog.id)
        print(f"✅ Đã tìm thấy {len(dest_ids)} nhóm hợp lệ để gửi!")
    except Exception as e:
        print(f"❌ Lỗi khi quét danh sách nhóm: {e}")
    return dest_ids


async def send_to_single_group(dest, message, results_tracker):
    """Hàm bổ trợ gửi tin nhắn cho từng nhóm riêng lẻ (để chạy song song)"""
    while True:
        try:
            # Ép lệnh gửi chỉ chạy trong tối đa 15 giây để tránh treo ngầm
            await asyncio.wait_for(client.forward_messages(dest, message), timeout=15)
            results_tracker['success'] += 1
            break
        except asyncio.TimeoutError:
            print(f"⏳ Nhóm {dest} phản hồi quá lâu (Bỏ qua)...")
            results_tracker['fail'] += 1
            break
        except FloodWaitError as e:
            # Nếu dính FloodWait, task này tự ngủ riêng rồi thử lại, không ảnh hưởng task khác
            print(f"⏳ Nhóm {dest} gặp FloodWait. Cần chờ {e.seconds} giây...")
            await asyncio.sleep(e.seconds + 2)
        except Exception as e:
            results_tracker['fail'] += 1
            print(f"✘ Lỗi khi forward tới nhóm {dest}: {e}")
            break


async def forward_to_all_parallel(message, current_round, total_rounds):
    """Tạo danh sách task và kích hoạt gửi song song đồng thời cho lượt hiện tại"""
    dest_ids = await get_all_group_ids()
    
    if not dest_ids:
        print("❌ Không tìm thấy nhóm nào hợp lệ để gửi.")
        return False

    print(f"\n🚀 [LƯỢT {current_round}/{total_rounds}] Bắt đầu gửi SONG SONG tới {len(dest_ids)} nhóm...")
    
    # Biến tracker để đếm số lượng thành công / thất bại từ các luồng song song
    results_tracker = {'success': 0, 'fail': 0}
    
    # Tạo danh sách các tác vụ gửi song song
    tasks = [send_to_single_group(dest, message, results_tracker) for dest in dest_ids]
    
    # Kích hoạt toàn bộ các task chạy cùng một lúc và đợi cho đến khi tất cả hoàn thành
    await asyncio.gather(*tasks)
                
    print(f"🏁 Hoàn thành lượt {current_round}: Thành công {results_tracker['success']}, Thất bại {results_tracker['fail']}\n")
    return True


@client.on(events.NewMessage(chats='me'))
async def handler(event):
    text = event.raw_text or ''
    
    # 1. Kiểm tra điều kiện: Phải có link t.me và có chữ 'ok'
    match_link = LINK_PATTERN.search(text)
    if not match_link or 'ok' not in text.lower():
        return

    # 2. Kiểm tra xem có điền số lần lặp không (Ví dụ: ok 10 -> lặp 10 lần. Nếu chỉ gõ ok -> chạy 1 lần)
    match_repeat = REPEAT_PATTERN.search(text)
    total_repeats = 1
    if match_repeat:
        total_repeats = int(match_repeat.group(1))

    print(f"\n[DEBUG] Nhận lệnh hợp lệ từ Saved Messages. Tổng số lượt chạy: {total_repeats}")
    channel_username, msg_id = match_link.group(1), int(match_link.group(2))

    try:
        # Lấy tin nhắn gốc cần forward từ link
        source_entity = await client.get_entity(channel_username)
        message = await client.get_messages(source_entity, ids=msg_id)
        
        if message is None:
            await event.reply("❌ Không tìm thấy bài viết này từ link bạn gửi.")
            return

        await event.reply(f"🔄 Hệ thống bắt đầu chạy (Tổng số lượt gửi: {total_repeats}). Các nhóm sẽ được gửi SONG SONG...")
        
        # Tiến hành chạy theo số lượt yêu cầu
        for lan in range(1, total_repeats + 1):
            # Gửi song song toàn bộ nhóm trong lượt này
            await forward_to_all_parallel(message, current_round=lan, total_rounds=total_repeats)
            
            # Nếu chưa phải lượt cuối cùng thì nghỉ rồi mới chạy tiếp lượt sau
            if lan < total_repeats:
                print(f"⏳ Đang nghỉ {DELAY_BETWEEN_REPEATS} giây trước khi bước sang lượt tiếp theo...")
                await asyncio.sleep(DELAY_BETWEEN_REPEATS)

        await event.reply(f"✅ Đã hoàn thành toàn bộ {total_repeats} lượt gửi tin nhắn!")
        
    except Exception as e:
        await event.reply(f"❌ Có lỗi xảy ra: {e}")
        print(f"[DEBUG] Lỗi chi tiết: {e}")


async def main():
    print("🤖 BOT SONG SONG + LẶP LẠI ĐÃ SẴN SÀNG!")
    print("--------------------------------------------------")
    print("👉 Cách 1 (Gửi 1 lần song song): Gửi [Link bài viết] ok")
    print("👉 Cách 2 (Gửi lặp lại nhiều lần song song): Gửi [Link bài viết] ok 10")
    print("--------------------------------------------------")
    await client.run_until_disconnected()


if __name__ == '__main__':
    try:
        client.start()
        client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n🛑 Đã tắt Bot an toàn.")