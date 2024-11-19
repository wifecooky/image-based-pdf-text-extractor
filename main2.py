import re

# 修正版の正規表現
product_pattern = r'(\d+)\s+(.*?)\s+\d+\.\d+\s+kg\s+.*?\|\s+JAPAN\s+(\d+)\s*PCS'


# データ
data1 = "1       Fancl Supplement For Women in 60s                                0.078 kg | JAPAN                                72PCS      3,237 JPY |233,064 JPY"
data2 = "1      Fancl Brightening Lotion 1                                    0.054 kg _ | JAPAN                           168 PCS    1,216 JPY |204,288 JPY"

# マッチング
match1 = re.search(product_pattern, data1)
match2 = re.search(product_pattern, data2)

# 結果表示
def display_match(data_label, match):
    if match:
        print(f"{data_label} Matches:")
        print("Number:", match.group(1))
        print("Description:", match.group(2).strip())
        print("PCS:", match.group(3))
    else:
        print(f"{data_label} did not match.")

display_match("Data1", match1)
display_match("Data2", match2)
