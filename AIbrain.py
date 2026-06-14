# ==========================================
# DARMHIE'S AI BRAIN V3
# ==========================================

BUSINESS_NAME = "DARMHIE'S Collections"
INSTAGRAM = "@darmhies"
COUNTRY = "Nigeria"


# ==========================================
# GREETINGS
# ==========================================
greetings = {
    "hello": f"Hello! Welcome to {BUSINESS_NAME}.",
    "hi": f"Hi there! Welcome to {BUSINESS_NAME}.",
    "good morning": "Good morning! How can I assist you today?",
    "good afternoon": "Good afternoon! How may I help you?",
    "good evening": "Good evening! Welcome to DARMHIE'S.",
}


# ==========================================
# PAYMENT
# ==========================================
payments = {
    "payment": (
        "Orders are handled through WhatsApp. "
        "We'll confirm availability and provide payment details."
    ),
}


# ==========================================
# DELIVERY
# ==========================================
delivery = {
    "delivery": (
        "Delivery takes 1-3 business days within Lagos "
        "and 3-5 business days nationwide."
    ),

    "shipping": "We deliver nationwide across Nigeria.",

    "track": (
        "Tracking details are sent once your order has been dispatched."
    ),
}


# ==========================================
# RETURNS
# ==========================================
returns = {
    "return": (
        "Returns are accepted within 7 days if the item is unused "
        "and in its original condition."
    )
}


# ==========================================
# CONTACT
# ==========================================
contact = {
    "contact": (
        f"You can reach us via WhatsApp or Instagram {INSTAGRAM}."
    )
}


# ==========================================
# SIZE GUIDE
# ==========================================
sizes = {
    "size": (
        "Available sizes are listed on each product page."
    ),

    "small": "Small sizes are available on selected items.",

    "medium": "Medium sizes are available on selected items.",

    "large": "Large sizes are available on selected items.",
}


# ==========================================
# PRODUCT CATEGORIES
# ==========================================
products = {
    "dress": (
        "We offer elegant dresses suitable for different occasions."
    ),

    "gown": (
        "Our gown collection combines elegance and luxury."
    ),

    "ankara": (
        "We offer beautiful Ankara styles for various events."
    ),

    "luxury": (
        "DARMHIE'S specializes in luxury fashion pieces."
    ),

    "casual": (
        "We also offer stylish casual outfits."
    ),
}


# ==========================================
# OCCASION RECOMMENDATIONS
# ==========================================
def recommend_wedding():
    return (
        "For weddings, I recommend our luxury gowns "
        "and elegant occasion dresses."
    )


def recommend_birthday():
    return (
        "For birthdays, stylish dresses and casual luxury pieces "
        "are excellent choices."
    )


def recommend_party():
    return (
        "For parties, our elegant and trendy collections "
        "will help you stand out."
    )


# ==========================================
# COLOR ADVICE
# ==========================================
def color_advice(color):
    if color == "black":
        return "Black outfits are timeless, elegant and versatile."

    if color == "white":
        return "White gives a clean and classy appearance."

    if color == "red":
        return "Red creates a bold and confident look."

    if color == "pink":
        return "Pink gives a soft and feminine touch."

    return "That color can look beautiful depending on the occasion."


# ==========================================
# MAIN AI FUNCTION
# ==========================================
def get_response(message):

    message = message.lower()

    # Wedding
    if "wedding" in message:
        return recommend_wedding()

    # Birthday
    if "birthday" in message:
        return recommend_birthday()

    # Party
    if "party" in message:
        return recommend_party()

    # Color questions
    if "black" in message:
        return color_advice("black")

    if "white" in message:
        return color_advice("white")

    if "red" in message:
        return color_advice("red")

    if "pink" in message:
        return color_advice("pink")

    # Merge all dictionaries
    all_responses = {}

    all_responses.update(greetings)
    all_responses.update(payments)
    all_responses.update(delivery)
    all_responses.update(returns)
    all_responses.update(contact)
    all_responses.update(sizes)
    all_responses.update(products)

    # Keyword search
    for keyword, response in all_responses.items():
        if keyword in message:
            return response

    # Identity questions
    if "who are you" in message:
        return (
            "I'm the DARMHIE'S AI Fashion Assistant. "
            "I'm here to help you with fashion recommendations and store information."
        )

    if "what do you sell" in message:
        return (
            "We sell luxury fashion pieces, dresses, gowns, "
            "Ankara styles and casual wear."
        )

    if "where are you located" in message:
        return (
            "We operate in Nigeria and deliver nationwide."
        )

    if "thank" in message:
        return "You're welcome. Thank you for choosing DARMHIE'S."

    if "bye" in message:
        return "Thank you for visiting DARMHIE'S. Have a wonderful day."

    # Default response
    return (
        "I'm sorry, I couldn't understand your request. "
        "Ask me about delivery, sizes, returns, dresses, weddings or payment."
    )