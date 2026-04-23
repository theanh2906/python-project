import pdfplumber
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import os
import re
from fpdf import FPDF

def extract_data_from_text(pdf_path):
    transactions = []
    # Regex tìm dòng giao dịch: Ngày (dd-mm-yyyy) - Ngày - Thẻ - Nội dung - Số tiền
    # Cấu trúc: (Ngày 1) (Ngày 2) (Số thẻ) (Nội dung) (Số tiền có dấu chấm)
    pattern = re.compile(r'(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})\s+(\d{4})\s+(.*?)\s+([\d\.]+)(?:\s+CR)?$')

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            
            for line in text.split('\n'):
                line = line.strip()
                match = pattern.search(line)
                if match:
                    date, _, card, desc, amount_str = match.groups()
                    
                    # Làm sạch số tiền
                    amount = int(amount_str.replace('.', ''))
                    if 'CR' in line:
                        amount = -amount
                    
                    transactions.append({"Desc": desc, "Amount": amount})
    
    return pd.DataFrame(transactions)

def categorize(desc):
    desc = desc.upper()
    if any(k in desc for k in ["XANHSM", "GSM", "BE GROUP", "MOCA"]): return "Di chuyen"
    if any(k in desc for k in ["HIGHLANDS", "FOODY", "ANNAM", "CLOUD POT", "7-ELEVEN", "AMERICANO"]): return "An uong"
    if any(k in desc for k in ["TAM ANH", "PHARMACITY", "LONGCHAU", "WELLNESS"]): return "Y te"
    if any(k in desc for k in ["SACOMBANK KLK", "TRA GOP"]): return "Tra gop"
    if any(k in desc for k in ["SHOPEE", "MICROSOFT", "GOOGLE", "NETFLIX", "SONG HUA"]): return "Mua sam"
    return "Khac"

def create_report(df, export_path):
    if df.empty:
        print("❌ Van khong tim thay du lieu. Co the file PDF nay la dang scan (anh)?")
        return

    df['Category'] = df['Desc'].apply(categorize)
    summary = df.groupby('Category')['Amount'].sum().reset_index()
    
    # Vẽ biểu đồ
    plt.figure(figsize=(6, 6))
    plt.pie(summary['Amount'].abs(), labels=summary['Category'], autopct='%1.1f%%', startangle=140)
    plt.title("Ti le chi tieu - Ben's Report")
    plt.savefig("chart.png")
    plt.close()
    
    # Tạo PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "BAO CAO CHI TIEU TIN DUNG", ln=True, align='C')
    
    if os.path.exists("chart.png"):
        pdf.image("chart.png", x=50, y=30, w=110)
    
    pdf.set_y(150)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(100, 10, "Hang muc", border=1)
    pdf.cell(80, 10, "So tien (VND)", border=1, ln=True)
    
    pdf.set_font("Arial", '', 12)
    for _, row in summary.iterrows():
        pdf.cell(100, 10, str(row['Category']), border=1)
        pdf.cell(80, 10, f"{row['Amount']:,.0f}", border=1, ln=True)
    
    pdf.output(export_path)
    if os.path.exists("chart.png"): os.remove("chart.png")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    
    output_file = args.output if args.output else os.path.splitext(args.input)[0] + "_Report.pdf"
    
    print(f"🔄 Dang xu ly file (Plan B): {args.input}...")
    df_raw = extract_data_from_text(args.input)
    create_report(df_raw, output_file)
    if not df_raw.empty:
        print(f"✅ Thanh cong ruc ro! Da xuat tai: {output_file}")


if __name__ == "__main__":
    main()