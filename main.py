# main_part1.py
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonCommands
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = "8268148633:AAHlcBIaMplGzwlmiZ2w11NCCWy5CA_tbJY"
ADMINS = [1226196443]

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
        with open(DATA_FILE,"w",encoding="utf-8") as f:
            json.dump(data,f,ensure_ascii=False,indent=4)
    with open(DATA_FILE,"r",encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE,"w",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=4)

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
    text = f"💰 رصيدك الحالي:\n{balance} ليرة سورية"
    await query.edit_message_text(text, reply_markup=main_menu(user_id, data))

# ===== شحن الرصيد (عرض طرق الدفع) =====
async def deposit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    keyboard = []
    for name, link in data["payments"].items():
        keyboard.append([InlineKeyboardButton(name, url=link)])
    keyboard.append([InlineKeyboardButton("📤 إرسال إشعار الدفع", callback_data="send_payment")])
    await query.edit_message_text(
        "اختر طريقة الدفع ثم أرسل صورة الإشعار",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===== عرض الباقات للاشتراك =====
async def subscriptions_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    keyboard = []
    for name, info in data["subscriptions"].items():
        price = info["price"]
        count = info["count"]
        keyboard.append([
            InlineKeyboardButton(f"{name} | {count} تصميم | {price} ل.س", callback_data=f"buy_sub_{name}")
        ])
    await query.edit_message_text(
        "اختر الباقة المناسبة",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===== تعيين قائمة الدردشة الدائمة =====
async def set_menu(app):
    await app.bot.set_my_commands([("start","بدء البوت")])
    await app.bot.set_chat_menu_button(menu_button=MenuButtonCommands())

# ===== إنشاء التطبيق =====
app = Application.builder().token(TOKEN).build()
app.post_init = set_menu

# ===== Handlers =====
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(subscriptions_menu, pattern="subscribe"))
app.add_handler(CallbackQueryHandler(deposit_menu, pattern="deposit"))
app.add_handler(CallbackQueryHandler(show_balance, pattern="balance"))

print("Bot running...")
app.run_polling()

# main_part2.py
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters

from main_part1 import load_data, save_data, user_state

# ===== استقبال صورة الدفع =====
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_state:
        return

    state = user_state[user_id]

    if state != "waiting_payment_photo":
        return

    photo = update.message.photo[-1].file_id
    data = load_data()
    payment_id = str(len(data["pending_payments"]) + 1)

    data["pending_payments"][payment_id] = {"user": user_id}
    save_data(data)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ قبول", callback_data=f"accept_payment_{payment_id}"),
            InlineKeyboardButton("❌ رفض", callback_data=f"reject_payment_{payment_id}")
        ]
    ])

    for admin in data["admins"]:
        await context.bot.send_photo(
            admin,
            photo,
            caption=f"💳 طلب شحن رصيد\nالمستخدم: {user_id}\nرقم الطلب: {payment_id}",
            reply_markup=keyboard
        )

    await update.message.reply_text("تم إرسال الطلب للأدمن للمراجعة")
    del user_state[user_id]

# ===== قبول الدفع من الأدمن =====
async def accept_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()

    payment_id = query.data.split("_")[-1]
    if payment_id not in data["pending_payments"]:
        await query.message.reply_text("❌ الطلب غير موجود")
        return

    user_id = data["pending_payments"][payment_id]["user"]
    user_state[query.from_user.id] = f"add_balance_{user_id}_{payment_id}"

    await query.message.reply_text("اكتب مبلغ الشحن ليتم إضافته للمستخدم")

# ===== إضافة الرصيد بعد الموافقة =====
async def handle_text_for_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_state:
        return

    state = user_state[user_id]
    if not state.startswith("add_balance"):
        return

    data = load_data()
    parts = state.split("_")
    target_user = parts[2]
    payment_id = parts[3]

    try:
        amount = int(text)
    except:
        await update.message.reply_text("❌ الصيغة خطأ")
        return

    data["wallet"][target_user] += amount
    data["admin_wallet"] += 0  # لمزيد التوضيح يمكن تعديل حسب المحفظة العامة
    del data["pending_payments"][payment_id]
    save_data(data)

    await update.message.reply_text("✅ تم إضافة الرصيد بنجاح")
    try:
        await context.bot.send_message(target_user, f"تم شحن {amount} ليرة إلى رصيدك")
    except:
        pass

    del user_state[user_id]

