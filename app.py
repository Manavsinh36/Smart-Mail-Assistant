import streamlit as st
import pickle
import string
import base64
import nltk
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from gmail_service import gmail_login

# -------------------------------------------------------
# Page Configuration
# -------------------------------------------------------

st.set_page_config(
    page_title="AI Email Security",
    page_icon="🛡",
    layout="wide"
)

# -------------------------------------------------------
# Load CSS
# -------------------------------------------------------

def load_css():
    with open("assets/css/style.css") as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )

load_css()

# -------------------------------------------------------
# NLTK
# -------------------------------------------------------

ps = PorterStemmer()

# -------------------------------------------------------
# Load ML Model
# -------------------------------------------------------

tfidf = pickle.load(open("vectorizer.pkl", "rb"))
model = pickle.load(open("model.pkl", "rb"))

# -------------------------------------------------------
# Text Preprocessing
# -------------------------------------------------------

def transform_text(text):
    text = text.lower()
    text = nltk.word_tokenize(text)

    y = []
    for word in text:
        if word.isalnum():
            y.append(word)

    text = y[:]
    y.clear()

    stop_words = set(stopwords.words("english"))
    for word in text:
        if word not in stop_words and word not in string.punctuation:
            y.append(word)

    text = y[:]
    y.clear()

    for word in text:
        y.append(ps.stem(word))

    return " ".join(y)

# -------------------------------------------------------
# Email Category Detection
# -------------------------------------------------------

def detect_category(text):

    text = text.lower()

    categories = {

        "🎓 Education": [
            "exam", "examination", "semester", "student", "assignment",
            "college", "university", "lecture", "course", "class",
            "result", "marks", "hall ticket", "faculty", "professor",
            "attendance", "internal", "practical", "subject",
            "admission", "campus", "degree", "training", "placement"
        ],

        "💼 Business": [
            "meeting", "project", "invoice", "client", "proposal",
            "contract", "office", "company", "business", "manager",
            "employee", "salary", "conference"
        ],

        "🏦 Banking": [
            "bank", "account", "otp", "credit", "debit",
            "payment", "upi", "loan", "balance", "transaction"
        ],

        "🛒 Shopping": [
            "amazon", "flipkart", "order", "delivery", "shopping",
            "discount", "sale", "cart", "coupon"
        ],

        "🍔 Food": [
            "zomato", "swiggy", "pizza", "burger",
            "restaurant", "food", "menu", "dinner", "lunch"
        ],

        "✈ Travel": [
            "flight", "hotel", "booking", "trip",
            "airport", "ticket", "vacation", "travel", "train"
        ],

        "📢 Promotion": [
            "offer", "free", "limited", "exclusive",
            "buy", "save", "discount", "deal", "sale"
        ],

        "🎁 Lottery / Scam": [
            "winner", "won", "claim", "lottery", "prize",
            "cash", "reward", "urgent", "gift", "congratulations"
        ]
    }

    scores = {}

    for category, keywords in categories.items():
        score = 0
        for keyword in keywords:
            if keyword in text:
                score += 1
        scores[category] = score

    best_category = max(scores, key=scores.get)

    if scores[best_category] == 0:
        return "📄 General"

    return best_category

# -------------------------------------------------------
# Recommendations
# -------------------------------------------------------

def get_recommendations(is_spam, category):

    if is_spam:
        return [
            "🚫 Do NOT click any links in this message.",
            "📎 Do NOT download attachments.",
            "🔐 Never share OTP, passwords or banking details.",
            "🚩 Mark this email as Spam.",
            "🗑 Delete the email immediately.",
            "🚫 Block the sender.",
            "🔎 Verify the sender before taking any action."
        ]

    elif category == "🏦 Banking":
        return [
            "🏦 Verify the sender's email address.",
            "🔐 Never share OTP or PIN.",
            "🌐 Visit the official bank website manually.",
            "📞 Contact your bank if anything looks suspicious."
        ]

    elif category == "💼 Business":
        return [
            "📎 Scan attachments before opening.",
            "📞 Confirm payment requests via phone.",
            "✔ Verify sender authenticity.",
            "📄 Double-check invoices and contracts."
        ]

    elif category == "🛒 Shopping":
        return [
            "🛍 Shop only from trusted websites.",
            "💳 Avoid unknown payment links.",
            "📦 Verify delivery notifications.",
            "⭐ Compare prices before purchasing."
        ]

    elif category == "🍔 Food":
        return [
            "🍕 Verify restaurant details.",
            "🎁 Ignore fake food coupons.",
            "📱 Use trusted delivery apps.",
            "⭐ Check restaurant ratings."
        ]

    elif category == "🎓 Education":
        return [
            "🎓 Verify the university email.",
            "📚 Download files only from official portals.",
            "🔒 Never share student login credentials."
        ]

    elif category == "✈ Travel":
        return [
            "✈ Verify booking confirmation.",
            "🌍 Visit the airline's official website.",
            "🎫 Double-check ticket details.",
            "📅 Verify travel dates."
        ]

    elif category == "📢 Promotion":
        return [
            "🏷 Check whether the offer is genuine.",
            "🛒 Compare prices before buying.",
            "⚠ Beware of fake discount websites."
        ]

    else:
        return [
            "✅ Email appears safe.",
            "🔍 Verify unknown links before opening.",
            "🛡 Keep antivirus enabled.",
            "🔄 Keep your system updated."
        ]

# -------------------------------------------------------
# Helper: run the model on a piece of text
# -------------------------------------------------------

