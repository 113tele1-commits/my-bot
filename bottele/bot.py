from telethon import TelegramClient, events
from telethon.tl.types import UpdateNewChannelMessage, MessageActionChatAddUser, MessageActionChatJoinedByLink

# Điền API của bạn ở đây
API_ID = 28773966       
API_HASH = '0fcd39600314e24a86ee6d7ac91824ae'  

client = TelegramClient('account_bot_session', API_ID, API_HASH)

# =============================================================
# CÁCH MỚI: BẮT SỰ KIỆN GỐC (RAW UPDATE) - CHẮC CHẮN CHÀO ĐƯỢC
# =============================================================
@client.on(events.Raw())
async def raw_welcome_handler(event):
    # Kiểm tra xem có phải là tin nhắn mới trong Kênh/Nhóm siêu lớn không
    if isinstance(event, UpdateNewChannelMessage):
        message = event.message
        action = message.action
        
        # Kiểm tra xem hành động đó có phải là Add Mem hoặc Join qua Link không
        if isinstance(action, (MessageActionChatAddUser, MessageActionChatJoinedByLink)):
            # Lấy danh sách ID người mới vào
            user_ids = action.users if hasattr(action, 'users') else [message.from_id.user_id]
            
            for u_id in user_ids:
                try:
                    # Lấy thông tin chi tiết của người đó từ ID
                    user = await client.get_entity(u_id)
                    first_name = user.first_name if user.first_name else "Bạn mới"
                    
                    # Nội dung lời chào
                    welcome_text = (
                        f"» Chào mừng <a href='tg://user?id={user.id}'>{first_name}</a> đã tham gia vào nhóm! 🎉\n"
                        f"⚡ Chúc bạn có trải nghiệm vui vẻ. Đọc kỹ nội quy tránh bị lừa đảo nhé!"
                    )
                    
                    # Gửi lời chào vào nhóm
                    await client.send_message(message.peer_id, welcome_text, parse_mode='html')
                except Exception as e:
                    print(f"Lỗi khi lấy thông tin user: {e}")

# =============================================================
# PHẦN QUÉT TIN NHẮN CỦA BẠN (GIỮ NGUYÊN)
# =============================================================
@client.on(events.NewMessage()) 
async def handler(event):
    message_text = event.raw_text.lower()
    
    if message_text == '@':
        await event.reply('Các Thành Viên KHông Tự Ý Giao Dịch Với Nhau Tránh Lừa Đảo Cần Mua Bán Gì Hãy Nhắn Tin Cho Chủ Nhóm @ZaloViet84. 👋')
    elif message_text == 'bot ơi':
        await event.reply('Dạ, mình nghe đây! Có việc gì thế?')
    elif 'link' in message_text:
        await event.respond('xin chào quý khách hãy giao dịch an toàn tại ADM: [https://t.me/ZALOVIET84]')
    elif 'admin' in message_text:
        await event.respond('xin chào quý khách hãy giao dịch an toàn tại ADM: [https://t.me/ZALOVIET84]')
    elif 'giá' in message_text or 'mua' in message_text:
        await event.respond('Chào bạn, bạn muốn mua hàng vui lòng inbox @ZaloViet84 đợi mình tư vấn nhé!')
    elif 'mb' in message_text:
        await event.respond('Các Thành Viên Có Thể Tự Do Chát Nên Khi Mua Hàng Hãy Nhắn Tin Chủ Nhóm @ZaloViet84')
    elif 'ib' in message_text:
        await event.reply('Nguyên Cấm Các Thành Viên Trò Truyện Và GD Riêng Tránh Lừa Đảo Hãy Nhắn Tin Cho Chủ Nhóm @ZaloViet84?')
    elif 'khách' in message_text:
        await event.reply('Nguyên Cấm Các Thành Viên Trò Truyện Và GD Riêng Tránh Lừa Đảo Hãy Nhắn Tin Cho Chủ Nhóm @ZaloViet84?')
    elif 'nhận' in message_text:
        await event.respond('Các Thành Viên Có Thể Tự Do Chát Nên Khi Mua Hàng Hãy Nhắn Tin Chủ Nhóm @ZaloViet84')
    elif '' in message_text or 'mua' in message_text:
        await event.respond('Chào bạn, bạn muốn mua hàng vui lòng inbox @ZaloViet84 đợi mình tư vấn nhé!')
    elif 'telegram' in message_text:
        await event.respond('Các Thành Viên Có Thể Tự Do Chát Nên Khi Mua Hàng Hãy Nhắn Tin Chủ Nhóm @ZaloViet84') 
    elif 'zalo' in message_text:
        await event.respond('Các Thành Viên Có Thể Tự Do Chát Nên Khi Mua Hàng Hãy Nhắn Tin Chủ Nhóm @ZaloViet84')
    elif 'tài khoản' in message_text:
        await event.respond('Các Thành Viên Có Thể Tự Do Chát Nên Khi Mua Hàng Hãy Nhắn Tin Chủ Nhóm @ZaloViet84')
# Chạy bot
print("Bot đang quét tin nhắn và canh chào thành viên mới (Cơ chế Raw)...")
client.start()
client.run_until_disconnected()