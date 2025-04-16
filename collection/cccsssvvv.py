import pandas as pd

# CSV 파일 불러오기
df = pd.read_csv("C:/Users/user/Desktop/최종프로젝트/Final_Project\data\zu_traits.csv", encoding='utf-8')  # 또는 cp949

# 기본 확인
print(df['type'].value_counts())