def analyze_email(subject, body):
    email_text = f"{subject} {body}"
    processed = transform_text(email_text)
    vector = tfidf.transform([processed]).toarray()

    prediction = model.predict(vector)[0]
    confidence = model.predict_proba(vector)[0]
    category = detect_category(email_text)
    recommendations = get_recommendations(prediction == 1, category)

    return prediction, confidence, category, recommendations

def render_analysis(subject, sender, body, prediction, confidence, category, recommendations):
    st.markdown("---")
    st.subheader(subject if subject else "No Subject")
    st.write("**From:**", sender)

    if prediction == 1:
        st.error("🚨 Spam Email")
        st.metric("Spam Confidence", f"{confidence[1] * 100:.2f}%")
    else:
        st.success("✅ Legitimate Email")
        st.metric("Safe Confidence", f"{confidence[0] * 100:.2f}%")

    st.info(f"Category: {category}")

    st.write("### AI Recommendations")
    for rec in recommendations:
        st.success(rec)

    with st.expander("View Email Body"):
        st.write(body)

# -------------------------------------------------------
# Header / Gmail Login
# -------------------------------------------------------

if "service" not in st.session_state:

    if st.button("🔐 Login with Gmail"):
        st.session_state.service = gmail_login()
        st.success("Successfully connected to Gmail!")
        st.rerun()

st.markdown("""
<div class="main-title">
🛡 AI Email Security & Smart Mail Assistant
</div>

<div class="subtitle">
Smart Spam Detection • Email Categorization • AI Powered Security
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# Manual Paste Input
# -------------------------------------------------------

input_sms = st.text_area(
    "📩 Paste your Email or SMS",
    height=180,
    placeholder="Paste an email or SMS here for AI security analysis..."
)

if st.button("🔍 Analyze Email"):

    if input_sms.strip() == "":
        st.warning("Please enter an email or SMS.")
        st.stop()

    prediction, confidence, category, recommendations = analyze_email("", input_sms)

    st.divider()
    st.subheader("🛡 AI Analysis")

    if prediction == 1:
        st.error("🚨 SPAM EMAIL DETECTED")
        st.metric("Spam Confidence", f"{confidence[1] * 100:.2f}%")
    else:
        st.success("✅ LEGITIMATE EMAIL")
        st.metric("Safe Confidence", f"{confidence[0] * 100:.2f}%")

    st.divider()
    st.subheader("📂 Email Category")
    st.info(category)

    st.divider()
    st.subheader("🧠 Recommendations")
    for rec in recommendations:
        st.success(rec)

    st.divider()
    st.subheader("📄 Email Statistics")

    col1, col2, col3 = st.columns(3)
    col1.metric("Characters", len(input_sms))
    col2.metric("Words", len(input_sms.split()))
    col3.metric("Sentences", len(nltk.sent_tokenize(input_sms)))

# -------------------------------------------------------
# Gmail Inbox Section
# -------------------------------------------------------

if "service" in st.session_state:

    service = st.session_state.service

    @st.cache_data(show_spinner="Fetching inbox...")
    def fetch_inbox(_service, max_results=50):
        results = _service.users().messages().list(
            userId="me",
            labelIds=["INBOX"],
            maxResults=max_results
        ).execute()

        messages = results.get("messages", [])
        email_data = []

        for msg in messages:

            txt = _service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="full"
            ).execute()

            payload = txt["payload"]
            headers = payload.get("headers", [])

            subject = "No Subject"
            sender = "Unknown"

            for h in headers:
                if h["name"] == "Subject":
                    subject = h["value"]
                if h["name"] == "From":
                    sender = h["value"]

            body = ""

            if "parts" in payload:
                for part in payload["parts"]:
                    if part.get("mimeType") == "text/plain":
                        data = part["body"].get("data")
                        if data:
                            body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                            break
            else:
                data = payload.get("body", {}).get("data")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

            category = detect_category(subject + " " + body)

            prediction, confidence, _, _ = analyze_email(subject, body)

            email_data.append({
                "id": msg["id"],
                "subject": subject,
                "sender": sender,
                "body": body,
                "category": category,
                "spam": prediction,
                "confidence": round(max(confidence) * 100, 2)
            })

        return email_data

    email_data = fetch_inbox(service)

    if not email_data:
        st.info("No emails found in your inbox.")
    else:
        # Group emails by category for the sidebar filter
        categories = {}
        for email in email_data:
            cat = email["category"]
            categories.setdefault(cat, []).append(email)

        st.sidebar.title("📂 Categories")

        selected_category = st.sidebar.radio(
            "Select Category",
            ["📥 All Emails"] + list(categories.keys())
        )

        if selected_category == "📥 All Emails":
            filtered_emails = email_data
        else:
            filtered_emails = categories[selected_category]

        st.sidebar.title("📧 Emails")

        email_labels = [
            f"{'🚨' if e['spam'] == 1 else '✅'} {e['subject'][:40]}"
            for e in filtered_emails
        ]

        if email_labels:
            selected_index = st.sidebar.radio(
                "Select an email",
                range(len(filtered_emails)),
                format_func=lambda i: email_labels[i]
            )

            selected_email = filtered_emails[selected_index]

            prediction, confidence, category, recommendations = analyze_email(
                selected_email["subject"], selected_email["body"]
            )

            render_analysis(
                selected_email["subject"],
                selected_email["sender"],
                selected_email["body"],
                prediction,
                confidence,
                category,
                recommendations
            )
        else:
            st.info("No emails in this category.")