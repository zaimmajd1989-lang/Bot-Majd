# ==============================
# DAVINCI DESIGN BOT
# PART 1
# ==============================

import json
import os
import logging
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# ==============================
# BOT SETTINGS
# ==============================

TOKEN = "8520525369:AAGhpShBwAQYROXqkPXvm_1SVeSAvjuy3kc"

BOT_NAME = "Design Bot DaVinci"

CURRENCY = "ليرة سورية"

ADMINS = [1226196443]  # ضع ايدي الادمن هنا

DATA_FILE = "data.json"

user_state = {}

# ==============================
# LOGGING
# ==============================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ==============================
# DATABASE
# ==============================


def create_database():

    if not os.path.exists(DATA_FILE):

        data = {

            "users": [],

            "admins": ADMINS,

            "wallet": {},

            "admin_wallet": 0,

            "subscriptions": {

                "باقة10": {
                    "price": 10000,
                    "count": 10
                },

                "باقة30": {
                    "price": 25000,
                    "count": 30
                },

                "باقة50": {
                    "price": 40000,
                    "count": 50
                }

            },

            "subscribers": {},

            "orders": [],

            "payments": [],

            "payment_methods": [

                {
                    "name": "تحويل يدوي",
                    "text": "أرسل صورة إثبات الدفع"
                }

            ],

            "settings": {

                "currency": CURRENCY,
                "bot_name": BOT_NAME

            }

        }

        with open(DATA_FILE, "w", encoding="utf-8") as f:

            json.dump(data, f, ensure_ascii=False, indent=4)


def load_data():

    with open(DATA_FILE, "r", encoding="utf-8") as f:

        return json.load(f)


def save_data(data):

    with open(DATA_FILE, "w", encoding="utf-8") as f:

        json.dump(data, f, ensure_ascii=False, indent=4)


# ==============================
# USER REGISTER
# ==============================


def register_user(user_id, data):

    if user_id not in data["users"]:

        data["users"].append(user_id)

        data["wallet"][str(user_id)] = 0

        save_data(data)


# ==============================
# MAIN MENU
# ==============================


def main_menu(user_id, data):

    keyboard = [

        [InlineKeyboardButton("💰 رصيدي", callback_data="balance")],

        [InlineKeyboardButton("💳 شحن رصيد", callback_data="deposit")],

        [InlineKeyboardButton("⭐ الاشتراك بالباقة", callback_data="subscribe")],

        [InlineKeyboardButton("🎨 طلب تصميم", callback_data="design")],

        [InlineKeyboardButton("📦 طلباتي", callback_data="my_orders")],

        [InlineKeyboardButton("📞 الدعم", callback_data="support")]

    ]

    if user_id in data["admins"]:

        keyboard.append([InlineKeyboardButton("⚙️ لوحة التحكم", callback_data="admin_panel")])

    return InlineKeyboardMarkup(keyboard)


# ==============================
# START COMMAND
# ==============================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    data = load_data()

    register_user(user.id, data)

    text = f"""
👋 أهلاً بك في {BOT_NAME}

بوت متخصص في طلب التصاميم.

يمكنك من خلاله:

🎨 طلب تصميم
💰 شحن الرصيد
⭐ الاشتراك بالباقة

اختر من القائمة:
"""

    await update.message.reply_text(

        text,

        reply_markup=main_menu(user.id, data)

    )


# ==============================
# BALANCE
# ==============================


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    data = load_data()

    balance = data["wallet"].get(str(user_id), 0)

    currency = data["settings"]["currency"]

    text = f"""

💰 رصيدك الحالي:

{balance} {currency}

"""

    await query.edit_message_text(

        text,

        reply_markup=main_menu(user_id, data)

    )


# ==============================
# SUPPORT
# ==============================


async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    user_state[user_id] = "support"

    await query.message.reply_text(

        "📞 اكتب رسالتك للدعم الآن"

    )


# ==============================
# USER MESSAGES
# ==============================


