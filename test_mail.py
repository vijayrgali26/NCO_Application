import smtplib, ssl

sender = "yourgmail@gmail.com"
password = "rcsbirtbjcrydnpb"  # your 16-char app password

try:
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls(context=ssl.create_default_context())
    server.login(sender, password)
    print("✅ Login successful")
    server.quit()
except Exception as e:
    print("❌ Error:", e)
