# What

中身が画像の PDF のテキスト抽出ツールです。(macOS 専用)

# Prerequisites

- Python 3.12 or later
- tesseract-lang: OCR 識別ライブラリの日本語対応のために必要です。
  - `brew install tesseract-lang`
- poppler: pdf2image ライブラリが依存している poppler
  - `brew install poppler`

# Getting Started

- 0. Put PDF files in the `Data` directory OR change the `pdf_path` variable in `main.py` to the path of the PDF file you want to extract.
- 1. install
  - `pip install -r requirements.txt`
- 2. run
  - `python main.py`

# Process Flow

```mermaid
graph TD
    A[開始] --> B[PDFファイルのフォルダを読み込む]
    B --> C{PDFファイルか?}
    C -->|Yes| D[PDFを画像に変換]
    C -->|No| B
    D --> E[画像を前処理]
    E --> F[OCRでテキスト抽出]
    F --> G{テキストが空?}
    G -->|Yes| H[コントラスト強調]
    H --> E
    G -->|No| I[PDFタイプを識別]
    I --> J{タイプ特定?}
    J -->|Yes| K[タイプ固有の情報抽出]
    J -->|No| L[Unknown typeとして処理]
    K --> M[抽出データを保存]
    L --> M
    M --> N[次のPDFファイル]
    N --> C
    C -->|全て処理完了| O[CSVファイルに結果を書き込み]
    O --> P[終了]

    subgraph 画像処理
    E
    end

    subgraph テキスト抽出
    F
    G
    H
    end

    subgraph データ抽出
    I
    J
    K
    L
    end
```