# ===== دمج مع Handlers في main =====
# app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
# app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_for_balance))

# main_part3.py
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from main_part1 import load_data, save_data, user_state

# ===== قائمة اختيار نوع التصميم =====
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

    await query.edit_message_text(
        "اختر نوع التصميم",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===== اختيار نوع التصميم =====
async def design_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_state[user_id] = query.data

    await query.message.reply_text("✏️ اكتب تفاصيل التصميم الذي تريده")

# ===== استقبال تفاصيل التصميم ومعالجة الطلب =====
async def handle_design_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_state:
        return

    state = user_state[user_id]

    if not state.startswith("design_"):
        return

    data = load_data()

    # التحقق من الباقة المتاحة وعدد التصاميم
    subscriber = data["subscribers"].get(str(user_id))
    if not subscriber or subscriber["remaining"] <= 0:
        await update.message.reply_text("❌ لا يوجد تصميمات متبقية في باقتك")
        del user_state[user_id]
        return

    # تسجيل الطلب
    order_id = len(data["orders"]) + 1
    order = {
        "id": order_id,
        "user": user_id,
        "type": state,
        "text": text,
        "status": "pending"
    }
    data["orders"].append(order)

    # خصم التصميم من الباقة
    subscriber["remaining"] -= 1
    save_data(data)

    # إشعار الأدمن
    for admin in data["admins"]:
        await context.bot.send_message(
            admin,
            f"📥 طلب تصميم جديد\n\n"
            f"الطلب: {order_id}\n"
            f"المستخدم: {user_id}\n"
            f"نوع التصميم: {state}\n"
            f"التفاصيل:\n{text}"
        )

    await update.message.reply_text("✅ تم إرسال طلبك بنجاح")
    del user_state[user_id]

# ===== إضافة Handlers في main =====
# app.add_handler(CallbackQueryHandler(design_menu, pattern="^design$"))
# app.add_handler(CallbackQueryHandler(design_type, pattern="^design_"))
# app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_design_text))
# main_part4.py
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from main_part1 import load_data, save_data, user_state

# ===== لوحة التحكم الرئيسية =====
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

    await query.edit_message_text(
        "⚙️ لوحة التحكم",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===== الإحصائيات =====
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()

    users = len(data["users"])
    subs = len(data["subscribers"])
    orders = len(data["orders"])
    admin_balance = data.get("admin_wallet",0)

    text = (
        f"📊 إحصائيات البوت\n\n"
        f"👥 المستخدمين: {users}\n"
        f"💎 المشتركين: {subs}\n"
        f"📦 الطلبات: {orders}\n"
        f"💰 محفظة الأدمن: {admin_balance} ل.س"
    )

    await query.edit_message_text(text)

# ===== البث =====
async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_state[query.from_user.id] = "broadcast"
    await query.message.reply_text("✏️ اكتب الرسالة التي تريد إرسالها لجميع المستخدمين")

# ===== إدارة الباقات =====
async def manage_packages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_state[query.from_user.id] = query.data

    if query.data == "add_package":
        await query.message.reply_text("اكتب الباقة الجديدة بالشكل: اسم الباقة | السعر | عدد التصاميم")
    elif query.data == "del_package":
        await query.message.reply_text("اكتب اسم الباقة المراد حذفها")
    elif query.data == "edit_package":
        await query.message.reply_text("اكتب تعديل الباقة بالشكل: اسم الباقة | السعر الجديد | عدد التصاميم")

# ===== إدارة طرق الدفع =====
async def manage_payments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_state[query.from_user.id] = query.data

    if query.data == "add_payment":
        await query.message.reply_text("اكتب طريقة الدفع بالشكل: اسم الطريقة | الرابط أو الكود")
    elif query.data == "del_payment":
        await query.message.reply_text("اكتب اسم طريقة الدفع المراد حذفها")

# ===== إضافة أدمن =====
async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_state[query.from_user.id] = "add_admin"
    await query.message.reply_text("اكتب ID المستخدم الذي تريد إضافته كأدمن")

# ===== معالجة نصوص لوحة التحكم =====
async def text_handler_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    data = load_data()

    if user_id not in user_state:
        return

    state = user_state[user_id]

    try:
        # البث
        if state == "broadcast":
            for u in data["users"]:
                try:
                    await context.bot.send_message(u, text)
                except:
                    continue
            await update.message.reply_text("✅ تم الإرسال")

        # إدارة الباقات
        elif state == "add_package":
            name, price, count = text.split("|")
            data["subscriptions"][name.strip()] = {
                "price": int(price.strip()),
                "count": int(count.strip())
            }
            save_data(data)
            await update.message.reply_text("✅ تم إضافة الباقة")

        elif state == "del_package":
            data["subscriptions"].pop(text.strip(), None)
            save_data(data)
            await update.message.reply_text("✅ تم حذف الباقة")

        elif state == "edit_package":
            name, price, count = text.split("|")
            if name.strip() in data["subscriptions"]:
                data["subscriptions"][name.strip()] = {
                    "price": int(price.strip()),
                    "count": int(count.strip())
                }
                save_data(data)
                await update.message.reply_text("✅ تم تعديل الباقة")
            else:
                await update.message.reply_text("❌ الباقة غير موجودة")

        # إدارة طرق الدفع
        elif state == "add_payment":
            name, link = text.split("|")
            data["payments"][name.strip()] = link.strip()
            save_data(data)
            await update.message.reply_text("✅ تم إضافة طريقة الدفع")

        elif state == "del_payment":
            data["payments"].pop(text.strip(), None)
            save_data(data)
            await update.message.reply_text("✅ تم حذف طريقة الدفع")

        # إضافة أدمن
        elif state == "add_admin":
            data["admins"].append(int(text.strip()))
            save_data(data)
            await update.message.reply_text("✅ تم إضافة أدمن")

    except:
        await update.message.reply_text("❌ الصيغة خطأ")

    del user_state[user_id]

# main_part5.py
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from main_part1 import load_data, save_data, user_state

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
        keyboard.append([
            InlineKeyboardButton(f"{name} | {count} تصميم | {price} ل.س", callback_data=f"buy_sub_{name}")
        ])

    await query.edit_message_text(
        "⭐ اختر الباقة المناسبة",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===== شراء باقة =====
async def buy_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = load_data()

    sub_name = query.data.replace("buy_sub_", "")
    sub = data["subscriptions"][sub_name]

    price = sub["price"]
    count = sub["count"]

    balance = data["wallet"].get(str(user_id), 0)

    if balance < price:
        await query.edit_message_text("❌ رصيدك غير كافي، اشحن رصيدك أولاً")
        return

    # خصم تلقائي من رصيد المستخدم وتحويله لمحفظة الأدمن
    data["wallet"][str(user_id)] -= price
    data["admin_wallet"] += price

    # تفعيل الباقة
    data["subscribers"][str(user_id)] = {
        "package": sub_name,
        "remaining": count
    }

    save_data(data)

    await query.edit_message_text(
        f"✅ تم الاشتراك بنجاح\n\nالباقة: {sub_name}\nعدد التصاميم: {count}\n💰 تم خصم {price} ل.س من رصيدك"
    )

# ===== قائمة تصميمات المستخدم =====
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
    if user_id not in user_state:
        return

    state = user_state[user_id]
    if not state.startswith("design_"):
        return

    data = load_data()
    order_id = len(data["orders"]) + 1

    # حفظ الطلب
    order = {
        "id": order_id,
        "user": user_id,
        "type": state,
        "text": update.message.text,
        "status": "pending"
    }

    data["orders"].append(order)

    # خصم من الباقة
    sub = data["subscribers"][str(user_id)]
    sub["remaining"] -= 1

    save_data(data)

    # إشعار الأدمن
    for admin in data["admins"]:
        await context.bot.send_message(
            admin,
            f"📥 طلب تصميم جديد\n\nالطلب: {order_id}\nالمستخدم: {user_id}\nنوع التصميم: {state}\n\nالتفاصيل:\n{update.message.text}"
        )

    await update.message.reply_text("✅ تم إرسال طلبك بنجاح")
    del user_state[user_id]

# main_part6.py
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from main_part1 import load_data, save_data, user_state

# ===== قائمة شحن الرصيد =====
async def deposit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    keyboard = []

    for name, link in data["payments"].items():
        keyboard.append([InlineKeyboardButton(name, url=link)])

    keyboard.append([InlineKeyboardButton("📤 إرسال إشعار الدفع", callback_data="send_payment")])

    await query.edit_message_text(
        "💳 اختر طريقة الدفع ثم أرسل صورة الإشعار",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

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
    if user_id not in user_state:
        return
    state = user_state[user_id]
    if state != "waiting_payment_photo":
        return

    photo_file_id = update.message.photo[-1].file_id
    data = load_data()
    payment_id = str(len(data["pending_payments"]) + 1)

    # حفظ الدفع المعلق
    data["pending_payments"][payment_id] = {"user": user_id, "photo": photo_file_id}
    save_data(data)

    # أزرار قبول أو رفض للأدمن
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ قبول", callback_data=f"accept_payment_{payment_id}"),
            InlineKeyboardButton("❌ رفض", callback_data=f"reject_payment_{payment_id}")
        ]
    ])

    # إرسال إشعار لكل الأدمن
    for admin in data["admins"]:
        await context.bot.send_photo(
            admin,
            photo_file_id,
            caption=f"💳 طلب شحن رصيد\nالمستخدم: {user_id}\nرقم الطلب: {payment_id}",
            reply_markup=keyboard
        )

    await update.message.reply_text("تم إرسال الطلب للأدمن للمراجعة")
    del user_state[user_id]

# ===== قبول الدفع =====
async def accept_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    payment_id = query.data.split("_")[-1]

    if payment_id not in data["pending_payments"]:
        await query.message.reply_text("❌ الطلب غير موجود")
        return

    user_id = data["pending_payments"][payment_id]["user"]
    user_state[query.from_user.id] = f"add_balance_{user_id}_{payment_id}"
    await query.message.reply_text(f"✏️ اكتب المبلغ المودع للمستخدم {user_id}")

# ===== إضافة الرصيد بعد قبول الدفع =====
async def handle_text_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_state:
        return

    state = user_state[user_id]
    if not state.startswith("add_balance"):
        return

    data = load_data()
    parts = state.split("_")
    target_user = parts[2]
    payment_id = parts[3]

    try:
        amount = int(update.message.text)
        data["wallet"][target_user] += amount
        del data["pending_payments"][payment_id]
        save_data(data)

        await update.message.reply_text("✅ تم إضافة الرصيد بنجاح")

        # إخطار المستخدم
        try:
            await context.bot.send_message(target_user, f"💰 تم شحن {amount} ليرة إلى رصيدك")
        except:
            pass
    except:
        await update.message.reply_text("❌ صيغة المبلغ غير صحيحة")

    del user_state[user_id]

# main_part7.py
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from main_part1 import load_data, save_data, user_state, main_menu

# ===== لوحة التحكم =====
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

    await query.edit_message_text(
        "⚙️ لوحة التحكم",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===== الإحصائيات =====
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()

    text = f"""
📊 إحصائيات البوت

👥 المستخدمين: {len(data['users'])}
💎 المشتركين: {len(data['subscribers'])}
📦 الطلبات: {len(data['orders'])}
💰 محفظة الأدمن: {data['admin_wallet']} ل.س
"""
    await query.edit_message_text(text)

# ===== بث رسالة لجميع المستخدمين =====
async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_state[query.from_user.id] = "broadcast"
    await query.message.reply_text("✏️ اكتب الرسالة التي تريد إرسالها لجميع المستخدمين")

# ===== إدارة الباقات =====
async def manage_packages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    action = query.data
    user_state[user_id] = action

    if action == "add_package":
        await query.message.reply_text("✏️ اكتب الباقة الجديدة بالشكل: اسم الباقة | السعر | عدد التصاميم")
    elif action == "del_package":
        await query.message.reply_text("✏️ اكتب اسم الباقة المراد حذفها")
    elif action == "edit_package":
        await query.message.reply_text("✏️ اكتب تعديل الباقة بالشكل: اسم الباقة | السعر الجديد | عدد التصاميم")

# ===== إدارة طرق الدفع =====
async def manage_payments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    action = query.data
    user_state[user_id] = action

    if action == "add_payment":
        await query.message.reply_text("✏️ اكتب طريقة الدفع بالشكل: اسم الطريقة | الرابط أو الكود")
    elif action == "del_payment":
        await query.message.reply_text("✏️ اكتب اسم طريقة الدفع المراد حذفها")

# ===== إضافة أدمن =====
async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_state[query.from_user.id] = "add_admin"
    await query.message.reply_text("✏️ اكتب ID المستخدم الذي تريد إضافته كأدمن")

# ===== معالجة نصوص لوحة التحكم =====
async def text_handler_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_state:
        return

    state = user_state[user_id]
    data = load_data()

    try:
        # البث
        if state == "broadcast":
            for u in data["users"]:
                try:
                    await context.bot.send_message(u, text)
                except:
                    continue
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
            else:
                await update.message.reply_text("❌ الباقة غير موجودة")

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

# main_part8.py
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from main_part1 import load_data, save_data, user_state

# ===== قائمة التصميم =====
async def design_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = load_data()

    # التأكد من وجود الاشتراك
    if str(user_id) not in data["subscribers"]:
        await query.edit_message_text("❌ يجب الاشتراك بالباقة أولاً")
        return

    keyboard = [
        [InlineKeyboardButton("🖼 تصميم صورة", callback_data="design_image")],
        [InlineKeyboardButton("🎨 تصميم لوغو", callback_data="design_logo")],
        [InlineKeyboardButton("🎬 تصميم فيديو", callback_data="design_video")]
    ]

    await query.edit_message_text(
        "اختر نوع التصميم",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===== اختيار نوع التصميم =====
async def design_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    user_state[user_id] = query.data
    await query.message.reply_text("✏️ اكتب تفاصيل التصميم الذي تريده")

# ===== معالجة طلبات التصميم =====
async def handle_design_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id not in user_state:
        return

    state = user_state[user_id]

    # التأكد أن الطلب تصميم
    if not state.startswith("design_"):
        return

    data = load_data()
    order_id = len(data["orders"]) + 1

    # خصم عدد من الباقة
    sub = data["subscribers"].get(str(user_id))
    if sub is None or sub["remaining"] <= 0:
        await update.message.reply_text("❌ انتهت تصاميم باقتك، اشترك مرة أخرى")
        del user_state[user_id]
        return

    sub["remaining"] -= 1

    # حفظ الطلب
    order = {
        "id": order_id,
        "user": user_id,
        "type": state.replace("design_", ""),
        "text": text,
        "status": "pending"
    }
    data["orders"].append(order)
    save_data(data)

    # إشعار الأدمن
    for admin in data["admins"]:
        try:
            await context.bot.send_message(
                admin,
                f"""
📥 طلب تصميم جديد

الطلب: {order_id}
المستخدم: {user_id}
النوع: {state.replace('design_','')}

التفاصيل:
{text}
"""
            )
        except:
            continue

    await update.message.reply_text("✅ تم إرسال طلبك")
    del user_state[user_id]

# main_part9.py
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from main_part1 import load_data, save_data, user_state

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

    await query.edit_message_text(
        "اختر طريقة الدفع ثم أرسل صورة الإشعار",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===== طلب إرسال صورة الإشعار =====
async def ask_payment_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_state[user_id] = "waiting_payment_photo"
    await query.message.reply_text("📸 أرسل صورة إشعار الدفع الآن")

# ===== معالجة صورة الإشعار =====
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_state:
        return
    if user_state[user_id] != "waiting_payment_photo":
        return

    photo_file_id = update.message.photo[-1].file_id
    data = load_data()
    payment_id = str(len(data["pending_payments"]) + 1)
    data["pending_payments"][payment_id] = {"user": user_id, "photo": photo_file_id}
    save_data(data)
    del user_state[user_id]

    # زر قبول أو رفض الدفع للأدمن
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ قبول", callback_data=f"accept_payment_{payment_id}"),
            InlineKeyboardButton("❌ رفض", callback_data=f"reject_payment_{payment_id}")
        ]
    ])

    for admin in data["admins"]:
        try:
            await context.bot.send_photo(
                admin,
                photo=photo_file_id,
                caption=f"💳 طلب شحن رصيد\nالمستخدم: {user_id}\nرقم الطلب: {payment_id}",
                reply_markup=keyboard
            )
        except:
            continue

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
    await query.message.reply_text("اكتب مبلغ الشحن ليتم إضافته إلى رصيد المستخدم")

# ===== تحديث الرصيد بعد قبول الدفع =====
async def handle_text_for_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if user_id not in user_state:
        return

    state = user_state[user_id]
    if not state.startswith("add_balance"):
        return

    parts = state.split("_")
    target_user = parts[2]
    payment_id = parts[3]

    try:
        amount = int(text)
    except:
        await update.message.reply_text("❌ المبلغ غير صحيح")
        return

    data = load_data()
    # إضافة الرصيد للمستخدم
    data["wallet"][target_user] = data["wallet"].get(target_user, 0) + amount
    # خصم للأدمن إذا حاب (محفظة البوت)
    data["admin_wallet"] += 0  # يمكن تغييرها لو تريد نسبة
    # إزالة الدفع المعلق
    data["pending_payments"].pop(payment_id, None)
    save_data(data)

    await update.message.reply_text(f"✅ تم إضافة {amount} ليرة إلى رصيد المستخدم")

    # إشعار للمستخدم
    try:
        await context.bot.send_message(target_user, f"💰 تم شحن {amount} ل.س إلى رصيدك")
    except:
        pass

    del user_state[user_id]

# main_part10.py
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from main_part1 import load_data, save_data, user_state

# ===== قائمة الاشتراكات =====
async def subscriptions_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = load_data()

    keyboard = []
    for name, info in data["subscriptions"].items():
        price = info["price"]
        count = info["count"]
        keyboard.append([
            InlineKeyboardButton(
                f"{name} | {count} تصميم | {price} ل.س",
                callback_data=f"buy_sub_{name}"
            )
        ])

    await query.edit_message_text(
        "اختر الباقة المناسبة",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

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

    # خصم الرصيد من المحفظة
    data["wallet"][str(user_id)] -= price
    data["admin_wallet"] += price

    # تسجيل الاشتراك
    data["subscribers"][str(user_id)] = {
        "package": sub_name,
        "remaining": count
    }

    save_data(data)

    # إشعار المستخدم
    await query.edit_message_text(
        f"✅ تم الاشتراك بنجاح\nالباقة: {sub_name}\nعدد التصاميم: {count}"
    )

    # إشعار الأدمن
    for admin in data["admins"]:
        try:
            await context.bot.send_message(
                admin,
                f"📥 قام المستخدم {user_id} بالاشتراك في باقة {sub_name} بمبلغ {price} ل.س"
            )
        except:
            continue

# ===== قائمة طلب التصميم =====
async def design_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = load_data()

    # التأكد من الاشتراك
    if str(user_id) not in data["subscribers"]:
        await query.edit_message_text("❌ يجب الاشتراك بالباقة أولاً")
        return

    keyboard = [
        [InlineKeyboardButton("🖼 تصميم صورة", callback_data="design_image")],
        [InlineKeyboardButton("🎨 تصميم لوغو", callback_data="design_logo")],
        [InlineKeyboardButton("🎬 تصميم فيديو", callback_data="design_video")]
    ]

    await query.edit_message_text(
        "اختر نوع التصميم",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===== اختيار نوع التصميم =====
async def design_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # حفظ نوع التصميم للمستخدم
    user_state[user_id] = query.data

    await query.message.reply_text(
        "✏️ اكتب تفاصيل التصميم الذي تريده"
    )

# ===== استقبال طلب التصميم ومعالجة الرصيد =====
async def handle_design_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_state:
        return

    state = user_state[user_id]
    if not state.startswith("design_"):
        return

    data = load_data()

    # التأكد من الاشتراك والباقي
    if str(user_id) not in data["subscribers"]:
        await update.message.reply_text("❌ يجب الاشتراك بالباقة أولاً")
        del user_state[user_id]
        return

    sub = data["subscribers"][str(user_id)]
    if sub["remaining"] <= 0:
        await update.message.reply_text("❌ لا توجد تصاميم متبقية في باقتك")
        del user_state[user_id]
        return

    # تسجيل الطلب
    order_id = len(data["orders"]) + 1
    order = {
        "id": order_id,
        "user": user_id,
        "type": state,
        "text": update.message.text,
        "status": "pending"
    }
    data["orders"].append(order)

    # خصم عدد التصميم من الباقة
    sub["remaining"] -= 1

    save_data(data)

    # إشعار الأدمن
    for admin in data["admins"]:
        try:
            await context.bot.send_message(
                admin,
                f"📥 طلب تصميم جديد\nالطلب: {order_id}\nالمستخدم: {user_id}\nالنوع: {state}\nالتفاصيل:\n{update.message.text}"
            )
        except:
            continue

    await update.message.reply_text("✅ تم إرسال طلبك بنجاح")
    del user_state[user_id]

import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes, MessageHandler, filters

DATA_FILE = "data.json"
user_state = {}

def load_data():
    with open(DATA_FILE,"r",encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE,"w",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=4)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    user_id = query.from_user.id

    if user_id not in data["admins"]:
        await query.message.reply_text("❌ أنت لست أدمن")
        return

    keyboard = [
        [InlineKeyboardButton("➕ إضافة باقة",callback_data="add_package")],
        [InlineKeyboardButton("➖ حذف باقة",callback_data="del_package")],
        [InlineKeyboardButton("✏️ تعديل باقة",callback_data="edit_package")],
        [InlineKeyboardButton("➕ إضافة طريقة دفع",callback_data="add_payment")],
        [InlineKeyboardButton("➖ حذف طريقة دفع",callback_data="del_payment")],
        [InlineKeyboardButton("📢 رسالة للجميع",callback_data="broadcast")],
        [InlineKeyboardButton("📊 الإحصائيات",callback_data="stats")],
        [InlineKeyboardButton("👑 إضافة أدمن",callback_data="add_admin")],
        [InlineKeyboardButton("⬅️ رجوع",callback_data="back")]
    ]

    await query.edit_message_text(
        "⚙️ لوحة التحكم",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = load_data()
    action = query.data

    if action in ["add_package","del_package","edit_package",
                  "add_payment","del_payment","broadcast","add_admin"]:
        user_state[user_id] = action
        if action == "add_package":
            await query.message.reply_text(
                "📦 أرسل الباقة الجديدة بالشكل: اسم الباقة | السعر | عدد التصاميم"
            )
        elif action == "del_package":
            await query.message.reply_text(
                "📦 أرسل اسم الباقة المراد حذفها"
            )
        elif action == "edit_package":
            await query.message.reply_text(
                "📦 أرسل تعديل الباقة بالشكل: اسم الباقة | السعر | عدد التصاميم"
            )
        elif action == "add_payment":
            await query.message.reply_text(
                "💳 أرسل طريقة الدفع بالشكل: اسم الطريقة | الرابط أو الكود"
            )
        elif action == "del_payment":
            await query.message.reply_text(
                "💳 أرسل اسم طريقة الدفع المراد حذفها"
            )
        elif action == "broadcast":
            await query.message.reply_text(
                "📢 أرسل الرسالة التي تريد بثها لجميع المستخدمين"
            )
        elif action == "add_admin":
            await query.message.reply_text(
                "👑 أرسل ID المستخدم الذي تريد إضافته كأدمن"
            )

    elif action == "stats":
        users = len(data["users"])
        subs = len(data["subscribers"])
        orders = len(data["orders"])
        admin_balance = data.get("admin_wallet",0)
        text = f"""
📊 إحصائيات البوت

👥 المستخدمين: {users}
💎 المشتركين: {subs}
📦 الطلبات: {orders}
💰 محفظة الأدمن: {admin_balance} ل.س
"""
        await query.edit_message_text(text)

async def handle_admin_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if user_id not in user_state:
        return

    action = user_state[user_id]
    data = load_data()
    try:
        if action == "add_package":
            name,price,count = text.split("|")
            data["subscriptions"][name.strip()] = {
                "price": int(price.strip()),
                "count": int(count.strip())
            }
            save_data(data)
            await update.message.reply_text("✅ تمت إضافة الباقة")
        elif action == "del_package":
            data["subscriptions"].pop(text.strip(),None)
            save_data(data)
            await update.message.reply_text("✅ تم حذف الباقة")
        elif action == "edit_package":
            name,price,count = text.split("|")
            if name.strip() in data["subscriptions"]:
                data["subscriptions"][name.strip()] = {
                    "price": int(price.strip()),
                    "count": int(count.strip())
                }
                save_data(data)
                await update.message.reply_text("✅ تم تعديل الباقة")
            else:
                await update.message.reply_text("❌ الباقة غير موجودة")
        elif action == "add_payment":
            name,link = text.split("|")
            data["payments"][name.strip()] = link.strip()
            save_data(data)
            await update.message.reply_text("✅ تمت إضافة طريقة الدفع")
        elif action == "del_payment":
            data["payments"].pop(text.strip(),None)
            save_data(data)
            await update.message.reply_text("✅ تم حذف طريقة الدفع")
        elif action == "broadcast":
            for u in data["users"]:
                try:
                    await context.bot.send_message(u,text)
                except:
                    continue
            await update.message.reply_text("✅ تم الإرسال")
        elif action == "add_admin":
            data["admins"].append(int(text.strip()))
            save_data(data)
            await update.message.reply_text("✅ تم إضافة أدمن")
    except:
        await update.message.reply_text("❌ الصيغة خطأ")
    del user_state[user_id]

