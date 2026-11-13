import streamlit as st
import pandas as pd
import json
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import requests
import base64

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
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(secret_dict, scopes=scopes)
    gc = gspread.authorize(creds)
    return gc.open(SHEET_NAME).sheet1

try:
    sheet = init_google()
except Exception as e:
    st.error(f"Google連携エラーが発生しました。設定を確認してください: {e}")
    st.stop()

# --- データの取得 ---
# 画面の一番上でデータを読み込みます
data = sheet.get_all_records()
df = pd.DataFrame(data)

# ==========================================
# 🌟 今日の損益表示（サマリー）
# ==========================================
st.header("📊 サマリー")
today_str = datetime.today().strftime('%Y-%m-%d')

if not df.empty and "損益(円)" in df.columns and "日時" in df.columns:
    # 損益を計算用の数値に変換
    df["損益(円)"] = pd.to_numeric(df["損益(円)"], errors='coerce').fillna(0)
    
    # 今日の日付と一致するデータだけを集めて合計
    today_df = df[df["日時"] == today_str]
    today_pnl = today_df["損益(円)"].sum()
    
    # すべての期間の合計損益
    total_pnl = df["損益(円)"].sum()
    
    # 画面の上に大きく表示
    col_a, col_b = st.columns(2)
    col_a.metric(label=f"今日の損益 ({today_str})", value=f"{int(today_pnl):,} 円")
    col_b.metric(label="合計損益", value=f"{int(total_pnl):,} 円")
else:
    st.info("データがまだないか、計算できません。")

st.divider() # 区切り線

# ==========================================
# 1. 入力フォーム（価格入力を削除）
# ==========================================
st.header("新規トレード記録")
with st.form("trade_form", clear_on_submit=True):
    # 3列だったものを2列に変更し、スッキリさせました
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("トレード日時", datetime.today())
        pair = st.selectbox("通貨ペア", ["USD/JPY", "EUR/USD", "GBP/JPY", "EUR/JPY", "AUD/JPY", "その他"])
    with col2:
        trade_type = st.radio("売買", ["買い (Long)", "売り (Short)"])
        lot = st.number_input("数量 (Lot)", min_value=0.01, step=0.01, value=1.00)
        
    pnl = st.number_input("損益 (円) ※マイナスは - をつける", step=100)
    reason = st.text_area("理由・反省点")
    uploaded_file = st.file_uploader("チャート画像を添付", type=['png', 'jpg', 'jpeg'])

    submitted = st.form_submit_button("記録を保存する")

    if submitted:
        with st.spinner("データを送信中..."):
            image_url = ""
            
            # ImgBBに画像をアップロード
            if uploaded_file is not None:
                try:
                    img_bytes = uploaded_file.getvalue()
                    img_b64 = base64.b64encode(img_bytes).decode('utf-8')
                    res = requests.post(
                        "https://api.imgbb.com/1/upload",
                        data={
                            "key": st.secrets["IMGBB_API_KEY"],
                            "image": img_b64
                        }
                    )
                    if res.status_code == 200:
                        image_url = res.json()["data"]["url"]
                    else:
                        st.warning("画像のアップロードに失敗しました。文字データのみ保存します。")
                except Exception as e:
                    st.warning(f"画像処理エラーが発生しました: {e}")

            # スプレッドシートに行を追加（列数に合わせて7項目に修正）
            row_data = [
                str(date), pair, trade_type, lot, pnl, reason, image_url
            ]
            try:
                sheet.append_row(row_data)
                st.success("トレード記録を保存しました！")
                # 🌟 保存した瞬間に画面を自動で再読み込みし、上の「今日の損益」を最新にする
                st.rerun() 
            except Exception as e:
                st.error(f"スプレッドシートへの保存に失敗しました: {e}")

# ==========================================
# 2. 履歴表示と分析
# ==========================================
st.header("トレード履歴")

if not df.empty:
    st.dataframe(
        df,
        column_config={
            "画像URL": st.column_config.LinkColumn("画像リンク")
        },
        use_container_width=True
    )
    
    st.subheader("累積損益の推移")
    if "損益(円)" in df.columns:
        df["累積損益"] = df["損益(円)"].cumsum()
        st.line_chart(df["累積損益"])
