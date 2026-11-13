import streamlit as st
import pandas as pd
import json
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# ==========================================
SHEET_NAME = "fx-log"
# ==========================================

# --- ページ設定 ---
st.set_page_config(page_title="FXトレード記録", layout="centered")
st.title("FXトレード記録ノート 📈")

# --- Google連携の設定 ---
@st.cache_resource
def init_google():
    secret_dict = json.loads(st.secrets["google_credentials"])
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(secret_dict, scopes=scopes)
    gc = gspread.authorize(creds)
    return gc.open(SHEET_NAME).sheet1

try:
    sheet = init_google()
except Exception as e:
    st.error(f"Google連携エラーが発生しました。設定を確認してください: {e}")
    st.stop()

# --- データの取得 ---
data = sheet.get_all_records()
df = pd.DataFrame(data)

# ==========================================
# 🌟 今日の損益表示（サマリー）
# ==========================================
st.header("📊 サマリー")
today_str = datetime.today().strftime('%Y-%m-%d')

if not df.empty and "損益(円)" in df.columns and "日時" in df.columns:
    df["損益(円)"] = pd.to_numeric(df["損益(円)"], errors='coerce').fillna(0)
    
    # 今日の日付と一致するデータだけを集めて合計
    today_df = df[df["日時"] == today_str]
    today_pnl = today_df["損益(円)"].sum()
    
    # すべての期間の合計損益
    total_pnl = df["損益(円)"].sum()
    
    col_a, col_b = st.columns(2)
    col_a.metric(label=f"今日の損益 ({today_str})", value=f"{int(today_pnl):,} 円")
    col_b.metric(label="合計損益", value=f"{int(total_pnl):,} 円")
else:
    st.info("データがまだないか、計算できません。")

st.divider()

# ==========================================
# 1. 入力フォーム
# ==========================================
st.header("新規トレード記録")
with st.form("trade_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("トレード日時", datetime.today())
        pair = st.selectbox("通貨ペア", ["USD/JPY", "EUR/USD", "GBP/JPY", "EUR/JPY", "AUD/JPY", "その他"])
    with col2:
        trade_type = st.radio("売買", ["買い (Long)", "売り (Short)"])
        lot = st.number_input("数量 (Lot)", min_value=0.01, step=0.01, value=1.00)
        
    pnl = st.number_input("損益 (円) ※マイナスは - をつける", step=100)
    reason = st.text_area("理由・反省点")

    submitted = st.form_submit_button("記録を保存する")

    if submitted:
        with st.spinner("スプレッドシートに送信中..."):
            # スプレッドシートに行を追加（6項目）
            row_data = [
                str(date), pair, trade_type, lot, pnl, reason
            ]
            try:
                sheet.append_row(row_data)
                st.success("トレード記録を保存しました！")
                st.rerun() 
            except Exception as e:
                st.error(f"スプレッドシートへの保存に失敗しました: {e}")

# ==========================================
# 2. 履歴表示と分析
# ==========================================
st.header("トレード履歴")

if not df.empty:
    st.dataframe(df, use_container_width=True)
    
    st.subheader("累積損益の推移")
    if "損益(円)" in df.columns:
        df["累積損益"] = df["損益(円)"].cumsum()
        st.line_chart(df["累積損益"])
else:
    st.info("まだ記録がありません。一番上のフォームから記録を追加してください。")
