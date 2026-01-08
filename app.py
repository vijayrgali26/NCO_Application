import os
import ast
import csv
import random
from datetime import datetime

import torch
import pandas as pd
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash
)
from flask_mail import Mail, Message
from sentence_transformers import SentenceTransformer, util
from dotenv import load_dotenv
from googletrans import Translator   # <--- NEW

# -------------------------
# Environment
# -------------------------
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# -------------------------
# Mail Configuration
# -------------------------
app.config["MAIL_SERVER"]   = os.getenv("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"]     = int(os.getenv("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"]  = os.getenv("MAIL_USE_TLS", "True") == "True"
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
mail = Mail(app)

# -------------------------
# Language dictionary
# -------------------------
LANGS = {
    "en": {
        "lang_name": "English",
        "welcome": "Welcome",
        "search": "Search Occupations",
        "email": "Enter your Email",
        "label_name": "Enter your Name",
        "label_age": "Enter your Age",
        "sendotp": "Send OTP",
        "otp": "Enter OTP",
        "verify": "Verify OTP",
        "submit": "Submit",
        "results": "Top Matches",
        "num_results": "Number of results",
        "user_login": "User Login",
        "admin_login": "Admin Login",
        "sign_out": "Sign out",
        "mic_start": "Start Mic",
        "mic_stop": "Stop",
        "search_ph": "e.g. Electrician, Teacher, Engineer",
        "results_found": "results found"
    },
    "hi": {
        "lang_name": "हिंदी",
        "welcome": "स्वागत है",
        "search": "व्यवसाय खोजें",
        "email": "अपना ईमेल दर्ज करें",
        "label_name": "अपना नाम दर्ज करें",
        "label_age": "अपनी आयु दर्ज करें",
        "sendotp": "ओटीपी भेजें",
        "otp": "ओटीपी दर्ज करें",
        "verify": "ओटीपी सत्यापित करें",
        "submit": "जमा करें",
        "results": "शीर्ष परिणाम",
        "num_results": "परिणामों की संख्या",
        "user_login": "उपयोगकर्ता लॉगिन",
        "admin_login": "प्रशासक लॉगिन",
        "sign_out": "साइन आउट",
        "mic_start": "माइक शुरू करें",
        "mic_stop": "रोकें",
        "search_ph": "जैसे इलेक्ट्रीशियन, शिक्षक, इंजीनियर",
        "results_found": "परिणाम मिले"
    }
}

@app.context_processor
def inject_langs():
    return dict(LANGS=LANGS, lang=session.get("lang", "en"))

# -------------------------
# Admins
# -------------------------
ADMINS = {
    "4AD23CS083": {"password": "PuneethJ13", "display": "Admin Puneeth J"},
    "4AD23CS116": {"password": "VijayRGali", "display": "Admin Vijay R Gali"},
}

# -------------------------
# Load Occupations Dataset
# -------------------------
df = pd.read_csv("occupations_clean.csv")
if "embeddings" not in df.columns:
    raise RuntimeError("occupations_clean.csv must include an 'embeddings' column")

df["embeddings"] = df["embeddings"].apply(
    lambda x: torch.tensor(ast.literal_eval(x), dtype=torch.float32)
)
EMB_MATRIX = torch.stack(df["embeddings"].tolist())

# -------------------------
# Load Model + Translator
# -------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")
translator = Translator()   # <--- NEW

# -------------------------
# Helpers
# -------------------------
SUBMIT_FILE = "resubmission.csv"
SUBMIT_COLUMNS = ["timestamp", "email", "name", "age", "code", "job_title"]

def clamp_int(value, default=5, lo=1, hi=50):
    try:
        v = int(value)
    except Exception:
        v = default
    return max(lo, min(hi, v))

def ensure_submit_file():
    if not os.path.exists(SUBMIT_FILE):
        with open(SUBMIT_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=SUBMIT_COLUMNS, quoting=csv.QUOTE_ALL)
            writer.writeheader()

def read_submissions_df():
    ensure_submit_file()
    try:
        return pd.read_csv(SUBMIT_FILE, engine="python", quotechar='"', quoting=csv.QUOTE_ALL)
    except Exception:
        try:
            return pd.read_csv(SUBMIT_FILE, engine="python", on_bad_lines="skip")
        except Exception:
            return pd.DataFrame(columns=SUBMIT_COLUMNS)

def append_submission(row_dict):
    ensure_submit_file()
    record = {c: row_dict.get(c, "") for c in SUBMIT_COLUMNS}
    with open(SUBMIT_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SUBMIT_COLUMNS, quoting=csv.QUOTE_ALL)
        writer.writerow(record)

# -------------------------
# Routes
# -------------------------
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/set_lang/<lang>")
def set_lang(lang):
    if lang in LANGS:
        session["lang"] = lang
    return redirect(request.referrer or url_for("home"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        name = request.form.get("name", "").strip()
        age  = request.form.get("age", "").strip()

        if not email or not name or not age:
            flash("Name, Age and Email are required!", "danger")
            return redirect(url_for("login"))

        try:
            _ = int(age)
        except ValueError:
            flash("Age must be a number.", "danger")
            return redirect(url_for("login"))

        session["user_name"] = name
        session["user_age"]  = age
        session["email"]     = email

        otp = str(random.randint(100000, 999999))
        session["otp"] = otp

        try:
            msg = Message("Your OTP Code", sender=app.config["MAIL_USERNAME"], recipients=[email])
            msg.body = f"Your OTP is {otp}"
            mail.send(msg)
            flash("OTP sent to your email!", "info")
        except Exception as e:
            flash(f"Failed to send OTP: {e}", "danger")
            return redirect(url_for("login"))

        return redirect(url_for("verify"))

    return render_template("login_user.html")

@app.route("/verify", methods=["GET", "POST"])
def verify():
    if request.method == "POST":
        otp_entered = request.form.get("otp", "").strip()
        if otp_entered == session.get("otp"):
            flash("OTP Verified Successfully!", "success")
            return redirect(url_for("search"))
        else:
            flash("Invalid OTP. Please try again.", "danger")
            return redirect(url_for("verify"))
    return render_template("verify.html")

@app.route("/search", methods=["GET", "POST"])
def search():
    query = ""
    results = []
    top_k = 5

    if request.method == "POST":
        query = request.form.get("query", "").strip()
        top_k = clamp_int(request.form.get("top_k", 5), default=5, lo=1, hi=50)

        if query:
            # --- Step 1: Try detect Hindi or Hinglish and translate ---
            try:
                detected_lang = translator.detect(query).lang
                if detected_lang == "hi" or detected_lang == "mr":
                    query_translated = translator.translate(query, src="hi", dest="en").text
                    flash(f"Translated '{query}' → '{query_translated}'", "info")
                    query = query_translated
                else:
                    # Hinglish handling (like "darji")
                    query_translated = translator.translate(query, dest="en").text
                    if query_translated.lower() != query.lower():
                        flash(f"Interpreted '{query}' → '{query_translated}'", "info")
                        query = query_translated
            except Exception as e:
                print("Translation error:", e)

            # --- Step 2: Encode & Semantic Search ---
            q_emb = model.encode(query, convert_to_tensor=True)
            if q_emb.dtype != torch.float32:
                q_emb = q_emb.to(torch.float32)

            scores = util.cos_sim(q_emb, EMB_MATRIX)[0]
            top_vals, top_idxs = torch.topk(scores, k=min(top_k, scores.shape[0]))
            for s, idx in zip(top_vals, top_idxs):
                i = int(idx.item())
                row = df.iloc[i]
                results.append({
                    "row_idx": i,
                    "code": row["Code"],
                    "job_title": row["Job Title"],
                    "score": f"{float(s.item()):.4f}"
                })

    return render_template("search.html", query=query, results=results, top_k=top_k)

@app.route("/select/<int:row_idx>", methods=["POST"])
def select(row_idx):
    if row_idx < 0 or row_idx >= len(df):
        flash("Invalid selection.", "danger")
        return redirect(url_for("search"))

    row = df.iloc[row_idx]
    selected_data = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "email": session.get("email", "anonymous"),
        "name": session.get("user_name", ""),
        "age": session.get("user_age", ""),
        "code": row["Code"],
        "job_title": row["Job Title"],
    }
    append_submission(selected_data)
    flash(f"Saved: {row['Job Title']} (Code: {row['Code']})", "success")
    return redirect(url_for("search"))

@app.route("/login_admin", methods=["GET", "POST"])
def login_admin():
    if request.method == "POST":
        admin_id = request.form.get("admin_id", "").strip()
        password = request.form.get("password", "").strip()
        info = ADMINS.get(admin_id)
        if info and info["password"] == password:
            session["admin_id"] = admin_id
            session["admin_name"] = info["display"]
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid admin credentials.", "danger")
            return redirect(url_for("login_admin"))
    return render_template("admin_login.html")

@app.route("/admin")
def admin_dashboard():
    if "admin_id" not in session:
        return redirect(url_for("login_admin"))

    admin_name = session.get("admin_name", "Admin")
    df_res = read_submissions_df()
    records = [
        {
            "row_idx": int(i),
            "timestamp": r.get("timestamp", ""),
            "email": r.get("email", ""),
            "name": r.get("name", ""),
            "age": r.get("age", ""),
            "code": r.get("code", ""),
            "job_title": r.get("job_title", "")
        }
        for i, r in df_res.iterrows()
    ] if not df_res.empty else []

    return render_template("admin_dashboard.html", admin_name=admin_name, records=records)

@app.route("/admin/remove/<int:row_idx>", methods=["POST"])
def remove(row_idx):
    if "admin_id" not in session:
        return redirect(url_for("login_admin"))

    df_res = read_submissions_df()
    if row_idx < 0 or row_idx >= len(df_res):
        flash("Invalid row index.", "danger")
        return redirect(url_for("admin_dashboard"))

    df_res = df_res.drop(index=row_idx).reset_index(drop=True)
    with open(SUBMIT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SUBMIT_COLUMNS, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for _, r in df_res.iterrows():
            writer.writerow({c: r.get(c, "") for c in SUBMIT_COLUMNS})

    flash("Record removed.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# -------------------------
# Run App
# -------------------------
if __name__ == "__main__":
    app.run(debug=True,host="127.0.0.1", port=5000)