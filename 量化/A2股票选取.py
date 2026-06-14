import numpy as np
import tushare as ts
import statsmodels.api as sm
import time
import pymysql
import pandas as pd
from datetime import datetime
from timed_decorator.simple_timed import timed
db = pymysql.connect(host='localhost', user='root', password='123456', port=3306, db='stock_data')
# 创建数据库的游标
cursor = db.cursor()
ts.set_token('3f3c696116d8dbb7f9dbd53e598198e41c142216da03a9fc7ad56f89')
pro = ts.pro_api()

class StockChoice:
    def __init__(self, index, trade_date, last_days, s_strategy, A1, Sa1):
        self.index = index
        self.trade_date = trade_date
        self.last_days = last_days
        self.s_strategy = s_strategy
        self.ts_list = []
        self.top_stocks = []
        self.expected_return = []
        self.A1 = A1
        self.Sa1 = Sa1

        self.s_strategy_choice()

    def s_strategy_choice(self):
        s_method_map = {
            'Fama三因子': self.three_factors,
            'Fama五因子': self.five_factors
        }
        if self.s_strategy in s_method_map:
            s_method_map[self.s_strategy]()

    @timed(use_seconds=True, precision=3)
    def stock_filter(self, fina_year):
        stock_basic = pro.index_weight(index_code=self.index, start_date=fina_year, end_date=fina_year).iloc[:299]
        # i = 0
        j = 0
        ts_list = []
        for ts_code in stock_basic['con_code']:
            # time.time()用于程序计时，避免访问接口过于频繁
            # t1 = time.time()
            df1 = pro.query('stock_basic', ts_code=ts_code, exchange='', list_status='L',
                            fields='ts_code,symbol,name,area,industry,list_date')
            if df1.empty:
                # print(f"No stock_basic data for {ts_code}")
                continue
            df1.dropna()
            industry = df1['industry'].loc[0] # 剔除金融行业——银行、保险、证券
            current_year = time.localtime().tm_year
            list_date = current_year - int(df1['list_date'].loc[0][:4]) # 计算上市时间
            name = df1['name'].loc[0] # 剔除ST股票
            # 剔除财务数据异常的公司，如资产负债率大于等于1
            df2 = pro.query('fina_indicator', ts_code=ts_code, start_date=fina_year, end_date=fina_year)
            if df2.empty:
                print(f"No financial data for {ts_code}")
                continue
            debt_to_assets = df2['debt_to_assets'][0]  # 财务杠杆
            if industry not in ['银行', '保险', '证券']:
                # 剔除上市不满一年的公司
                if list_date > 1:
                    if 'ST' not in name:
                        if debt_to_assets < 100:
                            j += 1
                            ts_list.append(df1['ts_code'].loc[0])
        ''' i += 1
            if i == 199:
                t2 = time.time() - t1
                time.sleep(60 - t2) 目前不用，访问次数不会触发访问频繁'''
        # 可将数据写入到excel表
        # df.to_excel(r'C:\Users\a\Desktop\index{}.xlsx'.format(start_date))
        print('{}只股票'.format(j))
        return ts_list



    # 三因子1: 使用本地数据
    def calculate_three_factor_1(self, one_date):

        valid_codes = []
        circ_mv = []
        pb = []
        pct_chg = []

        if not self.ts_list:
            print("股票列表为空，无法计算三因子")

        # 批量查询所有股票数据
        placeholders = ','.join(['%s'] * len(self.ts_list))
        sql = f'''
                SELECT * FROM daily_basic 
                WHERE trade_date = %s AND ts_code IN ({placeholders})
            '''
        cursor.execute(sql, [one_date] + self.ts_list)
        all_data = cursor.fetchall()
        # 转换为 DataFrame 并处理
        df_batch = pd.DataFrame(all_data, columns=['trade_date', 'ts_code', 'circ_mv', 'pb', 'pct_chg'])
        if df_batch.empty:
            print(f'数据库缺少{one_date}的daily_basic数据,尝试进行数据本地化')
            temp_date = one_date.replace(one_date[4:], '1231') # one_date所属年份的末尾
            print(f'尝试将下载从{one_date}-->{temp_date}的数据')
            temp_trade_date_list = self.A1.date_translate(one_date, temp_date)
            ts_list = self.ts_list
            for date in temp_trade_date_list:
                self.Sa1.daily_basic_saver(date, ts_list=ts_list)
                if date in self.last_days:
                    ts_list = pro.index_weight(index_code=self.index,
                                               start_date=self.last_days[int(one_date[:4])].strftime('%Y%m%d'),
                                               end_date=self.last_days[int(one_date[:4])].strftime('%Y%m%d')).iloc[:299]

        # 按股票代码分组提取数据
        for code in self.ts_list:
            df_stock = df_batch[df_batch['ts_code'] == code]
            if df_stock.empty:
                continue
            valid_codes.append(code)
            pct_chg.append(df_stock['pct_chg'].iloc[0])
            circ_mv.append(df_stock['circ_mv'].iloc[0])
            pb.append(df_stock['pb'].iloc[0])


        data = {'ts_code': valid_codes, 'pct_chg': pct_chg, 'circ_mv': circ_mv, 'pb': pb}
        df = pd.DataFrame(data)
        #  清理数据
        df = df.replace([float('inf'), -float('inf')], np.nan).dropna()

        # 计算中位数
        median_mv = df['circ_mv'].median()
        # 根据中位数分类
        # df['SB'] = df['circ_mv'].map(lambda x: 'B' if x >= median_mv else 'S')
        df['SB'] = np.where(df['circ_mv'] >= median_mv, 'B', 'S')
        # print(df)
        # 求账面市值比：PB的倒数
        df['BM'] = 1 / df['pb']

        # 划分高中低账面市值比公司
        # 使用了 quantile() 方法来计算账面市值比 'BM' 列的分位数，传递给 quantile() 方法的参数是一个包含两个分位数的列表 [0.3, 0.7]。
        # 方法返回一个包含两个元素的 pandas Series，第一个元素是 'BM' 列的 30% 分位数，第二个元素是 'BM' 列的 70% 分位数。
        # 将返回的 Series 解包为两个变量 border_down 和 border_up。
        #  L（low，< 30%）、M（medium，[30%，70%]）、H（high，>70%）

        border_down, border_up = df['BM'].quantile([0.3, 0.7])
        df['HML'] = df['BM'].map(lambda x: 'H' if x >= border_up else 'M')
        # axis=0表示对DataFrame的行进行操作，而axis=1表示对列进行操作。
        df['HML'] = df.apply(lambda row: 'L' if row['BM'] <= border_down else row['HML'], axis=1)

        # 组合划分为6组
        # query() 函数是一种用于过滤 DataFrame 的方法。它可以根据特定条件从 DataFrame 中选择数据，并返回符合条件的子集。
        df_SL = df.query('(SB=="S") & (HML == "L")')
        df_SM = df.query('(SB=="S") & (HML == "M")')
        df_SH = df.query('(SB=="S") & (HML == "H")')
        df_BL = df.query('(SB=="B") & (HML == "L")')
        df_BM = df.query('(SB=="B") & (HML == "M")')
        df_BH = df.query('(SB=="B") & (HML == "H")')

        # 计算各组收益率 pct_chg:真实涨跌幅(复权后的涨跌幅)
        R_SL = (df_SL['pct_chg'] * df_SL['circ_mv']).sum() / df_SL['circ_mv'].sum()
        R_SM = (df_SM['pct_chg'] * df_SM['circ_mv']).sum() / df_SM['circ_mv'].sum()
        R_SH = (df_SH['pct_chg'] * df_SH['circ_mv']).sum() / df_SH['circ_mv'].sum()
        R_BL = (df_BL['pct_chg'] * df_BL['circ_mv']).sum() / df_BL['circ_mv'].sum()
        R_BM = (df_BM['pct_chg'] * df_BM['circ_mv']).sum() / df_BM['circ_mv'].sum()
        R_BH = (df_BH['pct_chg'] * df_BH['circ_mv']).sum() / df_BH['circ_mv'].sum()

        # 计算SMB,HML并返回
        # SMB 因子的计算公式是：(R_SL + R_SM + R_SH - R_BL -R_BM - R_BH) / 3，表示小市值公司收益率减去大市值公司收益率的平均值。
        # 而 HML 因子的计算公式是：(R_SH + R_BH - R_SL - R_BL ) / 2，表示高价值公司收益率减去低价值公司收益率的平均值。
        smb = (R_SL + R_SM + R_SH - R_BL - R_BM - R_BH) / 3
        hml = (R_SH + R_BH - R_SL - R_BL) / 2
        return smb, hml

    # 三因子2：使用在线数据 2025.7.17后续可以改成saver
    # 2026.04.26: 目前没有计划

    # 计算多个日期的SMB和HML
    @timed(use_seconds=True, precision=3)
    def calculate_factors_for_dates(self):
        results = []
        if int(self.trade_date[0]) <= int(self.last_days[int(self.trade_date[0][:4])].strftime('%Y%m%d')):
            fina_year = self.last_days[int(self.trade_date[0][:4]) - 1].strftime('%Y%m%d')
        else:
            fina_year = self.last_days[int(self.trade_date[0][:4])].strftime('%Y%m%d')
        self.ts_list = self.stock_filter(fina_year)
        for date in self.trade_date:
            one_date = date
            smb, hml = self.calculate_three_factor_1(one_date)
            results.append({'date': date, 'SMB': smb, 'HML': hml})

            # 更新财报日期
            if one_date in self.last_days:
                fina_year = int(one_date[:4])
                self.ts_list = self.stock_filter(fina_year)
        sml_hml = pd.DataFrame(results)
        sml_hml = sml_hml.set_index('date')
        return sml_hml

    @timed(use_seconds=True, precision=3)
    def three_factors(self):
        columns_to_add = []
        start_date = self.trade_date[0]
        end_date = self.trade_date[-1]
        print(start_date)
        print(end_date)
        self.A1.into_daily_basic()
        # 因子值计算
        smb_hml = self.calculate_factors_for_dates()
        print(len(self.ts_list))
        for code in self.ts_list:
            sql = '''
                   SELECT trade_date, pct_chg 
                   FROM daily_basic 
                   WHERE trade_date BETWEEN %s AND %s 
                   AND ts_code = %s
                   ORDER BY trade_date
               '''
            cursor.execute(sql, (start_date, end_date, code))
            all_d = cursor.fetchall()

            if not all_d:
                print(f'Warning: No pct_chg data for {code} in date range {start_date} to {end_date}')
                continue

            # 更高效的数据提取方式
            temp_frame = pd.DataFrame(all_d,columns=['trade_date', 'pct_chg'])
            time_stamp = pd.to_datetime(temp_frame['trade_date'])
            temp_frame = temp_frame[['pct_chg']]
            temp_frame.index = time_stamp
            temp_frame.columns = [code]  # 使用股票代码作为列名
            temp_frame.sort_index(inplace=True)
            columns_to_add.append(temp_frame)
        # 在循环结束后，一次性使用 pd.concat 合并所有列
        try:
            stock_return_data = pd.concat(columns_to_add, axis=1, verify_integrity=True)
            # print(f'个股每日收益率:\n{stock_return_data}')
        except ValueError as e:
            print(f"合并数据时出错: {str(e)}")
            # 如果合并失败，尝试不验证完整性
            stock_return_data = pd.concat(columns_to_add, axis=1)
            # 去除重复行
            stock_return_data = stock_return_data[~stock_return_data.index.duplicated(keep='first')]
        # 在 return_rate 函数中，检查 stock_return_data 是否有缺失值
        stock_return_data = stock_return_data.apply(pd.to_numeric, errors='coerce')

        market_return = pro.query('index_daily', ts_code=self.index, start_date=start_date, end_date=end_date,
                                  adj='qfq').set_index('trade_date')['pct_chg']
        market_return.name = 'market_return'
        market_return.sort_index(inplace=True)

        Rmt = pd.DataFrame()
        # 市场风险溢酬因子(Rmt)
        # rate_free为3月期的国债利率
        rate_free = pd.DataFrame()
        for year in range(int(start_date[:4]), int(end_date[:4]) + 1):
            df = pd.read_excel(f'D:/{year}国债收益率.xlsx') # 每日国债收益率
            data = df[['标准期限说明', '收益率(%)']]
            data.columns = ['period', 'pct_chg']
            data.index = pd.to_datetime(df['日期'])
            data.index.name = 'date'
            temp_m_3 = data[data['period'] == '3m']['pct_chg']
            rate_free = pd.concat([rate_free, temp_m_3])

        market_return.index = pd.to_datetime(market_return.index)
        rate_free = rate_free.loc[market_return.index]
        Rmt['Rm_Rf'] =( market_return - rate_free['pct_chg'])

        # 因子值存储
        if not self.A1.is_in_factors_value():
            self.Sa1.three_factors_saver(Rmt, smb_hml)

        # 因子值读取
        sql = '''select * from factors_value'''
        cursor.execute(sql)
        raw_data = cursor.fetchall()

        factors = pd.DataFrame(raw_data, columns=['trade_date', 'Rm_Rf', 'SMB', 'HML'])
        factors_timestamp = pd.to_datetime(factors['trade_date'])
        factors = factors[['Rm_Rf', 'SMB', 'HML']]
        factors.index = factors_timestamp
        factors.columns = ['Rm_Rf', 'SMB', 'HML']
        factors.sort_index(inplace=True)

        # 确保索引对齐
        common_index = stock_return_data.index.intersection(factors.index)
        stock_return_data = stock_return_data.loc[common_index]
        factors = factors.loc[common_index]
        results = {}

        for stock in stock_return_data.columns:
            stock_returns = (stock_return_data[stock] - rate_free['pct_chg'])  # 被解释变量：股票盈利
            if stock_returns.isnull().values.any():
                # print(f"stock {stock} has NaN values in stock_returns >>> dropna.")
                stock_returns = stock_returns.dropna()

            X_factors = factors.loc[stock_returns.index]
            model = sm.OLS(stock_returns, X_factors).fit()
            # 检查回归的R-squared和残差
            print(f"R-squared: {model.rsquared}")
            print(f"残差均值: {model.resid.mean()}")  # 应该接近0
            results[stock] = model.params
        print(f'因子系数\n{len(results)}')
        # 预期收益率计算
        expected_returns = {}
        for stock, params in results.items():
            expected_return = (params['Rm_Rf'] * (factors['Rm_Rf'].mean())
                                + params['SMB'] * factors['SMB'].mean() + params['HML'] * factors['HML'].mean())
            expected_returns[stock] = float(expected_return)

        # 选择预期收益率最高的股票
        sorted_stock = sorted(expected_returns.keys(), key=lambda x: expected_returns[x], reverse=True)[:10]
        sorted_return = sorted(expected_returns.values(), reverse=True)[:10]
        self.top_stocks = sorted_stock
        self.expected_return = sorted_return

        print('选取股票:{}, 预期收益率:{}\n'.format('\n'.join(map(str, self.top_stocks)), '\n'.join(map(str, self.expected_return))))
    # 2025.7.11还没考虑到数据不在数据库的情况

    # 五因子: 使用本地数据
    def calculate_five_factor(self, one_date, fina_year):

        valid_codes = []
        circ_mv = []
        pb = []
        pct_chg = []
        roe = []
        total_assets_change_rate = []

        if not self.ts_list:
            print("股票列表为空，无法计算三因子")

        # 批量查询所有股票数据
        placeholders = ','.join(['%s'] * len(self.ts_list))
        sql = f'''
                SELECT * FROM daily_basic_five_factors 
                WHERE trade_date = %s AND ts_code IN ({placeholders})
            '''
        cursor.execute(sql, [one_date] + self.ts_list)
        all_data = cursor.fetchall()
        # 转换为 DataFrame 并处理
        df_batch = pd.DataFrame(all_data, columns=['trade_date', 'ts_code', 'circ_mv', 'pb', 'pct_chg', 'roe', 'total_assets_change_rate'])
        if df_batch.empty:
            print(f'数据库缺少{one_date}的daily_basic数据,尝试进行数据本地化')
            temp_date = one_date.replace(one_date[4:], '1231') # one_date所属年份的末尾
            print(f'尝试将下载从{one_date}-->{temp_date}的数据')
            temp_trade_date_list = self.A1.date_translate(one_date, temp_date)
            for date in temp_trade_date_list:
                self.Sa1.daily_basic_saver_five_factors(date, ts_list=self.ts_list, fina_year=fina_year,
                                                        last_days=self.last_days)

        # 按股票代码分组提取数据
        for code in self.ts_list:
            df_stock = df_batch[df_batch['ts_code'] == code]
            if df_stock.empty:
                continue
            valid_codes.append(code)
            pct_chg.append(df_stock['pct_chg'].iloc[0])
            circ_mv.append(df_stock['circ_mv'].iloc[0])
            pb.append(df_stock['pb'].iloc[0])
            roe.append(df_stock['roe'].iloc[0])
            total_assets_change_rate.append(df_stock['total_assets_change_rate'].iloc[0])

        data = {'ts_code': valid_codes, 'pct_chg': pct_chg, 'circ_mv': circ_mv, 'pb': pb, 'roe': roe,
                'total_assets_change_rate': total_assets_change_rate}
        df = pd.DataFrame(data)
        #  清理数据
        df = df.replace([float('inf'), -float('inf')], np.nan).dropna()

        # 计算中位数
        median_mv = df['circ_mv'].median()
        # 根据中位数分类
        # df['SB'] = df['circ_mv'].map(lambda x: 'B' if x >= median_mv else 'S')
        df['SB'] = np.where(df['circ_mv'] >= median_mv, 'B', 'S')
        # print(df)
        # 求账面市值比：PB的倒数
        df['BM'] = 1 / df['pb']

        # 划分高中低账面市值比公司
        # 使用了 quantile() 方法来计算账面市值比 'BM' 列的分位数，传递给 quantile() 方法的参数是一个包含两个分位数的列表 [0.3, 0.7]。
        # 方法返回一个包含两个元素的 pandas Series，第一个元素是 'BM' 列的 30% 分位数，第二个元素是 'BM' 列的 70% 分位数。
        # 将返回的 Series 解包为两个变量 border_down 和 border_up。
        #  L（low，< 30%）、M（medium，[30%，70%]）、H（high，>70%）

        border_down, border_up = df['BM'].quantile([0.3, 0.7])
        df['HML'] = df['BM'].map(lambda x: 'H' if x >= border_up else 'M')
        # axis=0表示对DataFrame的行进行操作，而axis=1表示对列进行操作。
        df['HML'] = df.apply(lambda row: 'L' if row['BM'] <= border_down else row['HML'], axis=1)


        # 组合划分为6组
        # query() 函数是一种用于过滤 DataFrame 的方法。它可以根据特定条件从 DataFrame 中选择数据，并返回符合条件的子集。
        border_down_roe, border_up_roe = df['roe'].quantile([0.3, 0.7])
        df['RMW'] = df['roe'].map(lambda x: 'R' if x >= border_up_roe else 'M')
        df['RMW'] = df.apply(lambda row: 'W' if row['roe'] < border_down_roe else row['RMW'], axis=1)

        border_down_acr, border_up_acr = df['total_assets_change_rate'].quantile([0.3, 0.7])
        df['CMA'] = df['total_assets_change_rate'].map(lambda x: 'A' if x >= border_up_acr else 'M')
        df['CMA'] = df.apply(lambda row: 'C' if row['total_assets_change_rate'] < border_down_acr else row['CMA'],
                                 axis=1)

        SL_hml = df.query('(SB=="S") & (HML == "L")')
        SM_hml = df.query('(SB=="S") & (HML == "M")')
        SH_hml = df.query('(SB=="S") & (HML == "H")')
        BL_hml = df.query('(SB=="B") & (HML == "L")')
        BM_hml = df.query('(SB=="B") & (HML == "M")')
        BH_hml = df.query('(SB=="B") & (HML == "H")')

        SR_roe = df.query('(SB=="S") & (RMW == "R")')
        SM_roe = df.query('(SB=="S") & (RMW == "M")')
        SW_roe = df.query('(SB=="S") & (RMW == "W")')
        BR_roe = df.query('(SB=="B") & (RMW == "R")')
        BM_roe = df.query('(SB=="B") & (RMW == "M")')
        BW_roe = df.query('(SB=="B") & (RMW == "W")')

        SC_cma = df.query('(SB=="S") & (CMA == "C")')
        SM_cma = df.query('(SB=="S") & (CMA == "M")')
        SA_cma = df.query('(SB=="S") & (CMA == "A")')
        BC_cma = df.query('(SB=="B") & (CMA == "C")')
        BM_cma = df.query('(SB=="B") & (CMA == "M")')
        BA_cma = df.query('(SB=="B") & (CMA == "A")')

        R_SL_hml = (SL_hml['pct_chg'] * SL_hml['circ_mv']).sum() / SL_hml['circ_mv'].sum()
        R_SM_hml = (SM_hml['pct_chg'] * SM_hml['circ_mv']).sum() / SM_hml['circ_mv'].sum()
        R_SH_hml = (SH_hml['pct_chg'] * SH_hml['circ_mv']).sum() / SH_hml['circ_mv'].sum()
        R_BL_hml = (BL_hml['pct_chg'] * BL_hml['circ_mv']).sum() / BL_hml['circ_mv'].sum()
        R_BM_hml = (BM_hml['pct_chg'] * BM_hml['circ_mv']).sum() / BM_hml['circ_mv'].sum()
        R_BH_hml = (BH_hml['pct_chg'] * BH_hml['circ_mv']).sum() / BH_hml['circ_mv'].sum()
        R_SR_roe = (SR_roe['pct_chg'] * SR_roe['circ_mv']).sum() / SR_roe['circ_mv'].sum()
        R_SM_roe = (SM_roe['pct_chg'] * SM_roe['circ_mv']).sum() / SM_roe['circ_mv'].sum()
        R_SW_roe = (SW_roe['pct_chg'] * SW_roe['circ_mv']).sum() / SW_roe['circ_mv'].sum()
        R_BR_roe = (BR_roe['pct_chg'] * BR_roe['circ_mv']).sum() / BR_roe['circ_mv'].sum()
        R_BM_roe = (BM_roe['pct_chg'] * BM_roe['circ_mv']).sum() / BM_roe['circ_mv'].sum()
        R_BW_roe = (BW_roe['pct_chg'] * BW_roe['circ_mv']).sum() / BW_roe['circ_mv'].sum()
        R_SC_cma = (SC_cma['pct_chg'] * SC_cma['circ_mv']).sum() / SC_cma['circ_mv'].sum()
        R_SM_cma = (SM_cma['pct_chg'] * SM_cma['circ_mv']).sum() / SM_cma['circ_mv'].sum()
        R_SA_cma = (SA_cma['pct_chg'] * SA_cma['circ_mv']).sum() / SA_cma['circ_mv'].sum()
        R_BC_cma = (BC_cma['pct_chg'] * BC_cma['circ_mv']).sum() / BC_cma['circ_mv'].sum()
        R_BM_cma = (BM_cma['pct_chg'] * BM_cma['circ_mv']).sum() / BM_cma['circ_mv'].sum()
        R_BA_cma = (BA_cma['pct_chg'] * BA_cma['circ_mv']).sum() / BA_cma['circ_mv'].sum()

        SMB_HML = (R_SL_hml + R_SM_hml + R_SH_hml - R_BL_hml - R_BM_hml - R_BH_hml) / 3
        SMB_RMW = (R_SR_roe + R_SM_roe + R_SW_roe - R_BR_roe - R_BM_roe - R_BW_roe) / 3
        SMB_CMA = (R_SC_cma + R_SM_cma + R_SA_cma - R_BC_cma - R_BM_cma - R_BA_cma) / 3

        smb = (SMB_CMA + SMB_RMW + SMB_HML) / 3
        hml = (SH_hml + BH_hml - SL_hml - BL_hml) / 2
        rmw = (SR_roe + BR_roe - SW_roe - BW_roe) / 2
        cma = (SC_cma + BC_cma - SA_cma - BA_cma) / 2

        return smb, hml, rmw, cma

    # 三因子2：使用在线数据 2025.7.17后续可以改成saver
    # 2026.04.26: 目前没有计划

    # 计算多个日期的SMB和HML
    @timed(use_seconds=True, precision=3)
    def calculate_five_factors_for_dates(self):
        results = []
        if int(self.trade_date[0]) <= int(self.last_days[int(self.trade_date[0][:4])].strftime('%Y%m%d')):
            fina_year = self.last_days[int(self.trade_date[0][:4]) - 1].strftime('%Y%m%d')
        else:
            fina_year = self.last_days[int(self.trade_date[0][:4])].strftime('%Y%m%d')
        self.ts_list = self.stock_filter(fina_year)
        for date in self.trade_date:
            one_date = date
            smb, hml, rmw, cma = self.calculate_five_factor(one_date, fina_year)
            results.append({'date': date, 'SMB': smb, 'HML': hml, 'RMW': rmw, 'CMA': cma})

            # 更新财报日期
            if one_date in self.last_days:
                fina_year = self.last_days[int(one_date[:4])].strftime('%Y%m%d')
                self.ts_list = self.stock_filter(fina_year)

        sml_hml_rmw_cma = pd.DataFrame(results)
        sml_hml_rmw_cma = sml_hml_rmw_cma.set_index('date')
        return sml_hml_rmw_cma

    @timed(use_seconds=True, precision=3)
    def five_factors(self):
        columns_to_add = []
        start_date = self.trade_date[0]
        end_date = self.trade_date[-1]
        print(start_date)
        print(end_date)
        self.A1.into_daily_basic_five_factors()
        # 因子值计算
        smb_hml_rmw_cma = self.calculate_five_factors_for_dates()
        print(len(self.ts_list))
        for code in self.ts_list:
            sql = '''
                   SELECT trade_date, pct_chg 
                   FROM daily_basic_five_factors 
                   WHERE trade_date BETWEEN %s AND %s 
                   AND ts_code = %s
                   ORDER BY trade_date
               '''
            cursor.execute(sql, (start_date, end_date, code))
            all_d = cursor.fetchall()

            if not all_d:
                print(f'Warning: No pct_chg data for {code} in date range {start_date} to {end_date}')
                continue

            # 更高效的数据提取方式
            temp_frame = pd.DataFrame(all_d,columns=['trade_date', 'pct_chg'])
            time_stamp = pd.to_datetime(temp_frame['trade_date'])
            temp_frame = temp_frame[['pct_chg']]
            temp_frame.index = time_stamp
            temp_frame.columns = [code]  # 使用股票代码作为列名
            temp_frame.sort_index(inplace=True)
            columns_to_add.append(temp_frame)
        # 在循环结束后，一次性使用 pd.concat 合并所有列
        try:
            stock_return_data = pd.concat(columns_to_add, axis=1, verify_integrity=True)
            # print(f'个股每日收益率:\n{stock_return_data}')
        except ValueError as e:
            print(f"合并数据时出错: {str(e)}")
            # 如果合并失败，尝试不验证完整性
            stock_return_data = pd.concat(columns_to_add, axis=1)
            # 去除重复行
            stock_return_data = stock_return_data[~stock_return_data.index.duplicated(keep='first')]
        # 在 return_rate 函数中，检查 stock_return_data 是否有缺失值
        stock_return_data = stock_return_data.apply(pd.to_numeric, errors='coerce')
        market_return = pro.query('index_daily', ts_code=self.index, start_date=start_date, end_date=end_date,
                                  adj='qfq').set_index('trade_date')['pct_chg']
        market_return.name = 'market_return'
        market_return.sort_index(inplace=True)

        Rmt = pd.DataFrame()
        # 市场风险溢酬因子(Rmt)
        # rate_free为3月期的国债利率
        rate_free = pd.DataFrame()
        for year in range(int(start_date[:4]), int(end_date[:4]) + 1):
            df = pd.read_excel(f'D:/{year}国债收益率.xlsx')
            data = df[['标准期限说明', '收益率(%)']]
            data.columns = ['period', 'pct_chg']
            data.index = pd.to_datetime(df['日期'])
            data.index.name = 'date'
            temp_m_3 = data[data['period'] == '3m']['pct_chg']
            rate_free = pd.concat([rate_free, temp_m_3])

        rate_free = rate_free.loc[market_return.index]

        Rmt['Rm_Rf'] = market_return - rate_free['pct_chg']

        # 因子值存储
        if not self.A1.is_in_factors_value_five_factors():
            self.Sa1.five_factors_saver(Rmt, smb_hml_rmw_cma=smb_hml_rmw_cma)

        # 因子值读取
        sql = '''select * from factors_value_five_factors'''
        cursor.execute(sql)
        raw_data = cursor.fetchall()

        factors = pd.DataFrame(raw_data, columns=['trade_date', 'Rm_Rf', 'SMB', 'HML', 'RMW', 'CMA'])
        factors_timestamp = pd.to_datetime(factors['trade_date'])
        factors = factors[['Rm_Rf', 'SMB', 'HML', 'RMW', 'CMA']]
        factors.index = factors_timestamp
        factors.columns = ['Rm_Rf', 'SMB', 'HML', 'RMW', 'CMA']
        factors.sort_index(inplace=True)

        # 确保索引对齐
        common_index = stock_return_data.index.intersection(factors.index)
        stock_return_data = stock_return_data.loc[common_index]
        factors = factors.loc[common_index]
        results = {}

        for stock in stock_return_data.columns:
            stock_returns = stock_return_data[stock] - rate_free['pct_chg'] # 被解释变量：股票盈利
            if stock_returns.isnull().values.any():
                # print(f"stock {stock} has NaN values in stock_returns >>> dropna.")
                stock_returns = stock_returns.dropna()

            X_factors = factors.loc[stock_returns.index]
            model = sm.OLS(stock_returns, X_factors).fit()
            # 检查回归的R-squared和残差
            print(f"R-squared: {model.rsquared}")
            print(f"残差均值: {model.resid.mean()}")  # 应该接近0
            results[stock] = model.params

        print(f'因子系数\n{len(results)}')
        # 预期收益率计算
        expected_returns = {}
        for stock, params in results.items():
            expected_return = (params['Rm_Rf'] * (factors['Rm_Rf'].mean())
                               + params['SMB'] * factors['SMB'].mean() + params['HML'] * factors['HML'].mean()
                               + params['RMW'] * factors['RMW'].mean() + params['CMA'] * factors['CMA'].mean())
            expected_returns[stock] = float(expected_return)


        # 选择预期收益率最高的股票
        sorted_stock = sorted(expected_returns.keys(), key=lambda x: expected_returns[x], reverse=True)[:10]
        sorted_return = sorted(expected_returns.values(), reverse=True)[:10]
        self.top_stocks = sorted_stock
        self.expected_return = sorted_return

        print('选取股票:{}, 预期收益率:{}\n'.format('\n'.join(map(str, self.top_stocks)), '\n'.join(map(str, self.expected_return))))
