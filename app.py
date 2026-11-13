import streamlit as st
import pandas as pd
import os
from datetime import datetime

DATA_FILE = "fx_log.csv"
IMAGE_DIR = "images" # 画像を保存するフォルダ

# 画像保存用フォルダが存在しない場合は作成
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

# CSVファイルが存在しない場合は初期化（画像パスの列を追加）
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["日時", "通貨ペア", "売買", "数量(Lot)", "エントリー価格", "決済価格", "損益(円)", "エントリー理由・反省点", "画像パス"])
    df.to_csv(DATA_FILE, index=False)

st.title("FXトレード記録ノート 📈")

# -----------------------------------
# 1. 入力フォームの作成
# -----------------------------------
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
        
    pnl = st.number_input("損益 (円) ※マイナスは - をつける", step=100)
    reason = st.text_area("エントリーの根拠・決済の理由・反省点")
    
    # 画像アップロード機能を追加
    uploaded_file = st.file_uploader("チャート画像を添付 (任意)", type=['png', 'jpg', 'jpeg'])

    submitted = st.form_submit_button("記録を保存する")

    if submitted:
        image_path = ""
        # 画像がアップロードされた場合の保存処理
        if uploaded_file is not None:
            # 重複を避けるため、現在時刻をファイル名に含める
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"{timestamp}_{uploaded_file.name}"
            image_path = os.path.join(IMAGE_DIR, file_name)
            
            # 画像をフォルダに書き込む
            with open(image_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

        # データを保存
        new_data = pd.DataFrame([{
            "日時": date,
            "通貨ペア": pair,
            "売買": trade_type,
            "数量(Lot)": lot,
            "エントリー価格": entry_price,
            "決済価格": exit_price,
            "損益(円)": pnl,
            "エントリー理由・反省点": reason,
            "画像パス": image_path
        }])
        
        new_data.to_csv(DATA_FILE, mode='a', header=False, index=False)
        st.success("トレード記録と画像を保存しました！")

# -----------------------------------
# 2. データの表示と分析
# -----------------------------------
st.header("トレード履歴と分析")
if os.path.exists(DATA_FILE):
    df_display = pd.read_csv(DATA_FILE)
    
    if not df_display.empty:
        # 画像パスの列は表では見づらいため隠して表示
        st.dataframe(df_display.drop(columns=["画像パス"]), use_container_width=True)
        
        st.subheader("詳細ログ（画像つき）")
        # 履歴を1件ずつアコーディオン（折りたたみ）で表示
        for index, row in df_display.iterrows():
            with st.expander(f"{row['日時']} | {row['通貨ペア']} | {row['売買']} | 損益: {row['損益(円)']}円"):
                st.write(f"**理由・反省点:** {row['エントリー理由・反省点']}")
                
                # 画像パスが存在し、かつファイルが実在する場合のみ画像を表示
                if pd.notna(row['画像パス']) and row['画像パス'] != "" and os.path.exists(row['画像パス']):
                    st.image(row['画像パス'], caption="エントリー時のチャート", use_container_width=True)
    else:
        st.info("まだ記録がありません。")