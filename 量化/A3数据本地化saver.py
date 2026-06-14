import  pymysql
import time
import tushare as ts
import pandas as pd
from timed_decorator.simple_timed import timed
db = pymysql.connect(host='localhost', user='root', password='123456', port=3306, db='stock_data')
# 创建数据库的游标
cursor = db.cursor()
ts.set_token('3f3c696116d8dbb7f9dbd53e598198e41c142216da03a9fc7ad56f89')
pro = ts.pro_api()

class Saver:
    def __init__(self):
        pass

    @timed(use_seconds=True, precision=3)
    def daily_basic_saver(self, one_date, ts_list):
        i = 0
        t1 = time.time()
        for code in ts_list:
            max_retries = 5  # 最大重试次数
            retry_count = 0
            while retry_count < max_retries:
                try:
                    df3 = pro.query('daily_basic', ts_code=code, trade_date=one_date,
                                    fields='trade_date, ts_code, circ_mv, pb')
                    df4 = pro.daily(ts_code=code, start_date=one_date, end_date=one_date)
                    if df3.empty or df4.empty:
                        i += 1
                        print('{} no data'.format(code))
                        break
                    sql = '''
                            insert ignore into daily_basic values(%s, %s, %s, %s, %s)
                            '''
                    # replace into`user` ( `id`,`name`,`age` ) values ( 1, '张三', 30) 覆盖替换
                    # insert ignore into `user` ( `id`, `name`, `age` ) values ( 1, '张三', 30) 去重，需要设置唯一约束

                    cursor.execute(sql, (
                        df3['trade_date'].iloc[0], df3['ts_code'].iloc[0], df3['circ_mv'].iloc[0], df3['pb'].iloc[0],
                        df4['pct_chg'].iloc[0]))
                    db.commit()

                except Exception as e:
                    retry_count += 0
                    print(f'出现异常：{e}，尝试第{retry_count}次重试，睡眠60秒')
                    time.sleep(60)
                break  # 直到程序正常运行
        '''i += 1
        if i % 249 == 0:
            t2 = time.time()
            t3 = t2 - t1
            if t3 < 60.0:
                time.sleep(60 - t3)
            t1 = time.time()'''

    @timed(use_seconds=True, precision=3)
    def three_factors_saver(self, Rmt, smb_hml):
        factors_on = pd.concat([Rmt, smb_hml], axis=1)
        factors_on = factors_on.reset_index()
        for factor in range(len(factors_on)):
            date = factors_on.iloc[factor][0]
            Rm_Rf = factors_on.iloc[factor][1]
            SMB = factors_on.iloc[factor][2]
            HML = factors_on.iloc[factor][3]

            sql = '''
                        insert ignore into factors_value(trade_date, Rm_Rf, SMB, HML) values(%s, %s, %s, %s)
                        '''
            cursor.execute(sql, (date, Rm_Rf, SMB, HML))
            db.commit()


    @timed(use_seconds=True, precision=3)
    def daily_basic_saver_five_factors(self, one_date, ts_list, fina_year, last_days):
        retry_count = 0
        for code in ts_list:
            try:
                df1 = pro.query('daily_basic', ts_code=code, trade_date=one_date,
                                fields='trade_date, ts_code, circ_mv, pb')
                df2 = pro.daily(ts_code=code, start_date=one_date, end_date=one_date)
                df3 = pro.query('fina_indicator', ts_code=code, start_date=fina_year, end_date=fina_year)
                df4 = pro.balancesheet(ts_code=code, start_date=last_days[int(fina_year[:4]) - 1].strftime('%Y%m%d'),
                                       end_date=fina_year)
                df5 = pro.balancesheet(ts_code=code, start_date=last_days[int(fina_year[:4]) - 2].strftime('%Y%m%d'),
                                       end_date=last_days[int(fina_year[:4]) - 1].strftime('%Y%m%d'))

                if df1.empty or df2.empty or df3.empty or df4.empty or df5.empty:
                    print('{} no data'.format(code))
                    continue

                total_assets_change_rate = (df4['total_assets'].iloc[0] - df5['total_assets'].iloc[0]) / df4['total_assets'].iloc[0]
                sql = '''
                        insert ignore into daily_basic_five_factors values(%s, %s, %s, %s, %s, %s, %s)
                        '''
                # replace into`user` ( `id`,`name`,`age` ) values ( 1, '张三', 30) 覆盖替换
                # insert ignore into `user` ( `id`, `name`, `age` ) values ( 1, '张三', 30) 去重，需要设置唯一约束

                cursor.execute(sql, (
                    df1['trade_date'].iloc[0], df1['ts_code'].iloc[0], df1['circ_mv'].iloc[0], df1['pb'].iloc[0],
                    df2['pct_chg'].iloc[0], df3['roe'].iloc[0], total_assets_change_rate))
                db.commit()
            except Exception as e:
                retry_count += 1
                print(f'出现异常：{e}，尝试第{retry_count}次重试，睡眠60秒')
                time.sleep(60)
        '''i += 1
        if i % 249 == 0:
            t2 = time.time()
            t3 = t2 - t1
            if t3 < 60.0:
                time.sleep(60 - t3)
            t1 = time.time()'''

    @timed(use_seconds=True, precision=3)
    def five_factors_saver(self, Rmt, smb_hml_rmw_cma):
        factors_on = pd.concat([Rmt, smb_hml_rmw_cma], axis=1)
        factors_on = factors_on.reset_index()
        factors_on = factors_on.where(pd.notna(factors_on), None)
        for factor in range(len(factors_on)):
            date = factors_on.iloc[factor][0]
            Rm_Rf = factors_on.iloc[factor][1]
            SMB = factors_on.iloc[factor][2]
            HML = factors_on.iloc[factor][3]
            RMW = factors_on.iloc[factor][4]
            CMA = factors_on.iloc[factor][5]

            sql = '''
                        insert ignore into factors_value_five_factors(trade_date, Rm_Rf, SMB, HML, RMW, CMA) values(%s, %s, %s, %s, %s, %s)
                        '''
            cursor.execute(sql, (date, Rm_Rf, SMB, HML, RMW, CMA))
            db.commit()