async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    text = update.message.text

    data = load_data()

    if user_state.get(user_id) == "support":

        for admin in data["admins"]:

            await context.bot.send_message(

                admin,

                f"""

📩 رسالة دعم جديدة

المستخدم:
{user_id}

الرسالة:
{text}

"""

            )

        await update.message.reply_text(

            "✅ تم إرسال رسالتك للدعم"

        )

        user_state[user_id] = None


# ==============================
# HANDLERS
# ==============================


def register_handlers(app):

    app.add_handler(CommandHandler("start", start))

    app.add_handler(CallbackQueryHandler(balance, pattern="balance"))

    app.add_handler(CallbackQueryHandler(support, pattern="support"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))


# ==============================
# RUN BOT
# ==============================


def main():

    create_database()

    app = Application.builder().token(TOKEN).build()

    register_handlers(app)

    print("Davinci Design Bot Running...")

    app.run_polling()


if __name__ == "__main__":

    main()
    
# ==============================
# DAVINCI DESIGN BOT
# PART 2 - DEPOSIT SYSTEM
# ==============================


# ==============================
# DEPOSIT MENU
# ==============================

async def deposit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = load_data()

    keyboard = []

    for i, method in enumerate(data["payment_methods"]):

        keyboard.append([
            InlineKeyboardButton(
                method["name"],
                callback_data=f"deposit_method_{i}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton("⬅️ رجوع", callback_data="back_main")
    ])

    await query.edit_message_text(

        "💳 اختر طريقة الدفع:",

        reply_markup=InlineKeyboardMarkup(keyboard)

    )


# ==============================
# CHOOSE PAYMENT METHOD
# ==============================

async def choose_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = load_data()

    user_id = query.from_user.id

    index = int(query.data.split("_")[-1])

    method = data["payment_methods"][index]

    user_state[user_id] = {

        "action": "send_payment_proof",
        "method": index

    }

    await query.edit_message_text(

        f"""
💳 طريقة الدفع:

{method['name']}

{method['text']}

📷 أرسل الآن صورة إثبات الدفع
"""

    )


# ==============================
# RECEIVE PAYMENT PROOF
# ==============================

async def receive_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    state = user_state.get(user_id)

    if not state:
        return

    if state.get("action") != "send_payment_proof":
        return

    if not update.message.photo:
        return

    data = load_data()

    photo = update.message.photo[-1].file_id

    payment_id = len(data["payments"]) + 1

    payment = {

        "id": payment_id,

        "user": user_id,

        "photo": photo,

        "status": "pending",

        "date": str(datetime.now())

    }

    data["payments"].append(payment)

    save_data(data)

    keyboard = [

        [

            InlineKeyboardButton(
                "✅ قبول",
                callback_data=f"accept_payment_{payment_id}"
            ),

            InlineKeyboardButton(
                "❌ رفض",
                callback_data=f"reject_payment_{payment_id}"
            )

        ]

    ]

    for admin in data["admins"]:

        await context.bot.send_photo(

            admin,

            photo,

            caption=f"""
💳 طلب شحن رصيد جديد

ID: {payment_id}

المستخدم:
{user_id}

الحالة:
معلق
""",

            reply_markup=InlineKeyboardMarkup(keyboard)

        )

    await update.message.reply_text(

        "⏳ تم إرسال إثبات الدفع للإدارة للمراجعة."

    )

    user_state[user_id] = None


# ==============================
# ACCEPT PAYMENT
# ==============================

async def accept_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    admin_id = query.from_user.id

    data = load_data()

    if admin_id not in data["admins"]:
        return

    payment_id = int(query.data.split("_")[-1])

    payment = next(
        (p for p in data["payments"] if p["id"] == payment_id),
        None
    )

    if not payment:
        return

    if payment["status"] != "pending":
        return

    user_id = payment["user"]

    amount = 10000  # قيمة افتراضية يمكن تعديلها لاحقاً

    data["wallet"][str(user_id)] += amount

    data["admin_wallet"] += amount

    payment["status"] = "accepted"

    save_data(data)

    await context.bot.send_message(

        user_id,

        f"""
✅ تم قبول الدفع

تم إضافة:

{amount} {data["settings"]["currency"]}

إلى رصيدك.
"""

    )

    await query.edit_message_caption(

        caption=f"""
✅ تم قبول الدفع

ID: {payment_id}

المستخدم:
{user_id}
"""

    )


# ==============================
# REJECT PAYMENT
# ==============================

async def reject_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    admin_id = query.from_user.id

    data = load_data()

    if admin_id not in data["admins"]:
        return

    payment_id = int(query.data.split("_")[-1])

    payment = next(
        (p for p in data["payments"] if p["id"] == payment_id),
        None
    )

    if not payment:
        return

    payment["status"] = "rejected"

    save_data(data)

    await context.bot.send_message(

        payment["user"],

        "❌ تم رفض طلب الشحن."

    )

    await query.edit_message_caption(

        caption="❌ تم رفض الدفع"

    )


# ==============================
# BACK MAIN
# ==============================

async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    data = load_data()

    await query.edit_message_text(

        "القائمة الرئيسية:",

        reply_markup=main_menu(user_id, data)

    )


# ==============================
# ADD HANDLERS PART 2
# ==============================

def register_deposit_handlers(app):

    app.add_handler(
        CallbackQueryHandler(deposit_menu, pattern="deposit")
    )

    app.add_handler(
        CallbackQueryHandler(choose_payment_method, pattern="deposit_method_")
    )

    app.add_handler(
        CallbackQueryHandler(accept_payment, pattern="accept_payment_")
    )

    app.add_handler(
        CallbackQueryHandler(reject_payment, pattern="reject_payment_")
    )

    app.add_handler(
        CallbackQueryHandler(back_main, pattern="back_main")
    )

    app.add_handler(
        MessageHandler(filters.PHOTO, receive_payment_proof)
    )
    
# ==============================
# DAVINCI DESIGN BOT
# PART 3 - SUBSCRIPTIONS
# ==============================


# ==============================
# SUBSCRIPTIONS MENU
# ==============================

async def subscriptions_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = load_data()

    keyboard = []

    for name, info in data["subscriptions"].items():

        text = f"{name} | {info['count']} تصميم | {info['price']} {data['settings']['currency']}"

        keyboard.append([
            InlineKeyboardButton(
                text,
                callback_data=f"buy_sub_{name}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton("⬅️ رجوع", callback_data="back_main")
    ])

    await query.edit_message_text(

        "⭐ اختر الباقة:",

        reply_markup=InlineKeyboardMarkup(keyboard)

    )


# ==============================
# BUY SUBSCRIPTION
# ==============================

async def buy_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    data = load_data()

    sub_name = query.data.replace("buy_sub_", "")

    if sub_name not in data["subscriptions"]:
        return

    sub = data["subscriptions"][sub_name]

    price = sub["price"]

    balance = data["wallet"].get(str(user_id), 0)

    if balance < price:

        await query.edit_message_text(
            "❌ رصيدك غير كافي لشراء هذه الباقة."
        )

        return

    data["wallet"][str(user_id)] -= price

    data["subscribers"][str(user_id)] = {

        "package": sub_name,

        "remaining": sub["count"],

        "date": str(datetime.now())

    }

    data["admin_wallet"] += price

    save_data(data)

    await query.edit_message_text(

        f"""
✅ تم شراء الباقة بنجاح

📦 الباقة: {sub_name}

🎨 عدد التصاميم: {sub['count']}
"""

    )


# ==============================
# USER SUBSCRIPTION STATUS
# ==============================

async def my_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    data = load_data()

    sub = data["subscribers"].get(str(user_id))

    if not sub:

        await query.edit_message_text(

            "❌ ليس لديك اشتراك حالياً."

        )

        return

    await query.edit_message_text(

        f"""
⭐ اشتراكك الحالي

📦 الباقة:
{sub['package']}

🎨 التصاميم المتبقية:
{sub['remaining']}
"""

    )


# ==============================
# CHECK USER CAN DESIGN
# ==============================

def check_user_design(user_id, data):

    sub = data["subscribers"].get(str(user_id))

    if not sub:
        return False

    if sub["remaining"] <= 0:
        return False

    return True


# ==============================
# USE DESIGN FROM PACKAGE
# ==============================

def use_design(user_id, data):

    sub = data["subscribers"].get(str(user_id))

    if not sub:
        return False

    if sub["remaining"] <= 0:
        return False

    sub["remaining"] -= 1

    save_data(data)

    return True


# ==============================
# ADD HANDLERS PART 3
# ==============================

def register_subscription_handlers(app):

    app.add_handler(
        CallbackQueryHandler(subscriptions_menu, pattern="subscribe")
    )

    app.add_handler(
        CallbackQueryHandler(buy_subscription, pattern="buy_sub_")
    )

    app.add_handler(
        CallbackQueryHandler(my_subscription, pattern="my_subscription")
)

# ==============================
# CREATE DESIGN REQUEST
# ==============================

async def create_design(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_state[user_id] = {"action": "send_design_request"}
    await query.edit_message_text(
        "🎨 أرسل وصف التصميم الذي ترغب به:"
    )


# ==============================
# RECEIVE DESIGN REQUEST
# ==============================

async def receive_design_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = user_state.get(user_id)
    if not state or state.get("action") != "send_design_request":
        return
    text = update.message.text
    data = load_data()
    design_id = len(data["designs"]) + 1
    design = {
        "id": design_id,
        "user": user_id,
        "text": text,
        "status": "pending",
        "date": str(datetime.now())
    }
    data["designs"].append(design)
    save_data(data)
    keyboard = [
        [
            InlineKeyboardButton("✅ قبول", callback_data=f"accept_design_{design_id}"),
            InlineKeyboardButton("❌ رفض", callback_data=f"reject_design_{design_id}")
        ]
    ]
    for admin in data["admins"]:
        await context.bot.send_message(
            admin,
            f"🎨 طلب تصميم جديد\nID: {design_id}\nالمستخدم: {user_id}\nالوصف: {text}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    await update.message.reply_text("⏳ تم إرسال طلب التصميم للإدارة للمراجعة.")
    user_state[user_id] = None


# ==============================
# ACCEPT DESIGN
# ==============================

async def accept_design(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    admin_id = query.from_user.id
    data = load_data()
    if admin_id not in data["admins"]:
        return
    design_id = int(query.data.split("_")[-1])
    design = next((d for d in data["designs"] if d["id"] == design_id), None)
    if not design or design["status"] != "pending":
        return
    design["status"] = "accepted"
    save_data(data)
    await context.bot.send_message(
        design["user"],
        f"✅ تم قبول طلب التصميم ID: {design_id}، سيتم تنفيذه قريبًا."
    )
    await query.edit_message_text(f"✅ تم قبول التصميم ID: {design_id}")


# ==============================
# REJECT DESIGN
# ==============================

async def reject_design(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    admin_id = query.from_user.id
    data = load_data()
    if admin_id not in data["admins"]:
        return
    design_id = int(query.data.split("_")[-1])
    design = next((d for d in data["designs"] if d["id"] == design_id), None)
    if not design:
        return
    design["status"] = "rejected"
    save_data(data)
    await context.bot.send_message(
        design["user"],
        f"❌ تم رفض طلب التصميم ID: {design_id}."
    )
    await query.edit_message_text(f"❌ تم رفض التصميم ID: {design_id}")


# ==============================
# ADD HANDLERS PART 4
# ==============================

def register_design_handlers(app):
    app.add_handler(CallbackQueryHandler(create_design, pattern="create_design"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_design_request))
    app.add_handler(CallbackQueryHandler(accept_design, pattern="accept_design_"))
    app.add_handler(CallbackQueryHandler(reject_design, pattern="reject_design_"))

# ==============================
# ADMIN DASHBOARD
# ==============================

async def admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = load_data()
    if user_id not in data["admins"]:
        await query.edit_message_text("🚫 أنت لست من الإدارة.")
        return
    keyboard = [
        [InlineKeyboardButton("💳 إدارة المدفوعات", callback_data="view_payments")],
        [InlineKeyboardButton("💎 إدارة الاشتراكات", callback_data="view_subscriptions")],
        [InlineKeyboardButton("🎨 إدارة التصميمات", callback_data="view_designs")],
        [InlineKeyboardButton("⚙️ إعدادات البوت", callback_data="bot_settings")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="back_main")]
    ]
    await query.edit_message_text("🛠 لوحة تحكم الإدارة:", reply_markup=InlineKeyboardMarkup(keyboard))


# ==============================
# BOT SETTINGS
# ==============================

async def bot_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    keyboard = [
        [InlineKeyboardButton(f"💱 العملة الحالية: {data['settings']['currency']}", callback_data="change_currency")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="admin_dashboard")]
    ]
    await query.edit_message_text("⚙️ إعدادات البوت:", reply_markup=InlineKeyboardMarkup(keyboard))


# ==============================
# CHANGE CURRENCY
# ==============================

async def change_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = load_data()
    user_state[user_id] = {"action": "change_currency"}
    await query.edit_message_text("💱 أرسل رمز العملة الجديد (مثلاً: USD, SYP, BTC):")


# ==============================
# SAVE NEW CURRENCY
# ==============================

async def save_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = user_state.get(user_id)
    if not state or state.get("action") != "change_currency":
        return
    currency = update.message.text.upper()
    data = load_data()
    data["settings"]["currency"] = currency
    save_data(data)
    await update.message.reply_text(f"✅ تم تغيير العملة إلى: {currency}")
    user_state[user_id] = None


# ==============================
# ADD HANDLERS PART 5
# ==============================

def register_admin_handlers(app):
    app.add_handler(CallbackQueryHandler(admin_dashboard, pattern="admin"))
    app.add_handler(CallbackQueryHandler(bot_settings, pattern="bot_settings"))
    app.add_handler(CallbackQueryHandler(change_currency, pattern="change_currency"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_currency))

# ==============================
# SUBSCRIPTION MENU
# ==============================

async def subscription_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    keyboard = []
    for i, plan in enumerate(data["subscriptions"]):
        keyboard.append([
            InlineKeyboardButton(
                f"{plan['name']} - {plan['price']} {data['settings']['currency']}",
                callback_data=f"subscribe_{i}"
            )
        ])
    keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back_main")])
    await query.edit_message_text("💎 اختر الاشتراك:", reply_markup=InlineKeyboardMarkup(keyboard))


# ==============================
# CHOOSE SUBSCRIPTION PLAN
# ==============================

async def choose_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    user_id = query.from_user.id
    index = int(query.data.split("_")[-1])
    plan = data["subscriptions"][index]
    user_state[user_id] = {"action": "subscribe", "plan": index}
    await query.edit_message_text(
        f"💎 اشتراكك:\n{plan['name']}\nالسعر: {plan['price']} {data['settings']['currency']}\n\n📷 أرسل إثبات الدفع أو أكمل الدفع."
    )


# ==============================
# ACTIVATE SUBSCRIPTION
# ==============================

async def activate_subscription(user_id, plan_index):
    data = load_data()
    plan = data["subscriptions"][plan_index]
    user_sub = {
        "plan": plan["name"],
        "expiry": str(datetime.now() + timedelta(days=plan["duration_days"]))
    }
    data["user_subscriptions"][str(user_id)] = user_sub
    save_data(data)

# ==============================
# SEND BROADCAST TO USERS
# ==============================

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    user_id = query.from_user.id
    if user_id not in data["admins"]:
        await query.edit_message_text("🚫 أنت لست من الإدارة.")
        return
    user_state[user_id] = {"action": "broadcast"}
    await query.edit_message_text("📢 أرسل الرسالة لجميع المستخدمين:")


# ==============================
# RECEIVE BROADCAST
# ==============================

async def receive_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = user_state.get(user_id)
    if not state or state.get("action") != "broadcast":
        return
    message_text = update.message.text
    data = load_data()
    for user in data["wallet"].keys():
        try:
            await context.bot.send_message(int(user), f"📢 رسالة من الإدارة:\n\n{message_text}")
        except:
            pass
    await update.message.reply_text("✅ تم إرسال الرسالة لجميع المستخدمين.")
    user_state[user_id] = None


# ==============================
# ADD HANDLERS PART 6 & 7
# ==============================

def register_subscription_handlers(app):
    app.add_handler(CallbackQueryHandler(subscription_menu, pattern="subscription"))
    app.add_handler(CallbackQueryHandler(choose_subscription, pattern="subscribe_"))

def register_misc_handlers(app):
    app.add_handler(CallbackQueryHandler(broadcast_message, pattern="broadcast"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_broadcast))

# ==============================
# USER REWARDS AND LEVELS
# ==============================

def calculate_level(points):
    # كل 100 نقطة = مستوى جديد
    return points // 100

async def show_user_rewards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    user_points = data["user_points"].get(str(user_id), 0)
    level = calculate_level(user_points)

    await update.message.reply_text(
        f"🎖 نقاطك الحالية: {user_points}\n"
        f"🏆 مستواك: {level}"
    )

async def add_points(user_id, points):
    data = load_data()
    current = data["user_points"].get(str(user_id), 0)
    data["user_points"][str(user_id)] = current + points
    save_data(data)

# ==============================
# HANDLERS PART 8
# ==============================

def register_rewards_handlers(app):
    app.add_handler(CommandHandler("rewards", show_user_rewards))

# ==============================
# CRYPTO PAYMENTS AND ADMIN STATS
# ==============================

async def crypto_deposit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    
    keyboard = []
    for i, method in enumerate(data["crypto_methods"]):
        keyboard.append([InlineKeyboardButton(method["name"], callback_data=f"crypto_{i}")])
    keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back_main")])

    await query.edit_message_text(
        "💰 اختر عملة رقمية للشحن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_user.id
    data = load_data()
    if admin_id not in data["admins"]:
        return

    total_users = len(data["wallet"])
    total_payments = len(data["payments"])
    total_crypto = sum(p.get("amount", 0) for p in data.get("crypto_payments", []))

    await update.message.reply_text(
        f"📊 إحصائيات الإدارة:\n"
        f"عدد المستخدمين: {total_users}\n"
        f"عدد طلبات الشحن: {total_payments}\n"
        f"إجمالي الشحن بالعملات الرقمية: {total_crypto}"
    )

# ==============================
# HANDLERS PART 9
# ==============================

def register_crypto_stats_handlers(app):
    app.add_handler(CallbackQueryHandler(crypto_deposit_menu, pattern="crypto_"))
    app.add_handler(CommandHandler("admin_stats", show_admin_stats))

# ==============================
# USER WITHDRAWAL SYSTEM
# ==============================

async def withdrawal_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = load_data()

    balance = data["wallet"].get(str(user_id), 0)

    await query.edit_message_text(
        f"💸 رصيدك الحالي: {balance} {data['settings']['currency']}\n"
        "📤 أدخل المبلغ الذي تريد سحبه:"
    )

async def process_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    text = update.message.text

    try:
        amount = int(text)
    except ValueError:
        await update.message.reply_text("❌ أدخل رقم صالح فقط.")
        return

    balance = data["wallet"].get(str(user_id), 0)
    if amount > balance:
        await update.message.reply_text("❌ المبلغ أكبر من رصيدك.")
        return

    withdrawal_id = len(data.get("withdrawals", [])) + 1
    withdrawal = {
        "id": withdrawal_id,
        "user": user_id,
        "amount": amount,
        "status": "pending",
        "date": str(datetime.now())
    }

    if "withdrawals" not in data:
        data["withdrawals"] = []

    data["withdrawals"].append(withdrawal)
    save_data(data)

    # Notify admins
    keyboard = [
        [
            InlineKeyboardButton("✅ قبول", callback_data=f"accept_withdraw_{withdrawal_id}"),
            InlineKeyboardButton("❌ رفض", callback_data=f"reject_withdraw_{withdrawal_id}")
        ]
    ]
    for admin in data["admins"]:
        await context.bot.send_message(
            admin,
            f"💸 طلب سحب جديد\nID: {withdrawal_id}\nالمستخدم: {user_id}\nالمبلغ: {amount}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    await update.message.reply_text("⏳ تم إرسال طلب السحب للإدارة.")


# ==============================
# ADMIN HANDLERS FOR WITHDRAWALS
# ==============================

async def accept_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    admin_id = query.from_user.id
    data = load_data()
    if admin_id not in data["admins"]:
        return

    withdrawal_id = int(query.data.split("_")[-1])
    withdrawal = next((w for w in data["withdrawals"] if w["id"] == withdrawal_id), None)
    if not withdrawal or withdrawal["status"] != "pending":
        return

    user_id = withdrawal["user"]
    amount = withdrawal["amount"]

    data["wallet"][str(user_id)] -= amount
    withdrawal["status"] = "accepted"
    save_data(data)

    await context.bot.send_message(user_id, f"✅ تم قبول طلب السحب، المبلغ {amount} {data['settings']['currency']} تم خصمه من رصيدك.")
    await query.edit_message_text(f"✅ تم قبول السحب ID: {withdrawal_id}")


async def reject_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    admin_id = query.from_user.id
    data = load_data()
    if admin_id not in data["admins"]:
        return

    withdrawal_id = int(query.data.split("_")[-1])
    withdrawal = next((w for w in data["withdrawals"] if w["id"] == withdrawal_id), None)
    if not withdrawal or withdrawal["status"] != "pending":
        return

    withdrawal["status"] = "rejected"
    save_data(data)
    await context.bot.send_message(withdrawal["user"], "❌ تم رفض طلب السحب.")
    await query.edit_message_text(f"❌ تم رفض السحب ID: {withdrawal_id}")


# ==============================
# ADVANCED CONTROL PANEL
# ==============================

async def control_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_user.id
    data = load_data()
    if admin_id not in data["admins"]:
        return

    keyboard = [
        [InlineKeyboardButton("💳 إدارة طرق الدفع", callback_data="panel_payment")],
        [InlineKeyboardButton("💰 إدارة العملات الرقمية", callback_data="panel_crypto")],
        [InlineKeyboardButton("🎁 تعديل المكافآت والنقاط", callback_data="panel_rewards")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="back_main")]
    ]
    await update.message.reply_text(
        "🛠️ لوحة التحكم المتقدمة:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==============================
# HANDLERS PART 10
# ==============================

def register_withdrawal_handlers(app):
    app.add_handler(CallbackQueryHandler(withdrawal_menu, pattern="withdraw"))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), process_withdrawal))
    app.add_handler(CallbackQueryHandler(accept_withdrawal, pattern="accept_withdraw_"))
    app.add_handler(CallbackQueryHandler(reject_withdrawal, pattern="reject_withdraw_"))
    app.add_handler(CommandHandler("control_panel", control_panel))

# ==============================
# FULL INTEGRATION & AUTO-UPDATES
# ==============================

# ==============================
# AUTO UPDATE DATA PERIODICALLY
# ==============================

import asyncio

async def auto_update_data(app):
    while True:
        try:
            data = load_data()

            # مثال على تحديث العملات الرقمية من API خارجي
            if "crypto" in data:
                for coin in data["crypto"]:
                    # هنا ممكن تضيف كود لجلب سعر جديد من API
                    data["crypto"][coin]["price"] += 0  # placeholder

            save_data(data)
            print("[AUTO-UPDATE] تم تحديث البيانات بنجاح")
        except Exception as e:
            print(f"[AUTO-UPDATE] خطأ أثناء التحديث: {e}")

        await asyncio.sleep(60*5)  # تحديث كل 5 دقائق


# ==============================
# MAIN INTEGRATION FUNCTION
# ==============================

def integrate_all(app):
    # تسجيل جميع Handlers
    register_deposit_handlers(app)
    register_subscription_handlers(app)
    register_reward_handlers(app)
    register_withdrawal_handlers(app)
    
    # يمكنك إضافة أي Handlers جديدة هنا مستقبلاً
    print("[INTEGRATION] تم تسجيل جميع Handlers")


# ==============================
# START BOT WITH AUTO-UPDATES
# ==============================

async def start_bot(app):
    integrate_all(app)
    # تشغيل التحديثات الدورية
    asyncio.create_task(auto_update_data(app))
    print("[BOT] البوت جاهز ويعمل")

# ==============================
# DAVINCI DESIGN BOT – GUI PANEL
# ==============================

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# ==============================
# MAIN MENU / USER PANEL
# ==============================

def main_menu(user_id, data):
    wallet = data["wallet"].get(str(user_id), 0)
    
    keyboard = [
        [InlineKeyboardButton("💳 شحن الرصيد", callback_data="deposit")],
        [InlineKeyboardButton("🎁 المكافآت", callback_data="reward")],
        [InlineKeyboardButton("💰 السحب", callback_data="withdraw")],
        [InlineKeyboardButton("📊 الاشتراك", callback_data="subscription")],
        [InlineKeyboardButton(f"💵 الرصيد الحالي: {wallet} {data['settings']['currency']}", callback_data="balance_info")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ==============================
# ADMIN PANEL / CONTROL PANEL
# ==============================

def admin_panel(user_id, data):
    wallet_total = data.get("admin_wallet", 0)
    
    keyboard = [
        [InlineKeyboardButton("📩 مراجعة الدفع", callback_data="review_payments")],
        [InlineKeyboardButton("⚙️ إدارة الاشتراكات", callback_data="manage_subscriptions")],
        [InlineKeyboardButton("💰 السحوبات", callback_data="admin_withdrawals")],
        [InlineKeyboardButton(f"💵 الرصيد الكلي: {wallet_total} {data['settings']['currency']}", callback_data="admin_balance_info")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ==============================
# HANDLERS FOR GUI NAVIGATION
# ==============================

async def handle_main_menu(update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = load_data()
    
    if str(user_id) in data["admins"]:
        await query.edit_message_text(
            "🛠 لوحة التحكم (إدارة):",
            reply_markup=admin_panel(user_id, data)
        )
    else:
        await query.edit_message_text(
            "📋 القائمة الرئيسية:",
            reply_markup=main_menu(user_id, data)
        )

# ==============================
# GUI BUTTON NAVIGATION HANDLERS
# ==============================

def register_gui_handlers(app):
    app.add_handler(CallbackQueryHandler(handle_main_menu, pattern="^main_menu$"))
    
def main():
    app = ApplicationBuilder().token("YOUR_BOT_TOKEN").build()

    # ⬅️ سجّل كل الـ handlers مرة واحدة
    register_main_handlers(app)
    register_deposit_handlers(app)
    register_subscription_handlers(app)
    # إذا عندك باقي الـ handlers من PART 4 → PART 12
    # register_design_handlers(app)
    # register_admin_handlers(app)
    # register_reports_handlers(app)

    # شغّل البوت
    print("🤖 Davinci Design Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
