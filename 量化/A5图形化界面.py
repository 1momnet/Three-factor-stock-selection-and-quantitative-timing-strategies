from tkinter import *
from A6量化主程序 import *

class Application2(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master =  master
        self.pack()

        self.index = '399300.SZ'
        self.s_strategy = 'Fama三因子'
        self.q_strategy = '布林线策略'

        self.create_widget()

    def create_widget(self):
        # 要求输入（后续更改成用户要求输入页面的时候，需要在确定按钮那里增加一个输入判断合理性的程序，避免报错）
        # 1.创建指数栏目
        self.Label_index = Label(self, text='指数')
        self.Label_index.grid(row=0, column=0) # 第一行第一列，pack()按照行数，一行一个
        user_input1 = StringVar()
        self.list_box_index = Listbox(self, listvariable=user_input1, height=1)
        self.list_box_index.insert('1', '399300.SZ')
        self.list_box_index.grid(row=0, column=1)
        def i_on_select(event):
            selected_tuple = self.list_box_index.curselection()
            if selected_tuple:
                self.index = self.list_box_index.get(selected_tuple[0])
                print(self.index)
        self.list_box_index.bind('<<ListboxSelect>>', i_on_select)

        # 2.创建日期栏目
        self.Label_date1 = Label(self, text='选股开始日期')
        self.Label_date1.grid(row=1, column=0)
        user_input2 = StringVar()
        self.entry_star_date = Entry(self, textvariable=user_input2) # entry2：开始日期
        self.entry_star_date.grid(row=1, column=1)

        self.Label_date2 = Label(self, text='选股结束日期')
        self.Label_date2.grid(row=1, column=2)
        user_input3 = StringVar()
        self.entry_end_date = Entry(self, textvariable=user_input3) # entry3：结束日期
        self.entry_end_date.grid(row=1, column=3)

        # 3.创建策略栏目
        self.Label_s_strategy = Label(self, text='选股策略')
        self.Label_s_strategy.grid(row=2, column=0)

        self.s_Strategy_Listbox = Listbox(self, listvariable=StringVar(), height=1)
        self.s_Strategy_Listbox.insert('1', 'Fama三因子')
        self.s_Strategy_Listbox.grid(row=2, column=1)
        def s_strategy_on_select(event):
            selected_tuple = self.s_Strategy_Listbox.curselection()
            if selected_tuple:
                self.s_strategy = self.s_Strategy_Listbox.get(selected_tuple[0])
                print(f'选中选股策略: {self.s_strategy}')
        self.s_Strategy_Listbox.bind('<<ListboxSelect>>', s_strategy_on_select)

        self.Label_q_strategy = Label(self, text='择时策略')
        self.Label_q_strategy.grid(row=2, column=2)

        self.q_Strategy_Listbox = Listbox(self, listvariable=StringVar(), height=1)
        self.q_Strategy_Listbox.insert('1', '布林线策略')
        self.q_Strategy_Listbox.insert('2', '多策略')
        self.q_Strategy_Listbox.insert('3', '动量策略')
        self.q_Strategy_Listbox.insert('4', '趋势跟踪策略SMA')
        self.q_Strategy_Listbox.grid(row=2, column=3)

        def q_strategy_on_select(event):
            selected_tuple = self.q_Strategy_Listbox.curselection()
            if selected_tuple:
                self.q_strategy = self.q_Strategy_Listbox.get(selected_tuple[0])
                print(f'选中择时策略:{self.q_strategy}')

        self.q_Strategy_Listbox.bind('<<ListboxSelect>>', q_strategy_on_select)

        # 5.创建回测时间栏目
        self.Label_q_date = Label(self, text='回测开始日期')
        self.Label_q_date.grid(row=3, column=0)
        user_input_q_start = StringVar()
        self.entry_q_star_date = Entry(self, textvariable=user_input_q_start) # entry6：开始日期
        self.entry_q_star_date.grid(row=3, column=1)

        self.Label_q_date2 = Label(self, text='回测结束日期')
        self.Label_q_date2.grid(row=3, column=2)
        user_input_q_end = StringVar()
        self.entry_q_end_date = Entry(self, textvariable=user_input_q_end)  # entry7：结束日期
        self.entry_q_end_date.grid(row=3, column=3)

        # 6.创建确定按钮
        self.Btn_login = Button(self, text='确定', command=self.event_confirm)
        self.Btn_login.grid(row=4)

        self.Label_result1 = Label(self, text='选股结果')
        self.Label_result1.grid(row=5, column=0)

        self.Label_result2 = Label(self, text='回测结果')
        self.Label_result2.grid(row=5, column=1)



    # 5.为确定按钮创建一个点击事件login
    def event_confirm(self):
        start_date = self.entry_star_date.get()
        end_date = self.entry_end_date.get()
        index = self.index
        s_strategy = self.s_strategy
        q_strategy = self.q_strategy
        trade_back_start_date = self.entry_q_star_date.get()
        trade_back_end_date = self.entry_q_end_date.get()

        stock_profit_ratios = main_procedure(start_date=start_date, end_date=end_date,
                                             index=index, s_strategy=s_strategy, q_strategy=q_strategy,
                                             trade_back_start_date=trade_back_start_date, trade_back_end_date=trade_back_end_date)

        self.Text_result3 = Text(self, borderwidth=1, relief='solid', height=15, width=10)
        txt1 = '\n'.join(map(str, stock_profit_ratios.keys()))
        self.Text_result3.insert('1.0', txt1)
        self.Text_result3.config(state='disabled')
        self.Text_result3.grid(row=6, column=0)

        self.Text_result4 = Text(self, borderwidth=1, relief='solid', height=15, width=10)
        txt2 = '\n'.join(map(str, stock_profit_ratios.values()))
        self.Text_result4.insert('1.0', txt2)
        self.Text_result4.config(state='disabled')
        self.Text_result4.grid(row=6, column=1)


if __name__ == '__main__':
    root = Tk()
    root.title("股票分析工具")
    root.geometry('600x400')
    app = Application2(master=root)
    app.mainloop()
