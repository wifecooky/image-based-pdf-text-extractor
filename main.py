import os
import csv
from pdf2image import convert_from_path
import pytesseract
from PIL import Image, ImageEnhance
import logging
import re
import cv2
import numpy as np

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# PDFタイプと抽出ロジックの定義
PDF_TYPES = {
    "TYPE-A": {
        "identifier": lambda text: "輸出許可通知書" in text,
        "extractor": lambda text: {}
    },
    "BZ Invoice": {
        "identifier": lambda text: "AWB No" in text,
        "extractor": lambda text: {}
    },
    "TYPE-C": {
        "identifier": lambda text: "WAYBILL" in text,
        "extractor": lambda text: {}
    }
    # 新しいPDFタイプをここに追加できます
}

def preprocess_image(image):
    # OpenCV形式に変換
    opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # グレースケールに変換
    gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
    
    # ノイズ除去
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    
    # コントラスト調整
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    contrast = clahe.apply(denoised)
    
    # 閾値処理
    _, threshold = cv2.threshold(contrast, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return Image.fromarray(threshold)

def extract_text_from_image(image):
    # 画像の前処理
    processed_image = preprocess_image(image)
    
    # pytesseractを使用してテキストを抽出（日本語と英語の両方に対応）
    text = pytesseract.image_to_string(processed_image, lang='jpn+eng', config='--psm 6 --oem 1')
    return text

def extract_text_from_pdf(pdf_path, image_output_dir):
    try:
        # より高いDPIで画像に変換
        images = convert_from_path(pdf_path, dpi=400)
        full_text = []
        
        for i, image in enumerate(images):
            # 画像を保存
            image_filename = f"{os.path.splitext(os.path.basename(pdf_path))[0]}_page_{i+1}.png"
            image_path = os.path.join(image_output_dir, image_filename)
            image.save(image_path, 'PNG')
            
            # テキスト抽出を試みる
            text = extract_text_from_image(image)
            
            # テキストが空の場合、別の方法を試みる
            if not text.strip():
                # コントラストを上げてみる
                enhancer = ImageEnhance.Contrast(image)
                enhanced_image = enhancer.enhance(2.0)  # コントラストを2倍に
                text = extract_text_from_image(enhanced_image)
            
            full_text.append(text)
        
        return "\n".join(full_text)
    except Exception as e:
        logging.error(f"Error converting PDF to images: {str(e)}")
        return ""

def process_pdfs_to_csv(folder_path, output_csv, text_output_dir, image_output_dir):
    pdf_data = []
    
    # 出力ディレクトリが存在しない場合は作成
    os.makedirs(text_output_dir, exist_ok=True)
    os.makedirs(image_output_dir, exist_ok=True)
    
    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.pdf'):
            file_path = os.path.join(folder_path, filename)
            logging.info(f"Processing: {file_path}")
            try:
                text = extract_text_from_pdf(file_path, image_output_dir)
                
                if not text.strip():
                    raise ValueError("No text could be extracted from the PDF")
                
                # 抽出されたテキストを個別のファイルに保存
                save_text_to_file(text, text_output_dir, filename)
                
                elements = identify_and_extract(text)
                elements['filename'] = filename
                
                # Only keep pdf_type, filename, and product_info
                pdf_data.append({
                    'pdf_type': elements['pdf_type'],
                    'filename': elements['filename'],
                    'product_info': ', '.join(elements.get('product_info', []))  # Join product_info list into a string
                })
            except Exception as e:
                logging.error(f"Failed to process {filename}: {str(e)}")
                pdf_data.append({'pdf_type': 'Error', 'filename': filename, 'product_info': str(e)})
    
    # CSVファイルに書き込み
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['pdf_type', 'filename', 'product_info']  # Specify the desired fieldnames
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for data in pdf_data:
            writer.writerow(data)

def extract_product_info(text):
    # 商品名とPCSの件数を抽出
    # product_pattern = r'(\d+)\s+(.*?)\s+\d+\.\d+\s+kg\s+.*?\|\s+JAPAN\s+(\d+)\s*PCS'
    product_pattern = r'(\d+)\s+(.*?)\s+\d+\.\d+\s+kg.*?\s+(\d+)\s*PCS'

    matches = re.findall(product_pattern, text)
    print("matches: ", matches)
    return [{'product_name': match[1], 'pcs_count': match[2]} for match in matches] if matches else []

def format_product_info(product_info):
    # 商品情報を指定されたフォーマットに変換
    return [f"{item['product_name']}: {item['pcs_count']}" for item in product_info]

def identify_and_extract(text):
    for pdf_type, config in PDF_TYPES.items():
        if config["identifier"](text):
            elements = config["extractor"](text)
            elements['pdf_type'] = pdf_type
            
            # 商品情報を抽出
            print("find pdf type: ", pdf_type)
            product_info = extract_product_info(text)
            elements['product_info'] = format_product_info(product_info)  # フォーマットを適用
            
            return elements
    
    # 未知のPDFタイプの場合
    return {'pdf_type': 'Unknown', 'product_info': []}

def save_text_to_file(text, output_dir, filename):
    # テキストファイルの名前を生成（PDFファイル名と同じ名前で.txtの拡張子）
    text_filename = os.path.splitext(filename)[0] + '.txt'
    text_filepath = os.path.join(output_dir, text_filename)
    
    # テキストをファイルに書き込む
    with open(text_filepath, 'w', encoding='utf-8') as f:
        f.write(text)

if __name__ == '__main__':
    folder_path = '/Users/wenping.wang/Downloads/invoice-11/'  # PDFファイルが格納されているフォルダのパス
    output_csv = 'extracted_data.csv'
    text_output_dir = './extracted_texts'  # 抽出されたテキスト(中間データ)を保存するディレクトリ
    image_output_dir = './extracted_images'  # 抽出された画像(中間データ)を保存するディレクトリ

    process_pdfs_to_csv(folder_path, output_csv, text_output_dir, image_output_dir)
    print(f"処理が完了しました。結果は {output_csv} に保存されました。")
    print(f"抽出されたテキストは {text_output_dir} に保存されました。")
    print(f"抽出された画像は {image_output_dir} に保存されました。")
