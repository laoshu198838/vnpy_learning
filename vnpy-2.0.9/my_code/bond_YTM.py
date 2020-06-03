# coding='utf-8'

from typing import List, Tuple, Dict
from datetime import datetime, timedelta, time
import numpy as np
import pandas as pd
import time
import sympy


class Computer_YTM():
    """计算债券的相关指标"""

    def __init__(
        self,
        settlement_date: str = '2019/11/29',
        maturity_date: str = '2020/6/15',
        coupon: float = 0.0505,
        principal: int = 100,
        date_frequently: str = 'semi_annual',
        clean_price=50,
        YTM: float = 1.4198226
    ):
        assert date_frequently in ['annual', 'semi_annual', 'quarterly',
                                   'monthly'], "付息频率请参照['annual','quarterly','quarterly','monthly']"

        self.d_s = datetime.strptime(settlement_date, '%Y/%m/%d')
        self.d_m = datetime.strptime(maturity_date, '%Y/%m/%d')
        self.r_c = coupon
        self.pr = principal
        self.d_f = date_frequently
        self.clean_price = clean_price
        self.YTM = YTM
        

        self.clean_bond_price = self.pr * self.clean_price / 100
        self.dirty_bond_price:float = 0.00
        self.yield_to_maturity = 0

        self.each_interest:float = 0
        self.time_receive_interest:int = 0
        self.pay_frequency: int = 1
        self.accured_interest: float = 0
        self.interest:float=0.00

        self.cash_flow_date:list=[]
        self.previous_cash_flow_date: str = 0
        self.next_cash_flow_date: str = None

        self.days_of_next_cash_flow: int = 0
        self.days_of_maturity = (self.d_m - self.d_s)
        self.days_of_accured_interest = None
        self.years_to_maturity: float = 0.00
        
        self.TCF: float = 0
        self.DCF: float = 0      
        self.number_of_remaining_cash_flow = len(self.cash_flow_date)
        self.days_value_to_maturity = (self.d_m - self.d_s).days
        
        self._calculate_maturity()
        self._calculate_CF_date()
        self._cash_flow()
        self.show_data()
        # self.YTM(self.TCF,self.clean_price)

    def _calculate_maturity(self):
        """ 计算到期年限 """
        delta = self.d_m.day - self.d_s.day + \
            (self.d_m.month - self.d_s.month) * 30 + \
            (self.d_m.year - self.d_s.year) * 360
        self.years_to_maturity = delta / 360

    def _calculate_CF_date(self):
        """ 计算现金流日期 """
        start_date = self.d_s
        end_date = self.d_m
        total_year = self.years_to_maturity
        interest = []
        if self.d_f == 'annual':
            while end_date > start_date:
                insert_date = end_date.strftime("%F")
                self.cash_flow_date.insert(0, insert_date)
                end_date = self._monthdelta(end_date, -12)
                self.each_interest = self.r_c
            self.pay_frequency = 1
        elif self.d_f == 'semi_annual':
            while end_date > start_date:
                insert_date = end_date.strftime("%F")
                self.cash_flow_date.insert(0, insert_date)
                end_date = self._monthdelta(end_date, -6)
                self.each_interest = round(self.r_c / 2, 4)
            self.pay_frequency = 2
        elif self.d_f == 'quarterly':
            while end_date > start_date:
                insert_date = end_date.strftime("%F")
                self.cash_flow_date.insert(0, insert_date)
                end_date = self._monthdelta(end_date, -3)
                self.each_interest = round(self.r_c / 4, 4)
            self.pay_frequency = 4
        elif self.d_f == 'monthly':
            while end_date > start_date:
                insert_date = end_date.strftime("%F")
                self.cash_flow_date.insert(0, insert_date)
                end_date = self._monthdelta(end_date, -1)
                self.each_interest = round(self.r_c / 12, 4)
            self.pay_frequency = 12

        self.time_receive_interest = len(self.cash_flow_date)
        self.interest = [self.each_interest * 100] * self.time_receive_interest
        
        self.next_cash_flow_date = self.cash_flow_date[0]
        self.days_of_accured_interest = (self.d_s - end_date).days
        self.accured_interest = self.days_of_accured_interest / 360 * self.r_c * self.pr

        self.previous_cash_flow_date = end_date.strftime('%F')
        self.days_of_next_cash_flow = (datetime.strptime(self.cash_flow_date[0], '%Y-%m-%d') - self.d_s).days
        
        self.dirty_bond_price = self.clean_bond_price + self.accured_interest
        self.number_of_remaining_cash_flow = len(self.cash_flow_date)
        
    def _monthdelta(self, date, delta):
        """ 日期月份加减 """
        m, y = (date.month + delta) % 12, date.year + \
            ((date.month) + delta - 1) // 12
        if not m:
            m = 12
        d = min(
            date.day,
            [31, 29 if y % 4 == 0
             and not y % 400 == 0
             else 28, 31, 30, 31, 30, 31,
             31, 30, 31, 30, 31][m - 1])
        return date.replace(day=d, month=m, year=y)

    def _cash_flow(self):
        """ 计算每期的现流 """
        # self.TCF
        each_interest = self.interest[:]
        self.TCF = each_interest[-1] + 100
        # # self.accured_interest
        first_time_to_settlement = datetime.strptime(
            self.cash_flow_date[0], '%Y-%m-%d')
        delta = first_time_to_settlement.day - self.d_s.day + \
            (first_time_to_settlement.month - self.d_s.month) * 30
        t = delta / 360
        # self.accured_interest = delta / 360 * self.pr * self.r_c
        
        # self.DCF
        for i in range(len(self.interest)):
            self.DCF += each_interest[i] / (1 + self.YTM /
                                         self.pay_frequency)**(self.pay_frequency * t + i)

    def show_data(self):
        """ 数据展示 """
        principal = [0] * len(self.cash_flow_date)
        principal[-1] = self.pr
        total_CF = self.interest[:]
        total_CF[-1] = total_CF[-1] + principal[-1]
        self.TCF=total_CF
        dict = {
            'cash flow date': self.cash_flow_date,
            'interest': self.interest,
            'principal':principal ,
            'total CF':total_CF ,
        }
        data = pd.DataFrame(dict)
        data.index = data.index + 1
        data.index.name="No."
        print(data)
        print('=====================================================')
        print(f"yield to maturity：\t{self.yield_to_maturity}")
        print(f"clean bond price：\t{self.clean_bond_price}")
        print(f"accured interest：\t{self.accured_interest:,.4f}")
        print(f"dirty bond price (includes accrued)：\
                    \t{self.dirty_bond_price:,.4f}")
        print(f"duration：\t{self.yield_to_maturity}")
        print(f"modified duration：\t{self.yield_to_maturity}")
        print(f"modified convexity：\
                    \t{self.yield_to_maturity}")
        print(f"basis point value:\
                    \t{self.yield_to_maturity}")
        print(f"yield value change per 1bp increase in price：\
                    \t{self.yield_to_maturity}")
        print(f"next cash flow date：\
                    \t{self.next_cash_flow_date}")
        print(f"previous cash flow date：\
                    \t{self.previous_cash_flow_date}")
        print(f"number of days from value date to maturity：\
                    \t{self.days_value_to_maturity}")
        print(f"years to maturity:\t{self.years_to_maturity:,.4f}")
        print(f"number of days from value date to next cash flow：\
            \t{self.days_of_next_cash_flow}")
        print(f"number of days of accrued interest：\
            \t{self.days_of_accured_interest}")
        print(f"number of remaining cash flows：\
            \t{self.number_of_remaining_cash_flow}")

    def YTM(self,total_cash_flow:list,clean_price):
        """ 计算债券的到期收益率 """
        pass
        # x = sympy.symbols("x")  # 申明未知数"x"
        # for i in range(len(total_cash_flow)):
        #     total_cash_flow[i]/(1+x)**(i+1)
        # YTM = sympy.solve([x+(1/5)*x-240],[x])


def main():
    bond = Computer_YTM(date_frequently='annual')

if __name__ == "__main__":
    main()