# -*- coding: utf-8 -*-
"""
بوت تصميم احترافي
متوافق مع Python 3.13
مكتبات: python-telegram-bot==20.5
"""
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonCommands
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = "8268148633:AAHlcBIaMplGzwlmiZ2w11NCCWy5CA_tbJY"  # ضع توكن البوت
ADMINS = [1226196443]  # ضع ID الأدمن

DATA_FILE = "data.json"
user_state = {}

# ===== تحميل وحفظ البيانات =====
def load_data():
    if not os.path.exists(DATA_FILE):
        data = {
            "users": [],
            "admins": ADMINS,
            "wallet": {},
            "admin_wallet": 0,
            "subscribers": {},
            "subscriptions": {
                "10 صور": {"price": 10000, "count": 10},
                "30 صورة": {"price": 30000, "count": 30},
                "50 صورة": {"price": 50000, "count": 50}
            },
            "payments": {},
            "orders": [],
            "pending_payments": {},
            "welcome": "أهلا بك في بوت التصميم 🎨"
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ===== القائمة الرئيسية =====
def main_menu(user_id, data):
    keyboard = [
        [InlineKeyboardButton("💰 رصيدي", callback_data="balance")],
        [InlineKeyboardButton("💳 شحن رصيد", callback_data="deposit")],
        [InlineKeyboardButton("⭐ الاشتراك بالباقة", callback_data="subscribe")],
        [InlineKeyboardButton("🎨 طلب تصميم", callback_data="design")]
    ]
    if user_id in data["admins"]:
        keyboard.append([InlineKeyboardButton("⚙️ لوحة التحكم", callback_data="admin_panel")])
    return InlineKeyboardMarkup(keyboard)

# ===== /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = load_data()

    if user.id not in data["users"]:
        data["users"].append(user.id)
        data["wallet"][str(user.id)] = 0
        save_data(data)

    await update.message.reply_text(
        data["welcome"],
        reply_markup=main_menu(user.id, data)
    )

# ===== عرض الرصيد =====
async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = load_data()
    balance = data["wallet"].get(str(user_id), 0)
    await query.edit_message_text(f"💰 رصيدك الحالي: {balance} ل.س", reply_markup=main_menu(user_id, data))

# ===== قائمة الاشتراكات =====
async def subscriptions_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    user_id = query.from_user.id
    keyboard = []
    for name, info in data["subscriptions"].items():
        price = info["price"]
        count = info["count"]
        keyboard.append([InlineKeyboardButton(f"{name} | {count} تصميم | {price} ل.س", callback_data=f"buy_sub_{name}")])
    await query.edit_message_text("⭐ اختر الباقة المناسبة", reply_markup=InlineKeyboardMarkup(keyboard))

# ===== شراء الباقة =====
async def buy_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = load_data()
    sub_name = query.data.replace("buy_sub_", "")
    if sub_name not in data["subscriptions"]:
        await query.edit_message_text("❌ الباقة غير موجودة")
        return
    sub_info = data["subscriptions"][sub_name]
    price = sub_info["price"]
    count = sub_info["count"]
    balance = data["wallet"].get(str(user_id), 0)
    if balance < price:
        await query.edit_message_text("❌ رصيدك غير كافي للباقة المختارة")
        return
    # خصم الرصيد وتفعيل الباقة
    data["wallet"][str(user_id)] -= price
    data["admin_wallet"] += price
    data["subscribers"][str(user_id)] = {"package": sub_name, "remaining": count}
    save_data(data)
    await query.edit_message_text(f"✅ تم الاشتراك بنجاح\nالباقة: {sub_name}\nعدد التصاميم: {count}")
    # إشعار الأدمن
    for admin in data["admins"]:
        try:
            await context.bot.send_message(admin, f"📥 قام المستخدم {user_id} بالاشتراك في باقة {sub_name} بمبلغ {price} ل.س")
        except: pass

# ===== قائمة التصميم =====
async def design_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = load_data()
    if str(user_id) not in data["subscribers"]:
        await query.edit_message_text("❌ يجب الاشتراك بالباقة أولاً")
        return
    keyboard = [
        [InlineKeyboardButton("🖼 تصميم صورة", callback_data="design_image")],
        [InlineKeyboardButton("🎨 تصميم لوغو", callback_data="design_logo")],
        [InlineKeyboardButton("🎬 تصميم فيديو", callback_data="design_video")]
    ]
    await query.edit_message_text("🎨 اختر نوع التصميم", reply_markup=InlineKeyboardMarkup(keyboard))

# ===== اختيار نوع التصميم =====
async def design_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_state[user_id] = query.data
    await query.message.reply_text("✏️ اكتب تفاصيل التصميم الذي تريده")

# ===== استقبال تفاصيل التصميم =====
async def handle_design_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_state: return
    state = user_state[user_id]
    if not state.startswith("design_"): return
    data = load_data()
    order_id = len(data["orders"]) + 1
    sub = data["subscribers"].get(str(user_id))
    if sub is None or sub["remaining"] <= 0:
        await update.message.reply_text("❌ انتهت تصاميم باقتك، اشترك مرة أخرى")
        del user_state[user_id]
        return
    sub["remaining"] -= 1
    order = {"id": order_id, "user": user_id, "type": state.replace("design_",""), "text": update.message.text, "status":"pending"}
    data["orders"].append(order)
    save_data(data)
    for admin in data["admins"]:
        try:
            await context.bot.send_message(admin, f"📥 طلب تصميم جديد\nالطلب: {order_id}\nالمستخدم: {user_id}\nالنوع: {state.replace('design_','')}\nالتفاصيل:\n{update.message.text}")
        except: pass
    await update.message.reply_text("✅ تم إرسال طلبك")
    del user_state[user_id]

# ===== قائمة شحن الرصيد =====
async def deposit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = load_data()
    keyboard = []
    for name, link in data["payments"].items():
        keyboard.append([InlineKeyboardButton(name, url=link)])
    keyboard.append([InlineKeyboardButton("📤 إرسال إشعار الدفع", callback_data="send_payment")])
    await query.edit_message_text("💳 اختر طريقة الدفع ثم أرسل صورة الإشعار", reply_markup=InlineKeyboardMarkup(keyboard))

# ===== طلب صورة الدفع =====
async def ask_payment_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_state[user_id] = "waiting_payment_photo"
    await query.message.reply_text("📸 أرسل صورة إشعار الدفع الآن")

# ===== استقبال صورة الدفع =====
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_state: return
    if user_state[user_id] != "waiting_payment_photo": return
    photo_file_id = update.message.photo[-1].file_id
    data = load_data()
    payment_id = str(len(data["pending_payments"]) + 1)
    data["pending_payments"][payment_id] = {"user": user_id, "photo": photo_file_id}
    save_data(data)
    del user_state[user_id]
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ قبول", callback_data=f"accept_payment_{payment_id}"), InlineKeyboardButton("❌ رفض", callback_data=f"reject_payment_{payment_id}")]])
    for admin in data["admins"]:
        try:
            await context.bot.send_photo(admin, photo_file_id, caption=f"💳 طلب شحن رصيد\nالمستخدم: {user_id}\nرقم الطلب: {payment_id}", reply_markup=keyboard)
        except: pass
    await update.message.reply_text("تم إرسال الطلب للأدمن للمراجعة")

# ===== قبول الدفع =====
async def accept_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    payment_id = query.data.split("_")[-1]
    if payment_id not in data["pending_payments"]:
        await query.message.reply_text("❌ الطلب غير موجود")
        return
    target_user = data["pending_payments"][payment_id]["user"]
    user_state[query.from_user.id] = f"add_balance_{target_user}_{payment_id}"
    await query.message.reply_text(f"✏️ اكتب المبلغ المودع للمستخدم {target_user}")

# ===== إضافة الرصيد بعد قبول الدفع =====
async def handle_text_for_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_state: return
    state = user_state[user_id]
    if not state.startswith("add_balance"): return
    parts = state.split("_")
    target_user = parts[2]
    payment_id = parts[3]
    try:
        amount = int(update.message.text)
    except:
        await update.message.reply_text("❌ المبلغ غير صحيح")
        return
    data = load_data()
    data["wallet"][target_user] = data["wallet"].get(target_user,0) + amount
    data["admin_wallet"] += 0
    data["pending_payments"].pop(payment_id,None)
    save_data(data)
    await update.message.reply_text(f"✅ تم إضافة {amount} ل.س إلى رصيد المستخدم")
    try:
        await context.bot.send_message(target_user, f"💰 تم شحن {amount} ل.س إلى رصيدك")
    except: pass
    del user_state[user_id]

# ===== لوحة التحكم للأدمن =====
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = load_data()
    if user_id not in data["admins"]:
        await query.message.reply_text("❌ أنت لست أدمن")
        return
    keyboard = [
        [InlineKeyboardButton("➕ إضافة باقة", callback_data="add_package")],
        [InlineKeyboardButton("➖ حذف باقة", callback_data="del_package")],
        [InlineKeyboardButton("✏️ تعديل باقة", callback_data="edit_package")],
        [InlineKeyboardButton("➕ إضافة طريقة دفع", callback_data="add_payment")],
        [InlineKeyboardButton("➖ حذف طريقة دفع", callback_data="del_payment")],
        [InlineKeyboardButton("📢 رسالة للجميع", callback_data="broadcast")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")],
        [InlineKeyboardButton("👑 إضافة أدمن", callback_data="add_admin")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="back")]
    ]
    await query.edit_message_text("⚙️ لوحة التحكم", reply_markup=InlineKeyboardMarkup(keyboard))

# ===== معالجة نصوص لوحة التحكم =====
async def text_handler_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if user_id not in user_state: return
    state = user_state[user_id]
    data = load_data()
    try:
        # البث
        if state == "broadcast":
            for u in data["users"]:
                try: await context.bot.send_message(u, text)
                except: continue
            await update.message.reply_text("✅ تم الإرسال")
        # إدارة الباقات
        elif state == "add_package":
            name, price, count = text.split("|")
            data["subscriptions"][name.strip()] = {"price": int(price.strip()), "count": int(count.strip())}
            save_data(data)
            await update.message.reply_text("✅ تمت إضافة الباقة")
        elif state == "del_package":
            data["subscriptions"].pop(text.strip(), None)
            save_data(data)
            await update.message.reply_text("✅ تم حذف الباقة")
        elif state == "edit_package":
            name, price, count = text.split("|")
            if name.strip() in data["subscriptions"]:
                data["subscriptions"][name.strip()] = {"price": int(price.strip()), "count": int(count.strip())}
                save_data(data)
                await update.message.reply_text("✅ تم تعديل الباقة")
            else: await update.message.reply_text("❌ الباقة غير موجودة")
        # إدارة طرق الدفع
        elif state == "add_payment":
            name, link = text.split("|")
            data["payments"][name.strip()] = link.strip()
            save_data(data)
            await update.message.reply_text("✅ تمت إضافة طريقة الدفع")
        elif state == "del_payment":
            data["payments"].pop(text.strip(), None)
            save_data(data)
            await update.message.reply_text("✅ تم حذف طريقة الدفع")
        # إضافة أدمن
        elif state == "add_admin":
            data["admins"].append(int(text.strip()))
            save_data(data)
            await update.message.reply_text("✅ تمت إضافة أدمن")
    except:
        await update.message.reply_text("❌ الصيغة خاطئة")
    del user_state[user_id]

# ===== تعيين قائمة الدردشة الدائمة =====
async def set_menu(app):
    await app.bot.set_my_commands([("start","بدء البوت")])
    await app.bot.set_chat_menu_button(menu_button=MenuButtonCommands())

# ===== إنشاء التطبيق وتشغيل البوت =====
app = Application.builder().token(TOKEN).build()
app.post_init = set_menu

# ===== Handlers =====
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(show_balance, pattern="^balance$"))
app.add_handler(CallbackQueryHandler(deposit_menu, pattern="^deposit$"))
app.add_handler(CallbackQueryHandler(subscriptions_menu, pattern="^subscribe$"))
app.add_handler(CallbackQueryHandler(buy_subscription, pattern="^buy_sub_"))
app.add_handler(CallbackQueryHandler(design_menu, pattern="^design$"))
app.add_handler(CallbackQueryHandler(design_type, pattern="^design_"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_design_text))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_for_balance))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler_admin))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(CallbackQueryHandler(admin_panel, pattern="^admin_panel$"))
app.add_handler(CallbackQueryHandler(ask_payment_photo, pattern="^send_payment$"))
app.add_handler(CallbackQueryHandler(accept_payment, pattern="^accept_payment_"))

print("Bot running...")
app.run_polling()
