import pandas as pd

df = pd.read_csv('RP-PreProd_rds.txt', delimiter='\t')
df.to_excel('RP-PreProd_rds.xlsx', index=False)
