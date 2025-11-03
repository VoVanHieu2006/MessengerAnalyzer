import streamlit as st
import os 
import zipfile
import ujson as json 
from collections import Counter, defaultdict
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import uuid
import shutil
import time




if "fre" not in st.session_state:
    st.session_state.fre = defaultdict(Counter)
fre = st.session_state.fre


def read_json(path, user_name):
    with open(path, 'r') as file:
        data = json.load(file)
    for dict in data["messages"]:
        sender_name = dict["sender_name"]
        sender_name = sender_name.encode("latin1").decode()
        if (sender_name == user_name):
            content = dict.get("content")
            if (content):
                time = dict.get("timestamp_ms")
                year = datetime.fromtimestamp(time / 1000).year # dịch ra giờ
                content = content.encode("latin1").decode()
                words = content.split()
                fre[year].update(words)


def create(path, user_name):
    for folders in os.listdir(path):
        folder_path = os.path.join(path, folders)
        if not os.path.isdir(folder_path):
            continue
        for files_folders in os.listdir(folder_path):
            if (files_folders.endswith('.json')):
                full_path = os.path.join(folder_path, files_folders)
                read_json(full_path, user_name)





#title
st.title("📩 Messenger Analyzer "
"\n(Cre: HieuKy)")

st.header("Bước 1: Nhập chính xác tên facebook của bạn")
user_name = st.text_input("Tên facebook: ")


st.header("Bước 2: Tải file lên")
uploaded_file = st.file_uploader("Tải lên file Messenger (folder inbox đã nén)", type=["zip", "rar"])



if uploaded_file is not None:
    st.success("Đã tải thành công file 🥰")

    if "data_loaded" not in st.session_state:
        extract_folder = f"temp_inbox_{uuid.uuid4().hex}"
        os.makedirs(extract_folder, exist_ok=True) 

        with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
            zip_ref.extractall(extract_folder)

        st.info("📂 Đang đọc các file JSON trong thư mục inbox...")

        inbox_path = None
        for root, dirs, files in os.walk(extract_folder):
            if "inbox" in dirs:
                inbox_path = os.path.join(root, "inbox")
                break

        if inbox_path is None:
            st.error("❌ Không tìm thấy thư mục 'inbox' trong file ZIP. Hãy nén đúng thư mục 'messages/inbox' của Facebook.")
        else:
            try:
                create(inbox_path, user_name)
                st.session_state.data_loaded = True
                st.success("Đã đọc xong tin nhắn 🎉")
                time.sleep(0.5)
            except Exception as e:
                st.error(f"❌ Lỗi khi đọc dữ liệu: {str(e)}")
            finally:
                shutil.rmtree(extract_folder)


st.header("Bước 3: Chọn kiểu biểu đồ để hiển thị")

choise = st.radio(
    "Chọn kiểu biểu đồ:",
    ["Biểu đồ tất cả", "Biểu đồ theo năm"]
)

number_of_word = st.number_input("Nhập số lượng từ phổ biến nhất muốn xem (1 - 20): ",
                                min_value=1,
                                max_value=20,
                                step=1)


if st.button("📈 Hiển thị biểu đồ"):
    if not fre:
        st.warning("Chưa có dữ liệu để hiển thị")
    else:
        if choise == "Biểu đồ tất cả":
            total_fre = sum(fre.values(), Counter())
            top_words = total_fre.most_common(number_of_word)
            df = pd.DataFrame(top_words, columns=['Từ sử dụng', 'Số lần sử dụng'])
            plt.figure(figsize=(5, 10))
            fig = plt.gcf()
            sns.barplot(y='Số lần sử dụng', x='Từ sử dụng', data=df, hue="Từ sử dụng", palette = "viridis")
            plt.suptitle("Top những từ được sử dụng nhiều nhất", fontsize=18, color = 'red', fontweight='bold', y=0.95)
            plt.ylabel("Số lần sử dụng", fontsize=11, color='darkred', fontweight='bold')
            plt.xlabel("Từ sử dụng", fontsize=11, color='darkgreen', fontweight='bold')

        elif choise == "Biểu đồ theo năm":
            sorted_fre = dict(sorted(fre.items()))
            number_of_year = len(sorted_fre.keys())
            plt.figure(figsize=(15 / 8 * number_of_year, 40 / 8 * number_of_year))
            fig = plt.gcf()
            sns.set_style("whitegrid")
            plt.suptitle("Top những từ sử dụng nhiều nhất qua các năm", fontsize=18, color = 'red', fontweight='bold', y=0.91)
            for year in sorted_fre.keys():
                top_words = fre[year].most_common(number_of_word)
                df = pd.DataFrame(data=top_words, columns=['Từ sử dụng', 'Số lần sử dụng'])
                ax = plt.subplot(4, 2, year - min(fre.keys()) + 1)
                sns.barplot(x='Số lần sử dụng', y='Từ sử dụng', data=df, hue="Từ sử dụng", palette = "viridis")

                ax.patch.set_edgecolor('black')   # màu khung
                ax.patch.set_linewidth(1)         # độ dày khung
                plt.title(f"Năm {year}", fontsize=14, color='royalblue', fontweight='bold')
                plt.xlabel("Số lần sử dụng", fontsize=11, color='darkred', fontweight='bold')
                plt.ylabel("Từ sử dụng", fontsize=11, color='darkgreen', fontweight='bold')
                plt.tight_layout()
                plt.subplots_adjust(top=0.93)  # chừa khoảng cho tiêu đề
                plt.suptitle("Top những từ sử dụng nhiều nhất qua các năm", fontsize=18, color='red', fontweight='bold', y=0.98)
            plt.tight_layout(rect=[0, 0, 1, 0.96])
        st.pyplot(fig)
        plt.close('all')


