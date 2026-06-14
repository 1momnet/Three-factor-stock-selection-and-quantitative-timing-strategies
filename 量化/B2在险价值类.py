import pymysql
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
db = pymysql.connect(host='localhost', user='root', password='123456', port=3306, db='stock_data')
# 创建数据库的游标
cursor = db.cursor()

# Var类的目标是接收股票列表，输出最大亏损
class Var:
    def __init__(self, ts_list):
        self.ts_list = ts_list

    def historical_simulation(self):
        for ts_code in self.ts_list:
            sql = '''
                select * from daily_basic where ts_code = %s order by trade_date
            '''

            cursor.execute(sql, ts_code)
            daily_data = cursor.fetchall()
            data_batch_pd = pd.DataFrame(daily_data, columns=['trade_date', 'ts_code', 'circ_mv', 'pb', 'pct_chg'])

            confidence_level = 0.95
            var = -np.percentile(data_batch_pd['pct_chg'].dropna(), (1 - confidence_level) * 100)
            print(f'{ts_code}95%置信度下的最大损失Var为{var}')
