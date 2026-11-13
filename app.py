import streamlit as st
import pandas as pd
import json
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

# ==========================================
# ⚠️ ここに先ほどメモしたフォルダIDを貼り付けます！
# ==========================================
DRIVE_FOLDER_ID = "1TI7JnkiLc3IYgTmkOHMeQSxan5oUT5d0"
SHEET_NAME = "fx_log"

# --- ページ設定 ---
st.title("FXトレード記録ノート 📈 (クラウド保存版)")

# --- Google連携の設定 ---
@st.cache_resource
def init_google():
    # Secretsから鍵を読み込む
    secret_dict = json.loads(st.secrets["google_credentials"])
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(secret_dict, scopes=scopes)
    
    # スプレッドシートとドライブの準備
    gc = gspread.authorize(creds)
    drive_service = build('drive', 'v3', credentials=creds)
    return gc.open(SHEET_NAME).sheet1, drive_service

# 連携開始
try:
    sheet, drive_service = init_google()
except Exception as e:
    st.error(f"Google連携エラーが発生しました。設定を確認してください: {e}")
    st.stop()

# ==========================================
# 1. 入力フォーム
# ==========================================
st.header("新規トレード記録")
with st.form("trade_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        date = st.date_input("トレード日時", datetime.today())
        pair = st.selectbox("通貨ペア", ["USD/JPY", "EUR/USD", "GBP/JPY", "EUR/JPY", "AUD/JPY", "その他"])
    with col2:
        trade_type = st.radio("売買", ["買い (Long)", "売り (Short)"])
        lot = st.number_input("数量 (Lot)", min_value=0.01, step=0.01, value=1.00)
    with col3:
        entry_price = st.number_input("エントリー価格", format="%.3f")
        exit_price = st.number_input("決済価格", format="%.3f")
        
    pnl = st.number_input("損益 (円)", step=100)
    reason = st.text_area("理由・反省点")
    uploaded_file = st.file_uploader("チャート画像を添付", type=['png', 'jpg', 'jpeg'])

    submitted = st.form_submit_button("クラウドに保存する")

    if submitted:
        with st.spinner("Googleにデータを送信中..."):
            image_url = ""
            # 画像がアップロードされた場合
            if uploaded_file is not None:
                file_metadata = {
                    'name': f"{date.strftime('%Y%m%d')}_{pair}.jpg", 
                    'parents': [DRIVE_FOLDER_ID]
                }
                media = MediaIoBaseUpload(io.BytesIO(uploaded_file.getvalue()), mimetype=uploaded_file.type, resumable=True)
                file = drive_service.files().create(body=file_metadata, media_body=media, fields='webViewLink').execute()
                image_url = file.get('webViewLink')

            # スプレッドシートに行を追加
            row_data = [
                str(date), pair, trade_type, lot, entry_price, exit_price, pnl, reason, image_url
            ]
            sheet.append_row(row_data)
            st.success("スプレッドシートとドライブに保存しました！")

# ==========================================
# 2. 履歴表示と分析
# ==========================================
st.header("トレード履歴")

# スプレッドシートからデータを取得
data = sheet.get_all_records()

if data:
    df = pd.DataFrame(data)
    
    # URLが含まれている場合はリンクとして表示できるように設定
    st.dataframe(
        df,
        column_config={
            "画像URL": st.column_config.LinkColumn("画像リンク")
        },
        use_container_width=True
    )
    
    # 累積損益グラフ
    st.subheader("累積損益の推移")
    if "損益(円)" in df.columns:
        # 空欄や文字を除外して数値化し、グラフ化
        df["累積損益"] = pd.to_numeric(df["損益(円)"], errors='coerce').fillna(0).cumsum()
        st.line_chart(df["累積損益"])
else:
    st.info("まだ記録がありません。一番上のフォームから記録を追加してください。")
