import json
import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonCommands
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = "8268148633:AAHlcBIaMplGzwlmiZ2w11NCCWy5CA_tbJY"
ADMINS = [1226196443]

DATA_FILE = "data.json"

user_state = {}

# تحميل البيانات
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

# حفظ البيانات
def save_data(data):
    with open(DATA_FILE,"w",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=4)

def main_menu(user_id,data):

    keyboard = [
        [InlineKeyboardButton("💰 رصيدي",callback_data="balance")],
        [InlineKeyboardButton("💳 شحن رصيد",callback_data="deposit")],
        [InlineKeyboardButton("⭐ الاشتراك بالباقة",callback_data="subscribe")],
        [InlineKeyboardButton("🎨 طلب تصميم",callback_data="design")]
    ]

    if user_id in data["admins"]:
        keyboard.append(
            [InlineKeyboardButton("⚙️ لوحة التحكم",callback_data="admin_panel")]
        )

    return InlineKeyboardMarkup(keyboard)

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    data = load_data()

    if user.id not in data["users"]:
        data["users"].append(user.id)
        data["wallet"][str(user.id)] = 0
        save_data(data)

    await update.message.reply_text(
        data["welcome"],
        reply_markup=main_menu(user.id,data)
    )

async def show_balance(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    data = load_data()

    balance = data["wallet"].get(str(user_id),0)

    text = f"""
💰 رصيدك الحالي

{balance} ليرة سورية
"""

    await query.edit_message_text(
        text,
        reply_markup=main_menu(user_id,data)
    )

async def deposit_menu(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = load_data()

    keyboard = []

    for name,link in data["payments"].items():
        keyboard.append(
            [InlineKeyboardButton(name,url=link)]
        )

    keyboard.append(
        [InlineKeyboardButton("📤 إرسال إشعار الدفع",callback_data="send_payment")]
    )

    await query.edit_message_text(
        "اختر طريقة الدفع ثم أرسل صورة الإشعار",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def ask_payment_photo(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    user_state[user_id] = "waiting_payment_photo"

    await query.message.reply_text(
        "📸 أرسل صورة إشعار الدفع الآن"
    )

async def ask_payment_photo(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    user_state[user_id] = "waiting_payment_photo"

    await query.message.reply_text(
        "📸 أرسل صورة إشعار الدفع الآن"
                     )

async def handle_photo(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in user_state:
        return

    state = user_state[user_id]

    if state != "waiting_payment_photo":
        return

    photo = update.message.photo[-1].file_id

    data = load_data()

    payment_id = str(len(data["pending_payments"]) + 1)

    data["pending_payments"][payment_id] = {
        "user": user_id
    }

    save_data(data)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ قبول",callback_data=f"accept_payment_{payment_id}"),
            InlineKeyboardButton("❌ رفض",callback_data=f"reject_payment_{payment_id}")
        ]
    ])

    for admin in data["admins"]:

        await context.bot.send_photo(
            admin,
            photo,
            caption=f"""
💳 طلب شحن رصيد

المستخدم: {user_id}
رقم الطلب: {payment_id}
""",
            reply_markup=keyboard
        )

    await update.message.reply_text(
        "تم إرسال الطلب للأدمن للمراجعة"
    )

    del user_state[user_id]

async def accept_payment(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = load_data()

    payment_id = query.data.split("_")[-1]

    if payment_id not in data["pending_payments"]:
        await query.message.reply_text("الطلب غير موجود")
        return

    user_id = data["pending_payments"][payment_id]["user"]

    user_state[query.from_user.id] = f"add_balance_{user_id}_{payment_id}"

    await query.message.reply_text(
        "اكتب مبلغ الشحن"
    )

async def handle_text(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in user_state:
        return

    state = user_state[user_id]

    if state.startswith("add_balance"):

        data = load_data()

        parts = state.split("_")

        target_user = parts[2]
        payment_id = parts[3]

        amount = int(update.message.text)

        data["wallet"][target_user] += amount

        del data["pending_payments"][payment_id]

        save_data(data)

        await update.message.reply_text(
            "تم إضافة الرصيد بنجاح"
        )

        try:
            await context.bot.send_message(
                target_user,
                f"تم شحن {amount} ليرة إلى رصيدك"
            )
        except:
            pass

        del user_state[user_id]

async def subscriptions_menu(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = load_data()

    keyboard = []

    for name,info in data["subscriptions"].items():

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

async def buy_subscription(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = load_data()

    sub_name = query.data.replace("buy_sub_","")

    sub = data["subscriptions"][sub_name]

    price = sub["price"]
    count = sub["count"]

    balance = data["wallet"].get(str(user_id),0)

    if balance < price:

        await query.edit_message_text(
            "❌ رصيدك غير كافي"
        )
        return

    data["wallet"][str(user_id)] -= price
    data["admin_wallet"] += price

    data["subscribers"][str(user_id)] = {
        "package": sub_name,
        "remaining": count
    }

    save_data(data)

    await query.edit_message_text(
        f"""
✅ تم الاشتراك بنجاح

الباقة: {sub_name}
عدد التصاميم: {count}
"""
        )

async def design_menu(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = load_data()

    if str(user_id) not in data["subscribers"]:

        await query.edit_message_text(
            "❌ يجب الاشتراك بالباقة أولاً"
        )
        return

    keyboard = [

        [InlineKeyboardButton("🖼 تصميم صورة",callback_data="design_image")],

        [InlineKeyboardButton("🎨 تصميم لوغو",callback_data="design_logo")],

        [InlineKeyboardButton("🎬 تصميم فيديو",callback_data="design_video")]

    ]

    await query.edit_message_text(
        "اختر نوع التصميم",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def design_type(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    user_state[user_id] = query.data

    await query.message.reply_text(
        "اكتب تفاصيل التصميم الذي تريده"
    )

async def handle_design_text(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in user_state:
        return

    state = user_state[user_id]

    if not state.startswith("design_"):
        return

    data = load_data()

    order_id = len(data["orders"]) + 1

    order = {
        "id":order_id,
        "user":user_id,
        "type":state,
        "text":update.message.text,
        "status":"pending"
    }

    data["orders"].append(order)

    sub = data["subscribers"][str(user_id)]
    sub["remaining"] -= 1

    save_data(data)

    for admin in data["admins"]:

        await context.bot.send_message(
            admin,
            f"""
📥 طلب تصميم جديد

الطلب: {order_id}
المستخدم: {user_id}
النوع: {state}

التفاصيل:
{update.message.text}
"""
        )

    await update.message.reply_text(
        "✅ تم إرسال طلبك"
    )

    del user_state[user_id]

async def admin_panel(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = load_data()

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

async def show_stats(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = load_data()

    users = len(data["users"])
    subs = len(data["subscribers"])
    orders = len(data["orders"])
    admin_balance = data["admin_wallet"]

    text = f"""
📊 إحصائيات البوت

👥 المستخدمين: {users}
💎 المشتركين: {subs}
📦 الطلبات: {orders}
💰 محفظة الأدمن: {admin_balance} ل.س
"""
    await query.edit_message_text(text)

async def broadcast_message(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_state[user_id] = "broadcast"

    await query.message.reply_text(
        "اكتب الرسالة التي تريد إرسالها لجميع المستخدمين"
    )

async def manage_packages(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    action = query.data

    user_state[user_id] = action

    if action == "add_package":
        await query.message.reply_text(
            "اكتب الباقة الجديدة بالشكل: اسم الباقة | السعر | عدد التصاميم"
        )
    elif action == "del_package":
        await query.message.reply_text(
            "اكتب اسم الباقة المراد حذفها"
        )
    elif action == "edit_package":
        await query.message.reply_text(
            "اكتب تعديل الباقة بالشكل: اسم الباقة | السعر الجديد | عدد التصاميم"
        )

async def manage_payments(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    action = query.data

    user_state[user_id] = action

    if action == "add_payment":
        await query.message.reply_text(
            "اكتب طريقة الدفع بالشكل: اسم الطريقة | الرابط أو الكود"
        )
    elif action == "del_payment":
        await query.message.reply_text(
            "اكتب اسم طريقة الدفع المراد حذفها"
        )

async def add_admin(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_state[query.from_user.id] = "add_admin"

    await query.message.reply_text(
        "اكتب ID المستخدم الذي تريد إضافته كأدمن"
    )

from telegram.ext import ApplicationBuilder

async def callback_handler(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    data = load_data()
    user_id = query.from_user.id

    # القوائم الرئيسية
    if query.data == "balance":
        await show_balance(update,context)
    elif query.data == "deposit":
        await deposit_menu(update,context)
    elif query.data == "send_payment":
        await ask_payment_photo(update,context)
    elif query.data.startswith("accept_payment"):
        await accept_payment(update,context)
    elif query.data.startswith("buy_sub_"):
        await buy_subscription(update,context)
    elif query.data == "subscribe":
        await subscriptions_menu(update,context)
    elif query.data == "design":
        await design_menu(update,context)
    elif query.data.startswith("design_"):
        await design_type(update,context)
    elif query.data == "admin_panel":
        await admin_panel(update,context)
    elif query.data == "stats":
        await show_stats(update,context)
    elif query.data == "broadcast":
        await broadcast_message(update,context)
    elif query.data in ["add_package","del_package","edit_package"]:
        await manage_packages(update,context)
    elif query.data in ["add_payment","del_payment"]:
        await manage_payments(update,context)
    elif query.data == "add_admin":
        await add_admin(update,context)
    elif query.data == "back":
        await query.edit_message_text(
            data["welcome"],
            reply_markup=main_menu(user_id,data)
        )


async def text_handler_full(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    text = update.message.text

    if user_id in user_state:

        state = user_state[user_id]
        data = load_data()

        try:
            # البث
            if state == "broadcast":
                for u in data["users"]:
                    try:
                        await context.bot.send_message(u,text)
                    except:
                        continue
                await update.message.reply_text("تم الإرسال")
            
            # إدارة الباقات
            elif state == "add_package":
                name,price,count = text.split("|")
                data["subscriptions"][name.strip()] = {
                    "price":int(price.strip()),
                    "count":int(count.strip())
                }
                save_data(data)
                await update.message.reply_text("تمت إضافة الباقة")

            elif state == "del_package":
                data["subscriptions"].pop(text.strip(),None)
                save_data(data)
                await update.message.reply_text("تم حذف الباقة")

            elif state == "edit_package":
                name,price,count = text.split("|")
                if name.strip() in data["subscriptions"]:
                    data["subscriptions"][name.strip()] = {
                        "price":int(price.strip()),
                        "count":int(count.strip())
                    }
                    save_data(data)
                    await update.message.reply_text("تم تعديل الباقة")
                else:
                    await update.message.reply_text("❌ الباقة غير موجودة")

            # إدارة طرق الدفع
            elif state == "add_payment":
                name,link = text.split("|")
                data["payments"][name.strip()] = link.strip()
                save_data(data)
                await update.message.reply_text("تمت إضافة طريقة الدفع")

            elif state == "del_payment":
                data["payments"].pop(text.strip(),None)
                save_data(data)
                await update.message.reply_text("تم حذف طريقة الدفع")

            # إضافة أدمن
            elif state == "add_admin":
                data["admins"].append(int(text.strip()))
                save_data(data)
                await update.message.reply_text("تمت إضافة أدمن")

        except:
            await update.message.reply_text("❌ الصيغة خطأ")

        del user_state[user_id]

    # استقبال تصميم المستخدم
    await handle_design_text(update,context)

    # إضافة رصيد بعد قبول الدفع
    if state.startswith("add_balance"):
        await handle_text(update,context)

async def set_menu(app):
    await app.bot.set_my_commands([("start","بدء البوت")])
    await app.bot.set_chat_menu_button(menu_button=MenuButtonCommands())

app = Application.builder().token(TOKEN).build()

app.post_init = set_menu

# Handlers
app.add_handler(CommandHandler("start",start))
app.add_handler(CallbackQueryHandler(callback_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,text_handler_full))
app.add_handler(MessageHandler(filters.PHOTO,handle_photo))

print("Bot running...")

app.run_polling()

