# -
本人25年本科毕业论文的量化项目
程序主要是基于沪深300指数成分股进行的三因子选股和布林线回测。
股票历史数据源：Tushare，在实际运行中，发现平台数据传输有点慢(几小时以上)，添加了数据本地化步骤，程序将数据存储进Mysql数据库。
以下是程序会使用到的数据库中两个数据表的ddl：
CREATE TABLE `daily_basic` (
  `trade_date` char(10) DEFAULT NULL,
  `ts_code` char(10) DEFAULT NULL,
  `circ_mv` float DEFAULT NULL,
  `pb` float DEFAULT NULL,
  `pct_chg` float DEFAULT NULL,
  UNIQUE KEY `date_ts` (`trade_date`,`ts_code`)
) 

CREATE TABLE `factors_value` (
  `trade_date` char(10) NOT NULL,
  `Rm_Rf` float DEFAULT NULL,
  `SMB` float DEFAULT NULL,
  `HML` float DEFAULT NULL,
  PRIMARY KEY (`trade_date`)
) 

CREATE TABLE `daily_basic_five_factors` (
  `trade_date` char(10) DEFAULT NULL,
  `ts_code` char(10) DEFAULT NULL,
  `circ_mv` float DEFAULT NULL,
  `pb` float DEFAULT NULL,
  `pct_chg` float DEFAULT NULL,
  `roe` float DEFAULT NULL,
  `total_assets_change_rate` float DEFAULT NULL,
  UNIQUE KEY `date_ts` (`trade_date`,`ts_code`)
)

CREATE TABLE `factors_value_five_factors` (
  `trade_date` char(10) NOT NULL,
  `Rm_Rf` float DEFAULT NULL,
  `SMB` float DEFAULT NULL,
  `HML` float DEFAULT NULL,
  `RMW` float DEFAULT NULL,
  `CMA` float DEFAULT NULL,
  PRIMARY KEY (`trade_date`)
)
程序需要下载多个第三方库，如backtrader,tushare,pymysql等

截止到20260106为止，上传的程序是一个初步完成的作品，有些瑕疵需要完善。

目标&期望：
1.程序预留了其它选股策略以及回测策略的空间，希望后续有机会能够丰富程序能够支持的策略。
2.考虑到程序使用mysql进行数据本地化，希望能够程序能够支持多样化的数据库存储。
3.添加风险控制模块

20260614
已更新五因子选股策略, 动量策略、趋势跟踪策略
