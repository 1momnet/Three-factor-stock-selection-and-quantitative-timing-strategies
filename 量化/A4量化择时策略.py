
import tushare as ts
import backtrader as bt
import pandas as pd
from timed_decorator.simple_timed import timed

ts.set_token('3f3c696116d8dbb7f9dbd53e598198e41c142216da03a9fc7ad56f89')
pro = ts.pro_api()

# 均值回归策略
class BollStrategy(bt.Strategy):

    params = (('boll_period', 20),('weight', 0.95))

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.lines.top = bt.indicators.BollingerBands(self.dataclose, period=self.p.boll_period).top
        self.lines.bot = bt.indicators.BollingerBands(self.dataclose, period=self.p.boll_period).bot

        self.signal_position = 0


    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:  # 如订单已被处理，则不用做任何事情
            return
        if order.status in [order.Completed]:  # # 检查订单是否完成
            if order.isbuy():
                print(
                    '{}布林线策略\n买入, 价格: {:.2f}, 成本: {:.2f}, 佣金: {:.2f}'.format
                    (self.datas[0].datetime.date(0),
                     order.executed.price,
                     order.executed.value,
                     order.executed.comm))
            else:
                print(
                    '{}布林线策略\n卖出, 价格: {:.2f}, 成本: {:.2f}, 佣金: {:.2f}'.format
                    (self.datas[0].datetime.date(0),
                     order.executed.price,
                     order.executed.value,
                     order.executed.comm))

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            print('Order Canceled/Margin/Rejected')
        self.order = None  # 订单状态处理完成，设为空

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        print('boll操作收益, 毛利润: {:.2f}, 净利润: {:.2f}'.format(trade.pnl, trade.pnlcomm))

    def next(self):
        if self.order:  # 是否正在下单，如果是的话不能提交第二次订单
            return
        # 检查持仓
        if self.signal_position < 1 - self.p.weight:
            # 没有持仓，买入开仓
            if self.dataclose <= self.lines.bot[0]:
                self.signal_position += self.p.weight
                print(f'布林线策略资金:{self.broker.getvalue()}')
                self.order = self.order_target_percent(target=self.signal_position)
        if self.signal_position > 0:
            # 手里有持仓，判断卖平
            if self.dataclose >= self.lines.top[0]:
                self.signal_position = 0
                self.order = self.order_target_percent(target=0)



