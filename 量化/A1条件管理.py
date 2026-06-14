import tushare as ts
import pymysql
import pandas as pd
from dateutil import parser
from datetime import datetime
from timed_decorator.simple_timed import timed

db = pymysql.connect(host='localhost', user='root', password='123456', port=3306, db='stock_data')
# 创建数据库的游标
cursor = db.cursor()
ts.set_token('3f3c696116d8dbb7f9dbd53e598198e41c142216da03a9fc7ad56f89')
pro = ts.pro_api()

class ConditionArrangement:
    def __init__(self, start_date, end_date, index, s_strategy, q_strategy, Sa1):
        self.Sa1 = Sa1
        self.start_date = start_date
        self.end_date = end_date
        self.index = index
        self.s_strategy = s_strategy # stock
        self.q_strategy = q_strategy # quantify
        self.trade_date = self.date_translate(self.start_date, self.end_date) # 这个变量的是数据类型是list
        self.last_days = self.get_june_last_trading_days()  # 数据类型pandas Series, Timestamp


    # 把正常的时间范围转化成交易日
    def date_translate(self, start_date, end_date):
        df = pro.query('trade_cal', start_date=start_date, end_date=end_date, is_open=1)
        trade_date = df['cal_date'].tolist()
        trade_date.sort()
        return  trade_date

    def get_june_last_trading_days(self):
        start_date = self.start_date.replace(self.start_date[:4], str(int(self.start_date[:4]) - 3))
        trade_dates = self.date_translate(start_date, self.end_date)
        df = pd.DataFrame({'date': pd.to_datetime(trade_dates)})
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        june_dates = df[(df['month'] == 6)]
        last_days = june_dates.groupby('year')['date'].max()
        return last_days

    @timed(use_seconds=True, precision=3)
    # 判断数据库daily_basic表是否存储给定日期的数据
    def into_daily_basic(self):


        sql = '''
                select trade_date from daily_basic order by trade_date asc
                '''
        cursor.execute(sql)
        db_date = cursor.fetchall()
        # 空数据表处理
        if not db_date:
            if int(self.trade_date[0]) <= int(self.last_days[int(self.trade_date[0])].strftime('%Y%m%d')):
                fina_year = self.last_days[int(self.trade_date[0][:4]) - 1].strftime('%Y%m%d')
            else:
                fina_year = self.last_days[int(self.trade_date[0][:4])].strftime('%Y%m%d')
            ts_list = pro.index_weight(index_code=self.index, start_date=fina_year, end_date=fina_year)['con_code'].iloc[:299]
            for date in self.trade_date:
                one_date = date
                self.Sa1.daily_basic_saver(one_date, ts_list=ts_list)

                if one_date in self.last_days:
                    ts_list = pro.index_weight(index_code=self.index,
                                               start_date=self.last_days[int(one_date[:4])].strftime('%Y%m%d'),
                                               end_date=self.last_days[int(one_date[:4])].strftime('%Y%m%d'))['con_code'].iloc[:299]
            return
        df_date = pd.DataFrame(db_date, columns=['trade_date'])
        date = df_date['trade_date'].to_list()
        min_date = min(parser.parse(d) for d in date)
        min_date = min_date.strftime('%Y%m%d')

        max_date = max(parser.parse(d) for d in date)
        max_date = max_date.strftime('%Y%m%d')

        # 另一种选取最大日期方法，在下面的is_in_factors_value中有使用。需要在数据库中按日期升序排序order by trade_date asc
        # max_date = db_date[-1][0]
        print(f"数据库中最小的日期是：{min_date}")
        print(f'数据库中最大的日期是：{max_date}')

        if int(self.trade_date[0]) < int(min_date):

            trade_date = self.date_translate(self.start_date, min_date)
            print(f'股票数据进行本地化数据，缺少起始日期数据。数据库最小日期为：{min_date}')
            if int(self.trade_date[0]) <= int(self.last_days[int(self.trade_date[0][:4])].strftime('%Y%m%d')):
                fina_year = self.last_days[int(self.trade_date[0][:4]) - 1].strftime('%Y%m%d')
            else:
                fina_year = self.last_days[int(self.trade_date[0][:4])].strftime('%Y%m%d')
            ts_list = pro.index_weight(index_code=self.index, start_date=fina_year, end_date=fina_year)['con_code'].iloc[:299]
            for date in trade_date:
                one_date = date
                self.Sa1.daily_basic_saver(one_date, ts_list=ts_list)
                if one_date in self.last_days:
                    ts_list = pro.index_weight(index_code=self.index,
                                               start_date=self.last_days[int(one_date[:4])].strftime('%Y%m%d'),
                                               end_date=self.last_days[int(one_date[:4])].strftime('%Y%m%d'))['con_code'].iloc[:299]

        elif int(self.trade_date[-1]) > int(max_date):
            print(f'股票数据进行本地化数据，缺少结束日期数据。数据库最大日期为：{max_date}')
            trade_date = self.date_translate(max_date, self.end_date)
            if int(max_date) <= int(self.last_days[int(max_date[:4])].strftime('%Y%m%d')):
                fina_year = self.last_days[int(max_date[:4]) - 1].strftime('%Y%m%d')
            else:
                fina_year = self.last_days[int(max_date[:4])].strftime('%Y%m%d')
            ts_list = pro.index_weight(index_code=self.index, start_date=fina_year, end_date=fina_year)['con_code'].iloc[:299]
            for date in trade_date:
                one_date = date
                self.Sa1.daily_basic_saver(one_date, ts_list=ts_list)
                if one_date in self.last_days:
                    ts_list = pro.index_weight(index_code=self.index,
                                               start_date=self.last_days[int(one_date[:4])].strftime('%Y%m%d'),
                                               end_date=self.last_days[int(one_date[:4])].strftime('%Y%m%d'))['con_code'].iloc[:299]
            return

        else:
            return

    @timed(use_seconds=True, precision=3)
    def is_in_factors_value(self):
        sql = '''
                        select trade_date from factors_value order by trade_date asc
                        '''
        cursor.execute(sql)
        db_data = cursor.fetchall()

        if not db_data:
            print('因子值数据进行本地化')
            return False

        min_date =  db_data[0][0]
        max_date = db_data[-1][0]

        if self.start_date < min_date:
            print(f'因子值数据进行本地化。数据库最小日期为：{min_date}')
            return False

        elif self.end_date > max_date:
            print(f'因子值数据进行本地化。 数据库最大日期为：{max_date}')
            return False
        else:
            return True

    @timed(use_seconds=True, precision=3)
    # 判断数据库daily_basic表是否存储给定日期的数据
    def into_daily_basic_five_factors(self):

        sql = '''
                select trade_date from daily_basic_five_factors order by trade_date asc
                '''
        cursor.execute(sql)
        db_date = cursor.fetchall()
        # 空数据表处理
        if not db_date:
            if int(self.trade_date[0]) <= int(self.last_days[int(self.trade_date[0][:4])].strftime('%Y%m%d')):
                fina_year = self.last_days[int(self.trade_date[0][:4]) - 1].strftime('%Y%m%d')
            else:
                fina_year = self.last_days[int(self.trade_date[0][:4])].strftime('%Y%m%d')
            ts_list = pro.index_weight(index_code=self.index, start_date=fina_year, end_date=fina_year)['con_code'].iloc[:299]
            for date in self.trade_date:
                one_date = date
                self.Sa1.daily_basic_saver_five_factors(one_date, ts_list=ts_list, fina_year=fina_year,
                                                        last_days=self.last_days)

                if one_date in self.last_days:
                    ts_list = pro.index_weight(index_code=self.index,
                                               start_date=self.last_days[int(one_date[:4])].strftime('%Y%m%d'),
                                               end_date=self.last_days[int(one_date[:4])].strftime('%Y%m%d'))['con_code'].iloc[:299]
            return
        df_date = pd.DataFrame(db_date, columns=['trade_date'])
        date = df_date['trade_date'].to_list()
        min_date = min(parser.parse(d) for d in date)
        min_date = min_date.strftime('%Y%m%d')

        max_date = max(parser.parse(d) for d in date)
        max_date = max_date.strftime('%Y%m%d')

        # 另一种选取最大日期方法，在下面的is_in_factors_value中有使用。需要在数据库中按日期升序排序order by trade_date asc
        # max_date = db_date[-1][0]
        print(f"数据库中five_factors最小的日期是：{min_date}")
        print(f'数据库中five_factors最大的日期是：{max_date}')

        if int(self.trade_date[0]) < int(min_date):
            trade_date = self.date_translate(self.start_date, min_date)
            print(f'股票数据进行本地化数据，缺少起始日期数据。数据库最小日期为：{min_date}')
            if int(trade_date[0]) <= int(self.last_days[int(trade_date[0][:4])].strftime('%Y%m%d')):
                fina_year = self.last_days[int(trade_date[0][:4]) - 1].strftime('%Y%m%d')
            else:
                fina_year = self.last_days[int(trade_date[0][:4])].strftime('%Y%m%d')
            ts_list = pro.index_weight(index_code=self.index, start_date=fina_year, end_date=fina_year)['con_code'].iloc[:299]
            for date in trade_date:
                one_date = date
                self.Sa1.daily_basic_saver_five_factors(one_date, ts_list=ts_list, fina_year=fina_year,
                                                        last_days=self.last_days)

                ts_list = pro.index_weight(index_code=self.index,
                                           start_date=self.last_days[int(one_date[:4])].strftime('%Y%m%d'),
                                           end_date=self.last_days[int(one_date[:4])].strftime('%Y%m%d'))['con_code'].iloc[:299]

        elif int(self.trade_date[-1]) > int(max_date):
            print(f'股票数据进行本地化数据，缺少结束日期数据。数据库最大日期为：{max_date}')
            trade_date = self.date_translate(max_date, self.end_date)

            if int(max_date) <= int(self.last_days[int(max_date[:4])].strftime('%Y%m%d')):
                fina_year = self.last_days[int(max_date[:4]) - 1].strftime('%Y%m%d')
            else:
                fina_year = self.last_days[int(max_date[:4])].strftime('%Y%m%d')
            ts_list = pro.index_weight(index_code=self.index, start_date=fina_year, end_date=fina_year)['con_code'].iloc[:299]
            for date in trade_date:
                one_date = date
                self.Sa1.daily_basic_saver_five_factors(one_date, ts_list=ts_list, fina_year=fina_year,
                                                        last_days=self.last_days)

                if one_date in self.last_days:
                    ts_list = pro.index_weight(index_code=self.index,
                                               start_date=self.last_days[int(one_date[:4])].strftime('%Y%m%d'),
                                               end_date=self.last_days[int(one_date[:4])].strftime('%Y%m%d'))['con_code'].iloc[:299]
            return

        else:
            return


    @timed(use_seconds=True, precision=3)
    def is_in_factors_value_five_factors(self):
        sql = '''
                    select trade_date from factors_value_five_factors order by trade_date asc
                        '''
        cursor.execute(sql)
        db_data = cursor.fetchall()

        if not db_data:
            print('因子值数据进行本地化')
            return False

        min_date =  db_data[0][0]
        max_date = db_data[-1][0]

        if self.start_date < min_date:
            print(f'因子值数据进行本地化。数据库最小日期为：{min_date}')
            return False

        elif self.end_date > max_date:
            print(f'因子值数据进行本地化。 数据库最大日期为：{max_date}')
            return False
        else:
            return True
