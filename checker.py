import os
import json
import urllib.request
import urllib.error
import smtplib
from email.mime.text import MIMEText
from pathlib import Path

# ================= 配置区 =================
INVITE_LINK = "https://discord.gg/elysianhorizon"   # 改成你要监控的链接
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465
SENDER_EMAIL = "493302953@qq.com"            # 你的发件邮箱
RECEIVER_EMAIL = "493302953@qq.com"          # 接收通知的邮箱
# ==========================================

STATUS_FILE = Path("last_status.txt")

def get_password():
    pwd = os.environ.get("QQ_SMTP_PASSWORD")
    if not pwd:
        raise ValueError("❌ 环境变量 QQ_SMTP_PASSWORD 未设置！")
    return pwd

def check_link_status():
    invite_code = INVITE_LINK.rstrip("/").split("/")[-1]
    api_url = f"https://discord.com/api/v10/invites/{invite_code}"

    try:
        req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                features = data.get("guild", {}).get("features", [])
                if "INVITES_DISABLED" in features:
                    return "PAUSED"
                return "OPEN"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return "INVALID"
        print(f"HTTP 错误: {e.code}")
    except Exception as e:
        print(f"请求出错: {e}")
    return "UNKNOWN"

def send_email():
    pwd = get_password()
    msg = MIMEText(
        f"你监控的 Discord 邀请链接已经重新开放！\n\n链接：{INVITE_LINK}\n\n快去加入吧！",
        "plain",
        "utf-8"
    )
    msg["Subject"] = "🚨 Discord 邀请已开放！"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SENDER_EMAIL, pwd)
            server.sendmail(SENDER_EMAIL, [RECEIVER_EMAIL], msg.as_string())
        print("✅ 邮件发送成功！")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        raise

def load_last_status():
    if STATUS_FILE.exists():
        return STATUS_FILE.read_text(encoding="utf-8").strip()
    return None

def save_status(status: str):
    STATUS_FILE.write_text(status, encoding="utf-8")

if __name__ == "__main__":
    print("开始检查...")
    status = check_link_status()
    last = load_last_status()
    print(f"当前状态: {status} | 上次状态: {last}")

    # 只有从非 OPEN 变成 OPEN 才发邮件（避免重复通知）
    if status == "OPEN" and last != "OPEN":
        print("🎉 链接已开放！正在发送邮件...")
        send_email()
    elif status == "PAUSED":
        print("⏳ 链接有效，但服务器正在暂停邀请。")
    elif status == "INVALID":
        print("❌ 链接已彻底失效（404）。")
    else:
        print("⚠️ 状态未知。")

    save_status(status)
