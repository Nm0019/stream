📊 Streamlit Trading Analytics Dashboard
<p align="center">
  <img src="assets/Screenshot 2025-10-17 121510.png" width="90%" alt="Dashboard Main Preview">
</p>

A real-time trading analytics dashboard built with Python, Streamlit, and SQLite, integrating technical indicators and price-action logic to visualize market structure, volatility, and trend strength.
Developed by Mohammad Naderi, based in Dubai, UAE.

🚀 Key Features

Live Data Fetching from MetaTrader 5 API

Automatic Demo Mode: if MT5 is unavailable, the app loads data directly from local SQLite database

Symbol-level SQLite Storage for OHLCV data

Modular Indicator Engine: RSI, MACD, ATR, ADX, Triple EMA

Price Action Detection: adaptive swing points, structure labels (HH / HL / LH / LL), and channel recognition

Interactive Plotly Charts across Streamlit tabs

Optimized UI Design for both trading and data analytics

🖼️ Dashboard Screenshots
<p align="center"> <img src="assets/Screenshot-2025-10-17-122035.png" width="45%" alt="Price Action Tab"> <img src="assets/Screenshot-2025-10-17-122103.png" width="45%" alt="ATR Dashboard"><br><br> <img src="assets/Screenshot-2025-10-17-122115.png" width="45%" alt="EMA and ADX Charts"> <img src="assets/Screenshot-2025-10-17-122127.png" width="45%" alt="MACD Tab"><br><br> <img src="assets/Screenshot-2025-10-17-122147.png" width="60%" alt="RSI Tab"> </p>

Each tab displays a different technical insight — from volatility analysis to price action and trend strength.

🧱 Architecture Overview
MetaTrader 5  →  Data Fetcher  →  SQLite DB  →  Indicator Manager  →  Streamlit Visualization

Core Modules
Folder	Description
mt5_connector/	Fetches OHLCV data from MetaTrader 5
database/	Handles SQLite operations
analysis/	Contains technical indicator & price-action calculations
visualization/	Creates Plotly visualizations for Streamlit
app.py	Streamlit front-end (Live & Demo modes)
run_indicators_launcher.py	Runs automated indicator updates
⚙️ Installation & Usage
1️⃣ Clone the Repository
git clone https://github.com/Nm0019/stream.git
cd stream

2️⃣ Create a Virtual Environment
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows

3️⃣ Install Requirements
pip install -r requirements.txt

4️⃣ Configure MT5 (Optional)

Create a .env file:

MT5_LOGIN=your_login
MT5_PASSWORD=your_password
MT5_SERVER=your_server
MT5_PATH=your_mt5_path

5️⃣ Run the App
streamlit run app.py


💡 If MT5 is unavailable, the app will automatically switch to Demo Mode using the local database.

🧮 Indicators Included

RSI – Relative Strength Index

MACD – Moving Average Convergence Divergence

ATR – Average True Range

ADX – Average Directional Index

EMA (Triple) – Short / Medium / Long Exponential Moving Averages

🧰 Tech Stack
Category	Technologies
Language	Python 3.10+
Framework	Streamlit
Libraries	Plotly, Pandas, NumPy, SciPy, MetaTrader5, python-dotenv
Database	SQLite
Visualization	Plotly
Environment	Streamlit UI + .ENV configuration
🧠 Highlights

Modular indicator system (easy to extend)

Offline demo-ready fallback mode

Structured, maintainable OOP codebase

Intuitive charts for market insight visualization

Optimized layout for readability and performance

🧩 Future Roadmap

 Docker deployment for Streamlit Cloud

 Multilingual UI (EN / FA)

 Pytest-based testing suite

 Extended Indicator Library

 Live multi-symbol comparison

👤 Author

Mohammad Naderi
Python Developer & Data Analyst
📍 Dubai, UAE

📧 Email: whiteramtehran@gmail.com

💬 WhatsApp: +971 583 071 091

🏷️ License

MIT License — free for educational and professional demonstration purposes.

🌟 Summary for Recruiters

This project demonstrates:

Strong command of Python, OOP, and modular data design

End-to-end data flow (API → DB → Indicators → Visualization)

Hands-on experience in financial and technical analysis

Practical dashboard development with Streamlit and Plotly

✅ Open to Junior Python / Data / Streamlit Developer roles in Dubai, UAE.

📌 If you’re a recruiter or company representative, feel free to reach out via email or WhatsApp for portfolio verification or collaboration.
