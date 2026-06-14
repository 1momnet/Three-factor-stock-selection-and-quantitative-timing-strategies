from A1条件管理 import *
from A2股票选取 import *
from A3数据本地化saver import *
from A4量化择时策略 import *
from B2在险价值类 import *

def main_procedure(start_date, end_date, index, s_strategy, q_strategy, trade_back_start_date, trade_back_end_date):
    Sa1 = Saver()
    A1 = ConditionArrangement(start_date=start_date, end_date=end_date, index=index, s_strategy=s_strategy,
                              q_strategy=q_strategy, Sa1=Sa1)

    S1 = StockChoice(index=A1.index, trade_date=A1.trade_date, last_days=A1.last_days, s_strategy=A1.s_strategy, A1=A1, Sa1=Sa1)

    # 在险价值部分
    var_instance = Var(S1.top_stocks)
    var_instance.historical_simulation()

    # 回测部分
    Qd1 = QuantifyData()
    q_strategy = q_strategy_choice(q_strategy=A1.q_strategy)
    stock_profit_ratios = main_backtrade(S1.top_stocks, q_strategy=q_strategy, qd_object=Qd1,
                                         trade_back_start_date=trade_back_start_date, tb_end_date=trade_back_end_date)

    return stock_profit_ratios