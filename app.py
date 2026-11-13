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

# 値を入力した瞬間に画面を更新（自動計算）させるため、st.formは外しています
col1, col2, col3 = st.columns(3)

with col1:
    date = st.date_input("トレード日時", datetime.today())
    pair = st.selectbox("通貨ペア", ["USD/JPY", "EUR/USD", "GBP/JPY", "EUR/JPY", "AUD/JPY", "その他"])
with col2:
    trade_type = st.radio("売買", ["買い (Long)", "売り (Short)"])
    lot = st.number_input("数量 (Lot)", min_value=0.01, step=0.01, value=0.50)
with col3:
    entry_price = st.number_input("エントリー価格", format="%.3f", value=0.000)
    exit_price = st.number_input("決済価格", format="%.3f", value=0.000)

# --- 損益の自動計算 ---
# 1Lot = 10,000通貨を基準に計算
multiplier = 10000

# 両方の価格が入力された場合のみ計算を実行
if entry_price > 0 and exit_price > 0:
    if trade_type == "買い (Long)":
        auto_pnl = (exit_price - entry_price) * lot * multiplier
    else: # 売り (Short)
        auto_pnl = (entry_price - exit_price) * lot * multiplier
    auto_pnl = int(round(auto_pnl)) # 小数点以下を四捨五入して整数化
else:
    auto_pnl = 0

# 自動計算された損益を大きくリアルタイム表示
st.metric(label="予想損益 (円)", value=f"{auto_pnl:,} 円")

reason = st.text_area("エントリーの根拠・決済の理由・反省点")
uploaded_file = st.file_uploader("チャート画像を添付 (任意)", type=['png', 'jpg', 'jpeg'])

# 保存ボタン
if st.button("記録を保存する"):
    image_path = ""
    if uploaded_file is not None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{timestamp}_{uploaded_file.name}"
        image_path = os.path.join(IMAGE_DIR, file_name)
        with open(image_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

    # 新しいデータをデータフレーム化（損益には自動計算された auto_pnl を直接代入）
    new_data = pd.DataFrame([{
        "日時": date,
        "通貨ペア": pair,
        "売買": trade_type,
        "数量(Lot)": lot,
        "エントリー価格": entry_price,
        "決済価格": exit_price,
        "損益(円)": auto_pnl, 
        "エントリー理由・反省点": reason,
        "画像パス": image_path
    }])
    
    # CSVファイルに追記
    new_data.to_csv(DATA_FILE, mode='a', header=False, index=False)
    st.success(f"損益 {auto_pnl:,} 円のトレード記録を保存しました！")
    
# -----------------------------------
# 2. データの表示と分析
# -----------------------------------
st.header("トレード履歴と分析")
if os.path.exists(DATA_FILE):
    df_display = pd.read_csv(DATA_FILE)
    
    if not df_display.empty:
        # --- 累積損益のグラフ作成（初期値0スタート） ---
        st.subheader("累積損益の推移 📈")
        
        # 損益データの先頭に「0」を追加し、リスト化してから累積和（cumsum）を取る
        # これによりグラフの左端が必ず「0」からスタートします
        cumulative_pnl = [0] + df_display["損益(円)"].cumsum().tolist()
        
        # 折れ線グラフを描画
        st.line_chart(cumulative_pnl)
        
        # 今までの合計損益を大きく表示
        total_pnl = df_display["損益(円)"].sum()
        if total_pnl >= 0:
            st.metric(label="現在の合計損益", value=f"+{total_pnl:,.0f} 円")
        else:
            st.metric(label="現在の合計損益", value=f"{total_pnl:,.0f} 円")

        # --- テーブルと詳細ログの表示 ---
        st.subheader("トレード履歴")
        # 画像パスの列は表では見づらいため隠して表示
        if "画像パス" in df_display.columns:
            st.dataframe(df_display.drop(columns=["画像パス"]), use_container_width=True)
        else:
            st.dataframe(df_display, use_container_width=True)
        
        st.subheader("詳細ログ（画像つき）")
        # 履歴を1件ずつアコーディオン（折りたたみ）で表示
        for index, row in df_display.iterrows():
            with st.expander(f"{row['日時']} | {row['通貨ペア']} | {row['売買']} | 損益: {row['損益(円)']}円"):
                st.write(f"**理由・反省点:** {row['エントリー理由・反省点']}")
                
                # 画像が存在する場合のみ表示
                if "画像パス" in row and pd.notna(row['画像パス']) and row['画像パス'] != "" and os.path.exists(row['画像パス']):
                    st.image(row['画像パス'], caption="エントリー時のチャート", use_container_width=True)
    else:
        st.info("まだ記録がありません。") 