# 动量策略
class MomentumStrategy(bt.Strategy):
    params = (('rsi_period', 14), ('over_bought', 70), ('over_sold', 30), ('weight', 0.95))

    def __init__(self):
        self.order = None
        self.rsi = bt.indicators.RSI(self.datas[0], period=self.p.rsi_period)
        self.signal_position = 0

    def next(self):
        if self.order:
            return
        if self.signal_position < 1 - self.p.weight:
            if self.rsi[0] < self.p.over_sold :
                self.signal_position += self.p.weight
                print(f'momentum策略资金:{self.broker.getvalue()}')
                self.order = self.order_target_percent(target=self.signal_position)
        if self.signal_position > 0:
            if self.rsi[0] > self.p.over_bought:
                self.signal_position = 0
                self.order = self.order_target_percent(target=0)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:  # 如订单已被处理，则不用做任何事情
            return
        if order.status in [order.Completed]:  # # 检查订单是否完成
            if order.isbuy():
                print(
                    '动量策略\n买入, 价格: {:.2f}, 成本: {:.2f}, 佣金: {:.2f}'.format
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))
            else:
                print(
                    '动量策略\n卖出, 价格: {:.2f}, 成本: {:.2f}, 佣金: {:.2f}'.format
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            print('Order Canceled/Margin/Rejected')
        self.order = None  # 订单状态处理完成，设为空

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        print('momentum操作收益, 毛利润: {:.2f}, 净利润: {:.2f}'.format(trade.pnl, trade.pnlcomm))



#趋势跟踪策略
class TrendFollowingStrategy(bt.Strategy):
    """使用均线交叉的趋势跟踪策略。"""

    params = (('fast_period', 10), ('slow_period', 30), ('weight', 0.95))

    def __init__(self, weight=0.95):
        self.order = None
        self.fast_ma = bt.indicators.SMA(self.datas[0], period=self.p.fast_period)
        self.slow_ma = bt.indicators.SMA(self.datas[0], period=self.p.slow_period)
        self.crossover = bt.ind.CrossOver(self.fast_ma, self.slow_ma)
        self.signal_position = 0

    def next(self):
        if self.order:
            return
        if self.signal_position < 1 - self.p.weight:
            if self.crossover[0] > 0 :
                self.signal_position += self.p.weight
                print(f'趋势策略资金:{self.broker.getvalue()}')
                self.order = self.order_target_percent(target=self.signal_position)
        if self.signal_position > 0:
            if self.crossover[0] < 0:
                self.signal_position = 0
                self.order = self.order_target_percent(target=0)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:  # 如订单已被处理，则不用做任何事情
            return
        if order.status in [order.Completed]:  # # 检查订单是否完成
            if order.isbuy():
                print(
                    '趋势跟踪策略\n买入, 价格: {:.2f}, 成本: {:.2f}, 佣金: {:.2f}'.format
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))
            else:
                print(
                    '趋势跟踪策略\n卖出, 价格: {:.2f}, 成本: {:.2f}, 佣金: {:.2f}'.format
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            print('Order Canceled/Margin/Rejected')
        self.order = None  # 订单状态处理完成，设为空

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        print('趋势跟踪--操作收益, 毛利润: {:.2f}, 净利润: {:.2f}'.format(trade.pnl, trade.pnlcomm))




class QuantifyData:
    def acquire_data(self, stock, start_date, end_date):
        df = ts.pro_bar(ts_code=stock, adj='qfq', start_date=start_date, end_date=end_date)
        dates = pd.to_datetime(df["trade_date"])
        df = df[["open", "high", "low", "close", "vol"]]
        df.columns = ['open', 'high', 'low', 'close', 'volume']
        df.index = dates
        df.sort_index(ascending=True, inplace=True)
        return df


def q_strategy_choice(q_strategy):
    q_method_map = {
        '布林线策略': BollStrategy,
        '多策略': '多策略',
        '动量策略': MomentumStrategy,
        '趋势跟踪策略SMA': TrendFollowingStrategy
    }
    return q_method_map.get(q_strategy)

@timed(use_seconds=True, precision=3)
def main_backtrade(top_stocks, qd_object, q_strategy, trade_back_start_date, tb_end_date):
    stock_profit_ratios = {}
    if q_strategy == '多策略':
        strategies_to_run = [
            ('布林线策略', BollStrategy, {'boll_period': 20}),
            ('动量策略', MomentumStrategy, {'rsi_period': 14}),
            ('趋势跟踪策略', TrendFollowingStrategy, {'fast_period': 10, 'slow_period': 30})
        ]
    else:
        # 单策略模式
        strategies_to_run = [('单策略', q_strategy, {})]

    for i in top_stocks:
        stock = i
        # today = datetime.now().strftime('%Y%m%d')
        # end_date_f = today
        print(stock)

        # 存储每个策略的收益率
        strategy_results = {}
        for strat_name, start_class, strat_params in strategies_to_run:
            print(f"\n--- 运行{strat_name} ---")
            # 实例化
            df = qd_object.acquire_data(stock, start_date=trade_back_start_date, end_date=tb_end_date)

            # 实例化 cerebro——引擎
            cerebro = bt.Cerebro()

            # 添加数据进cerebro
            data = bt.feeds.PandasData(dataname=df)
            cerebro.adddata(data)

            # 设置本金与佣金
            cerebro.broker.setcash(100000)
            cerebro.broker.setcommission(commission=0.001)
            # 添加交易策略——cerebro行动逻辑
            if strat_params:
                cerebro.addstrategy(start_class, **strat_params)
            else:
                cerebro.addstrategy(start_class)
            # 添加分析器
            cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
            cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
            cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
            cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
            cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='annual_return')

            # 添加观察器
            cerebro.addobserver(bt.observers.DrawDown)
            cerebro.addobserver(bt.observers.TimeReturn)

            # 运行
            results = cerebro.run()
            strat = results[0]

            # 打印结果
            print('*' * 54)
            print(f'{'结果分析':-^50}')
            print('*' * 54)
            # 打印结果
            returns = strat.analyzers.returns.get_analysis()
            sharpe = strat.analyzers.sharpe.get_analysis()
            drawdown = strat.analyzers.drawdown.get_analysis()
            trades = strat.analyzers.trades.get_analysis()
            annual_return = strat.analyzers.annual_return.get_analysis()

            print(f'初始资金: {cerebro.broker.startingcash:.2f}')
            print(f'最终资金: {cerebro.broker.getvalue():.2f}')
            print(f'收益率: {returns['rtot']:.2%}')
            print(f'平均收益率: {returns['ravg']:.2%}')
            print(f'最大回撤: {drawdown["max"]["drawdown"]:.2%}')
            print(f'最大回撤持续: {drawdown["max"]["len"]} 天')
            print(f'总交易次数: {trades["total"]["total"]}')
            # 检查夏普比率是否存在
            if sharpe.get('sharperatio'):
                print(f'夏普比率: {sharpe["sharperatio"]:.3f}')
            else:
                print('夏普比率: N/A')

            print(f'最大回撤: {drawdown["max"]["drawdown"]:.2%}')
            print(f'最大回撤持续: {drawdown["max"]["len"]} 天')

            # 检查 trades 字典中是否有交易记录
            if trades and 'total' in trades and trades['total'].get('total', 0) > 0:
                print(f'总交易次数: {trades["total"]["total"]}')
                if 'won' in trades and trades['won'].get('total', 0) > 0:
                    print(f'胜率: {trades["won"]["total"] / trades["total"]["total"]:.2%}')
                else:
                    print('胜率: 0%')
            else:
                print('总交易次数: 0')
                print('胜率: N/A')

            if annual_return and 'rnorm' in annual_return:
                print(f'年化收益: {annual_return.get("rnorm", 0):.2%}')
            else:
                print('年化收益: N/A')

            strategy_results[strat_name] = round(returns["rtot"] * 100, 2)
            # 可视化回测结果
            cerebro.plot()

        # 计算平均收益率
        if strategy_results:
            avg_profit = sum(strategy_results.values()) / len(strategy_results)
            stock_profit_ratios[stock] = round(avg_profit, 2)
            print(f"\n{stock} 多策略平均收益率: {avg_profit:.2}%")

    print(stock_profit_ratios)
    return stock_profit_ratios

