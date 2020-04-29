# coding: utf-8
from datetime import datetime, timedelta
from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)

import traceback
from copy import deepcopy
import pandas as pd

# from .ta import macd


def up_zs_number(ka):
    """检查最新走势的连续向上中枢数量"""
    zs_num = 1
    if len(ka.zs) > 1:
        k_zs = ka.zs[::-1]
        zs_cur = k_zs[0]
        for zs_next in k_zs[1:]:
            if zs_cur['zs'][0] >= zs_next['zs'][1]:
                zs_num += 1
                zs_cur = zs_next
            else:
                break
    return zs_num


def down_zs_number(ka):
    """检查最新走势的连续向下中枢数量"""
    zs_num = 1
    if len(ka.zs) > 1:
        k_zs = ka.zs[::-1]
        zs_cur = k_zs[0]
        for zs_next in k_zs[1:]:
            if zs_cur['zs'][1] <= zs_next['zs'][0]:
                zs_num += 1
                zs_cur = zs_next
            else:
                break
    return zs_num


def is_bei_chi(ka, zs1, zs2, direction="down", mode="bi"):
    """判断 zs1 对 zs2 是否有背驰

    :param ka: KlineAnalyze
        缠论的分析结果，即去除包含关系后，识别出分型、笔、线段的K线
    :param direction: str
        default `down`, optional value [`up`, 'down']
    :param zs1: list of datetime
        用于比较的走势，通常是最近的走势
    :param zs2: list of datetime
        被比较的走势，通常是较前的走势
    :param mode: str
        default `bi`, optional value [`zs`, `xd`, `bi`]
        zs  判断两个走势类型之间是否存在背驰
        xd  判断两个线段之间是否存在背驰
        bi  判断两笔之间是否存在背驰
    :return:
    """
    df = pd.DataFrame(ka.kline)
    df = macd(df)
    k1 = df[(df['dt'] >= zs1[0]) & (df['dt'] <= zs1[1])]
    k2 = df[(df['dt'] >= zs2[0]) & (df['dt'] <= zs2[1])]

    bc = False
    if mode == 'bi':
        macd_sum1 = sum([abs(x) for x in k1.macd])
        macd_sum2 = sum([abs(x) for x in k2.macd])
        if macd_sum1 < macd_sum2:
            bc = True

    elif mode == 'xd':
        if direction == "down":
            macd_sum1 = sum([abs(x) for x in k1.macd if x < 0])
            macd_sum2 = sum([abs(x) for x in k2.macd if x < 0])
        elif direction == "up":
            macd_sum1 = sum([abs(x) for x in k1.macd if x > 0])
            macd_sum2 = sum([abs(x) for x in k2.macd if x > 0])
        else:
            raise ValueError('direction value error')
        if macd_sum1 < macd_sum2:
            bc = True

    else:
        raise ValueError("mode value error")

    return bc


class KlineAnalyze(object):
    def __init__(self, kline):
        """

        :param kline: list of dict or pd.DataFrame
            example kline:
            kline = [
                {'symbol': '600797.SH', 'dt': '2020-01-08 11:30:00', 'open': 10.72, 'close': 10.67, 'high': 10.76, 'low': 10.63, 'vol': 4464800.0},
                {'symbol': '600797.SH', 'dt': '2020-01-08 13:30:00', 'open': 10.66, 'close': 10.59, 'high': 10.66, 'low': 10.55, 'vol': 5004800.0},
                {'symbol': '600797.SH', 'dt': '2020-01-08 14:00:00', 'open': 10.58, 'close': 10.41, 'high': 10.6, 'low': 10.38, 'vol': 10650500.0},
                {'symbol': '600797.SH', 'dt': '2020-01-08 14:30:00', 'open': 10.42, 'close': 10.41, 'high': 10.48, 'low': 10.35, 'vol': 6610000.0},
                {'symbol': '600797.SH', 'dt': '2020-01-08 15:00:00', 'open': 10.42, 'close': 10.39, 'high': 10.48, 'low': 10.36, 'vol': 7160500.0}
            ]
        """
        self.kline = self._preprocess(kline)
        self.kline_new = self._remove_include()
        self.fx = self._find_fx()
        self.bi = self._find_bi()
        self.xd = self._find_xd()
        self.zs = self._find_zs()
        self.__update_kline()

    @staticmethod
    def _preprocess(kline):
        """新增分析所需字段"""
        if isinstance(kline, pd.DataFrame):
            kline = [row.to_dict() for _, row in kline.iterrows()]

        results = []
        for k in kline:
            k['fx_mark'], k['fx'], k['bi'], k['xd'] = "o", None, None, None
            results.append(k)
        return results

    def _remove_include(self):
        """去除包含关系，得到新的K线数据"""
        # 取前两根 K 线放入 k_new，完成初始化
        kline = deepcopy(self.kline)
        k_new = kline[:2]

        for k in kline[2:]:
            # 从 k_new 中取最后两根 K 线计算方向
            k1, k2 = k_new[-2:]
            if k2['high'] > k1['high']:
                direction = "up"
            elif k2['low'] < k1['low']:
                direction = "down"
            else:
                direction = "up"

            # 判断 k2 与 k 之间是否存在包含关系
            cur_h, cur_l = k['high'], k['low']
            last_h, last_l = k2['high'], k2['low']

            # 左包含 or 右包含
            if (cur_h <= last_h and cur_l >= last_l) or (cur_h >= last_h and cur_l <= last_l):
                # 有包含关系，按方向分别处理
                if direction == "up":
                    last_h = max(last_h, cur_h)
                    last_l = max(last_l, cur_l)
                elif direction == "down":
                    last_h = min(last_h, cur_h)
                    last_l = min(last_l, cur_l)
                else:
                    raise ValueError

                k['high'] = last_h
                k['low'] = last_l
                k_new.pop(-1)
                k_new.append(k)
            else:
                # 无包含关系，更新 K 线
                k_new.append(k)
        return k_new

    def _find_fx(self):
        """识别线分型标记

        o   非分型
        d   底分型
        g   顶分型

        :return:
        """
        kn = deepcopy(self.kline_new)
        i = 0
        while i < len(kn):
            if i == 0 or i == len(kn) - 1:
                i += 1
                continue
            k1, k2, k3 = kn[i - 1: i + 2]
            i += 1

            # 顶分型标记
            if k2['high'] > k1['high'] and k2['high'] > k3['high']:
                k2['fx_mark'] = 'g'
                k2['fx'] = k2['high']

            # 底分型标记
            if k2['low'] < k1['low'] and k2['low'] < k3['low']:
                k2['fx_mark'] = 'd'
                k2['fx'] = k2['low']
        self.kline_new = kn

        fx = [{"dt": x['dt'], "fx_mark": x['fx_mark'], "fx": x['fx']} for x in self.kline_new
              if x['fx_mark'] in ['d', 'g']]
        return fx

    def __get_potential_bi(self):
        """识别笔标记：从已经识别出来的分型中确定能够构建笔的分型

        划分笔的步骤：
        （1）确定所有符合标准的分型，能够构成笔的标准底分型一定小于其前后的底分型，顶分型反之；
             两个相邻的顶底分型之间，如果没有共用K线，也可以认为是符合标准的分型。
        （2）如果前后两分型是同一性质的，对于顶，前面的低于后面的，只保留后面的，前面那个可以忽略掉；对于底，
            前面的高于后面的，只保留后面的，前面那个可以忽略掉。不满足上面情况的，例如相等的，都可以先保留。
        （3）经过步骤（2）的处理后，余下的分型，如果相邻的是顶和底，那么这就可以划为一笔。
        """
        # 符合标准的分型
        kn = deepcopy(self.kline_new)
        # 两个不同的对象

        fx_p = []
        for fx_mark in ['d', 'g']:
            # 从self.fx中把顶和底分别进行处理
            fx = [x for x in deepcopy(self.fx) if x['fx_mark'] == fx_mark]

            fx = sorted(fx, key=lambda x: x['dt'], reverse=False)
            for i in range(1, len(fx) - 1):
                fx1, fx2, fx3 = fx[i - 1:i + 2]
                if (fx_mark == "d" and fx1['fx'] >= fx2['fx'] <= fx3['fx']) or \
                        (fx_mark == "g" and fx1['fx'] <= fx2['fx'] >= fx3['fx']):
                    fx_p.append(deepcopy(fx2))

        # 两个相邻的顶点分型之间至少有1根非共用K线
        for i in range(len(self.fx) - 1):
            fx1, fx2 = self.fx[i], self.fx[i + 1]
            k_num = [x for x in kn if fx1['dt'] <= x['dt'] <= fx2['dt']]
            if len(k_num) >= 5:
                fx_p.append(deepcopy(fx1))
                fx_p.append(deepcopy(fx2))

        fx_p = sorted(fx_p, key=lambda x: x['dt'], reverse=False)

        # 确认哪些分型可以构成笔
        bi = []
        for i in range(len(fx_p)):
            k = deepcopy(fx_p[i])
            k['bi'] = k['fx']
            # 这个是把分型的数字转到笔上来
            del k['fx']
            if len(bi) == 0:
                bi.append(k)
            else:
                k0 = bi[-1]
                if k0['fx_mark'] == k['fx_mark']:
                    if (k0['fx_mark'] == "g" and k0['bi'] < k['bi']) or \
                            (k0['fx_mark'] == "d" and k0['bi'] > k['bi']):
                        bi.pop(-1)
                        bi.append(k)
                else:
                    # 确保相邻两个顶底之间顶大于底
                    if (k0['fx_mark'] == 'g' and k['bi'] >= k0['bi']) or \
                            (k0['fx_mark'] == 'd' and k['bi'] <= k0['bi']):
                        bi.pop(-1)
                        continue

                    # 一笔的顶底分型之间至少包含5根K线
                    k_num = [x for x in kn if k0['dt'] <= x['dt'] <= k['dt']]
                    if len(k_num) >= 5:
                        bi.append(k)
        return bi

    def __handle_last_bi(self, bi):
        """判断最后一个笔标记是否有效，有两个方案：
        方案一规则如下：
        1）如果最后一个笔标记为顶分型，最近一根K线的最高价在这个顶分型上方，该标记无效；
        2）如果最后一个笔标记为底分型，最近一根K线的最低价在这个底分型下方，该标记无效；

        方案二规则如下：
        1）如果最后一个笔标记为顶分型，最近一个底分型在这个顶分型上方，该标记无效；
        2）如果最后一个笔标记为底分型，最近一个顶分型在这个底分型下方，该标记无效；
        """
        last_bi = bi[-1]

        last_k = self.kline_new[-1]
        if (last_bi['fx_mark'] == 'g' and last_k['high'] >= last_bi['bi']) or \
                (last_bi['fx_mark'] == 'd' and last_k['low'] <= last_bi['bi']):
            bi.pop()

        # fx_last_d = [x for x in self.fx if x['fx_mark'] == "d"][-1]
        # fx_last_g = [x for x in self.fx if x['fx_mark'] == "g"][-1]
        # if (last_bi['fx_mark'] == 'g' and fx_last_d['fx'] >= last_bi['bi']) or \
        #         (last_bi['fx_mark'] == 'd' and fx_last_g['fx'] <= last_bi['bi']):
        #     bi.pop()
        return bi

    def _find_bi(self):
        bi = self.__get_potential_bi()
        bi = self.__handle_last_bi(bi)
        bi_list = [x["dt"] for x in bi]

        for k in self.kline_new:
            if k['dt'] in bi_list:
                k['bi'] = k['fx']
        return bi

    def __get_potential_xd(self):
        """依据不创新高、新低的近似标准找出所有潜在线段标记"""
        bi = deepcopy(self.bi)
        xd = []
        potential = bi[0]

        i = 0
        while i < len(bi) - 3:
            k1, k2, k3 = bi[i + 1], bi[i + 2], bi[i + 3]

            if potential['fx_mark'] == "d":
                assert k2['fx_mark'] == 'd'
                if k3['bi'] < k1['bi']:
                    potential['xd'] = potential['bi']
                    xd.append(potential)
                    i += 1
                    potential = deepcopy(bi[i])
                else:
                    i += 2
            elif potential['fx_mark'] == "g":
                assert k2['fx_mark'] == 'g'
                if k3['bi'] > k1['bi']:
                    potential['xd'] = potential['bi']
                    xd.append(potential)
                    i += 1
                    potential = deepcopy(bi[i])
                else:
                    i += 2
            else:
                raise ValueError

        potential['xd'] = potential['bi']
        xd.append(potential)
        xd = [{"dt": x['dt'], "fx_mark": x['fx_mark'], "xd": x['xd']}
              for x in xd]
        return xd

    def __get_valid_xd(self, xd_p):
        bi = deepcopy(self.bi)
        xd_v = []
        for i in range(len(xd_p)):
            p2 = deepcopy(xd_p[i])
            if i == 0:
                xd_v.append(p2)
            else:
                p1 = deepcopy(xd_v[-1])
                if p1['fx_mark'] == p2['fx_mark']:
                    if (p1['fx_mark'] == 'g' and p1['xd'] < p2['xd']) or \
                            (p1['fx_mark'] == 'd' and p1['xd'] > p2['xd']):
                        xd_v.pop(-1)
                        xd_v.append(p2)
                else:
                    # 连续两个不同类型线段标记不允许出现“线段高点低于线段低点”和“线段低点高于线段高点”的情况；
                    if (p1['fx_mark'] == "g" and p1['xd'] < p2['xd']) or \
                            (p1['fx_mark'] == "d" and p1['xd'] > p2['xd']):
                        continue

                    # bi_l = [x for x in bi if x['dt'] <= p1['dt']]
                    bi_m = [x for x in bi if p1['dt'] <= x['dt'] <= p2['dt']]
                    bi_r = [x for x in bi if x['dt'] >= p2['dt']]
                    if len(bi_m) == 2:
                        # 两个连续线段标记之间只有一笔的处理
                        if i == len(xd_p) - 1:
                            break
                        p3 = deepcopy(xd_p[i + 1])
                        if (p1['fx_mark'] == "g" and p1['xd'] < p3['xd']) or \
                                (p1['fx_mark'] == "d" and p1['xd'] > p3['xd']):
                            xd_v.pop(-1)
                            xd_v.append(p3)
                    elif len(bi_m) == 4:
                        # 两个连续线段标记之间只有三笔的处理
                        lp2 = bi_m[-2]
                        rp2 = bi_r[1]
                        if lp2['fx_mark'] == rp2['fx_mark']:
                            if (p2['fx_mark'] == "g" and lp2['bi'] < rp2['bi']) or \
                                    (p2['fx_mark'] == "d" and lp2['bi'] > rp2['bi']):
                                xd_v.append(p2)
                    else:
                        xd_v.append(p2)
        return xd_v

    def __handle_last_xd(self, xd_v):
        """判断最后一个线段标记是否有效，有以下两个方案：

        方案一规则如下：
        1）如果最后一个线段标记为顶分型，最近一根K线的最高价在这个顶分型上方，该标记无效；
        2）如果最后一个线段标记为底分型，最近一根K线的最低价在这个底分型下方，该标记无效；


        方案二规则如下：
        1）如果最后一个线段标记为顶分型，最近一个向下笔结束在这个顶分型上方，该线段标记无效；
        2）如果最后一个线段标记为底分型，最近一个向上笔结束在这个底分型下方，该线段标记无效；

        """
        last_xd = xd_v[-1]

        last_k = self.kline_new[-1]
        if (last_xd['fx_mark'] == 'g' and last_k['high'] >= last_xd['xd']) or \
                (last_xd['fx_mark'] == 'd' and last_k['low'] <= last_xd['xd']):
            xd_v.pop()

        # bi_last_d = [x for x in self.bi if x['fx_mark'] == "d"][-1]
        # bi_last_g = [x for x in self.bi if x['fx_mark'] == "g"][-1]
        # if (last_xd['fx_mark'] == 'g' and bi_last_d['bi'] >= last_xd['xd']) or \
        #         (last_xd['fx_mark'] == 'd' and bi_last_g['bi'] <= last_xd['xd']):
        #     xd_v.pop()
        return xd_v

    def _find_xd(self):
        try:
            xd = self.__get_potential_xd()
            xd = self.__get_valid_xd(xd)
            xd = self.__handle_last_xd(xd)
            dts = [x['dt'] for x in xd]

            def __add_xd(k):
                if k['dt'] in dts:
                    k['xd'] = k['fx']
                return k

            self.kline_new = [__add_xd(k) for k in self.kline_new]
            return xd
        except:
            traceback.print_exc()
            return []

    def _find_zs(self):
        """查找中枢"""
        if len(self.xd) <= 4:
            return []

        k_xd = self.xd
        k_zs = []
        zs_xd = []

        for i in range(len(k_xd)):
            if len(zs_xd) < 3:
                zs_xd.append(k_xd[i])
                continue
            xd_p = k_xd[i]
            zs_d = max([x['xd'] for x in zs_xd if x['fx_mark'] == 'd'])
            zs_g = min([x['xd'] for x in zs_xd if x['fx_mark'] == 'g'])

            if xd_p['fx_mark'] == "d" and xd_p['xd'] > zs_g:
                # 线段在中枢上方结束，形成三买
                k_zs.append({'zs': (zs_d, zs_g), "zs_xd": deepcopy(zs_xd)})
                zs_xd = deepcopy(k_xd[i - 2:i + 1])
            elif xd_p['fx_mark'] == "g" and xd_p['xd'] < zs_d:
                # 线段在中枢下方结束，形成三卖
                k_zs.append({'zs': (zs_d, zs_g), "zs_xd": deepcopy(zs_xd)})
                zs_xd = deepcopy(k_xd[i - 2:i + 1])
            else:
                zs_xd.append(deepcopy(xd_p))

        if len(zs_xd) >= 4:
            zs_d = max([x['xd'] for x in zs_xd if x['fx_mark'] == 'd'])
            zs_g = min([x['xd'] for x in zs_xd if x['fx_mark'] == 'g'])
            k_zs.append({'zs': (zs_d, zs_g), "zs_xd": deepcopy(zs_xd)})

        return k_zs

    def __update_kline(self):
        kn_map = {x['dt']: x for x in self.kline_new}
        for k in self.kline:
            k1 = kn_map.get(k['dt'], None)
            if k1:
                k['fx_mark'], k['fx'], k['bi'], k['xd'] = k1['fx_mark'], k1['fx'], k1['bi'], k1['xd']


class SolidAnalyze(object):
    """多级别（日线、30分钟、5分钟、1分钟）K线联合分析

    这只是一个样例，展示如何结合多个K线级别进行买卖点分析。
    你可以根据自己对缠论的理解，利用 KlineAnalyze 的分析结果在多个级别之间进行联合分析，找出符合自己要求的买卖点。
    """

    def __init__(self, klines, symbol=None):
        """

        :param klines: dict
            key 为K线级别名称；value 为对应的K线数据，K线数据基本格式参考 KlineAnalyze
            example: {"日线": df, "30分钟": df, "5分钟": df, "1分钟": df,}
        """
        self.kas = dict()
        self.symbol = symbol
        self.freqs = list(klines.keys())
        for freq, kline in klines.items():
            try:
                ka = KlineAnalyze(kline)
                self.kas[freq] = ka
            except:
                self.kas[freq] = None
                traceback.print_exc()

    def _get_ka(self, freq):
        """输入级别，返回该级别 ka，以及上一级别 ka1，下一级别 ka2"""
        assert freq in self.freqs, "‘%s’不在级别列表（%s）中" % (
            freq, "|".join(self.freqs))
        if freq == '日线':
            ka, ka1, ka2 = self.kas['日线'], None, self.kas['30分钟']
        elif freq == '30分钟':
            ka, ka1, ka2 = self.kas['30分钟'], self.kas['日线'], self.kas['5分钟']
        elif freq == '5分钟':
            ka, ka1, ka2 = self.kas['5分钟'], self.kas['30分钟'], self.kas['1分钟']
        elif freq == '1分钟':
            ka, ka1, ka2 = self.kas['1分钟'], self.kas['5分钟'], None
        else:
            raise ValueError
        return ka, ka1, ka2

    def is_xd_end(self, freq):
        """判断最后一个线段是否可以认为已经结束了（只能判断由小级别一买引发的线段结束）"""
        ka, ka1, ka2 = self._get_ka(freq)
        last_xd = ka.xd[-1]

        end = False

        # 向上线段结束的判断
        if last_xd['fx_mark'] == 'd' and ka.bi[-1]['fx_mark'] == 'g' and ka.bi[-1]['bi'] >= ka.bi[-3]['bi']:
            zs1 = [ka.bi[-2]['dt'], ka.bi[-1]['dt']]
            zs2 = [ka.bi[-4]['dt'], ka.bi[-3]['dt']]
            if is_bei_chi(ka, zs1, zs2, direction="up", mode="bi"):
                end = True
            if isinstance(ka1, KlineAnalyze) and ka1.bi[-1]['fx_mark'] == 'd':
                end = False
            if isinstance(ka2, KlineAnalyze) and ka2.xd[-1]['fx_mark'] == 'd':
                end = False

        # 向下线段结束的判断
        elif last_xd['fx_mark'] == 'g' and ka.bi[-1]['fx_mark'] == 'd' and ka.bi[-1]['bi'] <= ka.bi[-3]['bi']:
            zs1 = [ka.bi[-2]['dt'], ka.bi[-1]['dt']]
            zs2 = [ka.bi[-4]['dt'], ka.bi[-3]['dt']]
            xd_inside = [x for x in ka.bi if x['dt'] >= last_xd['dt']]
            # 线段内部走出三笔，且有背驰
            if len(xd_inside) >= 4 and is_bei_chi(ka, zs1, zs2, direction="down", mode="bi"):
                end = True
            if isinstance(ka1, KlineAnalyze) and ka1.bi[-1]['fx_mark'] == 'g':
                end = False
            if isinstance(ka2, KlineAnalyze) and ka2.xd[-1]['fx_mark'] == 'g':
                end = False

        else:
            raise ValueError
        return end

    # ====================================================================
    # 第一类买卖点

    def is_first_buy(self, freq, tolerance=0.03):
        """确定某一级别一买，包括由盘整背驰引发的类一买

        注意：如果本级别上一级别的 ka 不存在，默认返回 False !!!

        :param freq: str
            K线级别，如 1分钟；这个级别可以是你定义的任何名称
        :param tolerance: float
            相对于基准价格的操作容差，默认为 0.03，表示在基准价格附近上下3个点的波动范围内都是允许操作的
        :return:
        """
        ka, ka1, ka2 = self._get_ka(freq)

        if not isinstance(ka, KlineAnalyze) or len(ka.xd) < 6:
            return False, None

        b = False
        detail = {
            "标的代码": self.symbol,
            "操作提示": freq + "一买",
            "出现时间": "",
            "基准价格": 0,
            "其他信息": f"向下中枢数量为{down_zs_number(ka)}"
        }
        if isinstance(ka1, KlineAnalyze) and ka1.xd and ka1.xd[-1]['fx_mark'] == 'g':
            # 以上一级别线段终点为走势分解的起点
            xds_l = [x for x in ka.xd if x['dt'] <= ka1.xd[-1]['dt']]
            xds_r = [x for x in ka.xd if x['dt'] > ka1.xd[-1]['dt']]
            xds = [xds_l[-1]] + xds_r
            # 盘整至少有三段次级别走势，趋势至少有5段；底背驰一定要创新低
            if len(xds) >= 4 and xds[-1]['fx_mark'] == 'd' and xds[-1]['xd'] < xds[-3]['xd']:
                zs1 = [xds[-2]['dt'], xds[-1]['dt']]
                zs2 = [xds[-4]['dt'], xds[-3]['dt']]
                if is_bei_chi(ka, zs1, zs2, direction='down', mode='xd'):
                    detail["出现时间"] = xds[-1]['dt']
                    price = xds[-1]['xd']
                    detail["基准价格"] = price
                    # 确保当前价格在容差范围内
                    if (1 - tolerance) * price <= ka.kline[-1]['close'] <= (1 + tolerance) * price:
                        b = True

        if isinstance(ka2, KlineAnalyze) and ka2.xd[-1]['fx_mark'] == 'g':
            b = False
        return b, detail

    def is_first_sell(self, freq, tolerance=0.03):
        """确定某一级别一卖，包括由盘整背驰引发的类一卖

        注意：如果本级别上一级别的 ka 不存在，默认返回 False !!!

        :param freq: str
            K线级别，如 1分钟；这个级别可以是你定义的任何名称
        :param tolerance: float
            相对于基准价格的操作容差，默认为 0.03，表示在基准价格附近上下3个点的波动范围内都是允许操作的
        :return:
        """
        ka, ka1, ka2 = self._get_ka(freq)

        if not isinstance(ka, KlineAnalyze) or len(ka.xd) < 6:
            return False, None

        b = False
        detail = {
            "标的代码": self.symbol,
            "操作提示": freq + "一卖",
            "出现时间": "",
            "基准价格": 0,
            "其他信息": f"向上中枢数量为{up_zs_number(ka)}"
        }
        if isinstance(ka1, KlineAnalyze) and ka1.xd and ka1.xd[-1]['fx_mark'] == 'd':
            # 以上一级别线段终点为走势分解的起点
            xds_l = [x for x in ka.xd if x['dt'] <= ka1.xd[-1]['dt']]
            xds_r = [x for x in ka.xd if x['dt'] > ka1.xd[-1]['dt']]
            xds = [xds_l[-1]] + xds_r
            # 盘整至少有三段次级别走势，趋势至少有5段；顶背驰一定要创新高
            if len(xds) >= 4 and xds[-1]['fx_mark'] == 'g' and xds[-1]['xd'] > xds[-3]['xd']:
                zs1 = [xds[-2]['dt'], xds[-1]['dt']]
                zs2 = [xds[-4]['dt'], xds[-3]['dt']]
                if is_bei_chi(ka, zs1, zs2, direction='up', mode='xd'):
                    detail["出现时间"] = xds[-1]['dt']
                    price = xds[-1]['xd']
                    detail["基准价格"] = price
                    # 确保当前价格在容差范围内
                    if (1 - tolerance) * price <= ka.kline[-1]['close'] <= (1 + tolerance) * price:
                        b = True

        if isinstance(ka2, KlineAnalyze) and ka2.xd[-1]['fx_mark'] == 'd':
            b = False
        return b, detail

    # ====================================================================
    # 第二类买卖点

    def is_second_buy(self, freq, tolerance=0.03):
        """确定某一级别二买，包括类二买

        注意：如果本级别上一级别的 ka 不存在，默认返回 False !!!

        :param freq: str
            K线级别，如 1分钟；这个级别可以是你定义的任何名称
        :param tolerance: float
            相对于基准价格的操作容差，默认为 0.03，表示在基准价格附近上下3个点的波动范围内都是允许操作的
        :return:
        """
        ka, ka1, ka2 = self._get_ka(freq)

        if not isinstance(ka, KlineAnalyze) or len(ka.xd) < 6:
            return False, None

        b = False
        detail = {
            "标的代码": self.symbol,
            "操作提示": freq + "二买",
            "出现时间": "",
            "基准价格": 0,
            "其他信息": f"向下中枢数量为{down_zs_number(ka)}"
        }
        if isinstance(ka1, KlineAnalyze) and ka1.xd and ka1.xd[-1]['fx_mark'] == 'd':
            # 以上一级别线段终点为走势分解的起点
            xds_l = [x for x in ka.xd if x['dt'] <= ka1.xd[-1]['dt']]
            xds_r = [x for x in ka.xd if x['dt'] > ka1.xd[-1]['dt']]
            xds = [xds_l[-1]] + xds_r
            # 次级别向下走势不创新低，就认为是类二买，其中第一个是真正的二买；
            # 如果一个向上走势内部已经有5段次级别走势，则认为该走势随后不再有二买机会
            if 3 <= len(xds) <= 6 and xds[-1]['fx_mark'] == 'd' and xds[-1]['xd'] > xds[-3]['xd']:
                detail["出现时间"] = xds[-1]['dt']
                price = xds[-1]['xd']
                detail["基准价格"] = price
                # 确保当前价格在容差范围内
                if (1 - tolerance) * price <= ka.kline[-1]['close'] <= (1 + tolerance) * price:
                    b = True

        if isinstance(ka2, KlineAnalyze) and ka2.xd[-1]['fx_mark'] == 'g':
            b = False
        return b, detail

    def is_second_sell(self, freq, tolerance=0.03):
        """确定某一级别二卖，包括类二卖

        注意：如果本级别上一级别的 ka 不存在，默认返回 False !!!

        :param freq: str
            K线级别，如 1分钟；这个级别可以是你定义的任何名称
        :param tolerance: float
            相对于基准价格的操作容差，默认为 0.03，表示在基准价格附近上下3个点的波动范围内都是允许操作的
        :return:
        """
        ka, ka1, ka2 = self._get_ka(freq)

        if not isinstance(ka, KlineAnalyze) or len(ka.xd) < 6:
            return False, None

        b = False
        detail = {
            "标的代码": self.symbol,
            "操作提示": freq + "二卖",
            "出现时间": "",
            "基准价格": 0,
            "其他信息": f"向上中枢数量为{up_zs_number(ka)}"
        }
        if isinstance(ka1, KlineAnalyze) and ka1.xd and ka1.xd[-1]['fx_mark'] == 'g':
            # 以上一级别线段终点为走势分解的起点
            xds_l = [x for x in ka.xd if x['dt'] <= ka1.xd[-1]['dt']]
            xds_r = [x for x in ka.xd if x['dt'] > ka1.xd[-1]['dt']]
            xds = [xds_l[-1]] + xds_r
            # 次级别向上走势不创新高，就认为是类二卖，其中第一个是真正的二卖；
            # 如果一个向下走势内部已经有5段次级别走势，则认为该走势随后不再有二卖机会
            if 3 <= len(xds) <= 6 and xds[-1]['fx_mark'] == 'g' and xds[-1]['xd'] < xds[-3]['xd']:
                detail["出现时间"] = xds[-1]['dt']
                price = xds[-1]['xd']
                detail["基准价格"] = price
                # 确保当前价格在容差范围内
                if (1 - tolerance) * price <= ka.kline[-1]['close'] <= (1 + tolerance) * price:
                    b = True

        if isinstance(ka2, KlineAnalyze) and ka2.xd[-1]['fx_mark'] == 'd':
            b = False
        return b, detail

    # ====================================================================
    # 第三类买卖点
    # 一个第三类买卖点，至少需要有5段次级别的走势，前三段构成中枢，第四段离开中枢，第5段构成第三类买卖点。

    def is_third_buy(self, freq, tolerance=0.03):
        """确定某一级别三买

        :param freq: str
            K线级别，如 1分钟；这个级别可以是你定义的任何名称
        :param tolerance: float
            相对于基准价格的操作容差，默认为 0.03，表示在基准价格附近上下3个点的波动范围内都是允许操作的
        :return:
        """
        ka, ka1, ka2 = self._get_ka(freq)

        if not isinstance(ka, KlineAnalyze) or len(ka.xd) < 6:
            return False, None

        last_xd = ka.xd[-1]
        if last_xd['fx_mark'] == 'd':
            zs_g = min([x['xd'] for x in ka.xd[-6:-1] if x['fx_mark'] == "g"])
            zs_d = max([x['xd'] for x in ka.xd[-6:-1] if x['fx_mark'] == "d"])
        else:
            zs_g = min([x['xd'] for x in ka.xd[-5:] if x['fx_mark'] == "g"])
            zs_d = max([x['xd'] for x in ka.xd[-5:] if x['fx_mark'] == "d"])

        if zs_d > zs_g:
            return False, None

        b = False
        detail = {
            "标的代码": self.symbol,
            "操作提示": freq + "三买",
            "出现时间": "",
            "基准价格": 0,
            "其他信息": f"向上中枢数量为{up_zs_number(ka)}"
        }
        if last_xd['fx_mark'] == 'd' and last_xd['xd'] > zs_g:
            # 最后一个向下线段已经在本级别结束的情况
            detail['出现时间'] = last_xd['dt']
            price = last_xd['xd']
            detail["基准价格"] = price
            # 确保当前价格在容差范围内
            if (1 - tolerance) * price <= ka.kline[-1]['close'] <= (1 + tolerance) * price:
                b = True

        if last_xd['fx_mark'] == 'g':
            # 最后一个向下线段没有结束的情况
            last_bi_d = [x for x in ka.bi if x['fx_mark'] == 'd'][-1]
            xd_inside = [x for x in ka.bi if x['dt'] >= last_xd['dt']]
            if last_bi_d['bi'] > zs_g and len(xd_inside) >= 6:
                detail['出现时间'] = last_bi_d['dt']
                price = last_bi_d['bi']
                detail["基准价格"] = price
                # 确保当前价格在容差范围内
                if (1 - tolerance) * price <= ka.kline[-1]['close'] <= (1 + tolerance) * price:
                    b = True

        if isinstance(ka1, KlineAnalyze) and ka1.bi[-1]['fx_mark'] == 'g':
            b = False
        if isinstance(ka2, KlineAnalyze) and ka2.xd[-1]['fx_mark'] == 'g':
            b = False

        return b, detail

    def is_third_sell(self, freq, tolerance=0.03):
        """确定某一级别三卖

        :param freq: str
            K线级别，如 1分钟；这个级别可以是你定义的任何名称
        :param tolerance: float
            相对于基准价格的操作容差，默认为 0.03，表示在基准价格附近上下3个点的波动范围内都是允许操作的
        :return:
        """
        ka, ka1, ka2 = self._get_ka(freq)

        if not isinstance(ka, KlineAnalyze) or len(ka.xd) < 6:
            return False, None

        last_xd = ka.xd[-1]
        if last_xd['fx_mark'] == 'g':
            zs_g = min([x['xd'] for x in ka.xd[-6:-1] if x['fx_mark'] == "g"])
            zs_d = max([x['xd'] for x in ka.xd[-6:-1] if x['fx_mark'] == "d"])
        else:
            zs_g = min([x['xd'] for x in ka.xd[-5:] if x['fx_mark'] == "g"])
            zs_d = max([x['xd'] for x in ka.xd[-5:] if x['fx_mark'] == "d"])

        if zs_d > zs_g:
            return False, None

        b = False
        detail = {
            "标的代码": self.symbol,
            "操作提示": freq + "三卖",
            "出现时间": "",
            "基准价格": 0,
            "其他信息": f"向下中枢数量为{down_zs_number(ka)}"
        }
        if last_xd['fx_mark'] == 'g' and last_xd['xd'] < zs_d:
            # 最后一个向上线段已经在本级别结束的情况
            detail['出现时间'] = last_xd['dt']
            price = last_xd['xd']
            detail["基准价格"] = price
            # 确保当前价格在容差范围内
            if (1 - tolerance) * price <= ka.kline[-1]['close'] <= (1 + tolerance) * price:
                b = True

        if last_xd['fx_mark'] == 'd':
            # 最后一个向上线段没有结束的情况
            last_bi_g = [x for x in ka.bi if x['fx_mark'] == 'g'][-1]
            xd_inside = [x for x in ka.bi if x['dt'] >= last_xd['dt']]
            if last_bi_g['bi'] < zs_d and len(xd_inside) >= 6:
                detail['出现时间'] = last_bi_g['dt']
                price = last_bi_g['bi']
                detail["基准价格"] = price
                # 确保当前价格在容差范围内
                if (1 - tolerance) * price <= ka.kline[-1]['close'] <= (1 + tolerance) * price:
                    b = True

        if isinstance(ka1, KlineAnalyze) and ka1.bi[-1]['fx_mark'] == 'd':
            b = False
        if isinstance(ka2, KlineAnalyze) and ka2.xd[-1]['fx_mark'] == 'd':
            b = False

        return b, detail

    # ====================================================================
    # 同级别分解买卖点（这个实现仅支持5分钟、30分钟级别的分解）
    def is_xd_buy(self, freq, tolerance=0.03):
        """同级别分解买点

        :param freq: str
            K线级别，如 1分钟；这个级别可以是你定义的任何名称
        :param tolerance: float
            相对于基准价格的操作容差，默认为 0.03，表示在基准价格附近上下3个点的波动范围内都是允许操作的
        :return:
        """
        ka, ka1, ka2 = self._get_ka(freq)

        if not isinstance(ka, KlineAnalyze) or len(ka.xd) < 4:
            return False, None

        b = False
        detail = {
            "标的代码": self.symbol,
            "操作提示": freq + "同级别分解买点",
            "出现时间": "",
            "基准价格": 0,
            "其他信息": f"向下中枢数量为{down_zs_number(ka)}"
        }
        last_xd = ka.xd[-1]
        if last_xd['fx_mark'] == 'd':
            zs1 = [ka.xd[-2]['dt'], ka.xd[-1]['dt']]
            zs2 = [ka.xd[-4]['dt'], ka.xd[-3]['dt']]
            if is_bei_chi(ka, zs1, zs2, direction='down', mode='xd') or last_xd['xd'] >= ka.xd[-3]['xd']:
                detail['出现时间'] = last_xd['dt']
                price = last_xd['xd']
                detail["基准价格"] = price
                # 确保当前价格在容差范围内
                if (1 - tolerance) * price <= ka.kline[-1]['close'] <= (1 + tolerance) * price:
                    b = True

        if isinstance(ka1, KlineAnalyze) and ka1.bi[-1]['fx_mark'] == 'g':
            b = False
        if isinstance(ka2, KlineAnalyze) and ka2.xd[-1]['fx_mark'] == 'g':
            b = False
        return b, detail

    def is_xd_sell(self, freq, tolerance=0.03):
        """同级别分解卖点

        :param freq: str
            K线级别，如 1分钟；这个级别可以是你定义的任何名称
        :param tolerance: float
            相对于基准价格的操作容差，默认为 0.03，表示在基准价格附近上下3个点的波动范围内都是允许操作的
        :return:
        """
        ka, ka1, ka2 = self._get_ka(freq)

        if not isinstance(ka, KlineAnalyze) or len(ka.xd) < 4:
            return False, None

        b = False
        detail = {
            "标的代码": self.symbol,
            "操作提示": freq + "同级别分解卖点",
            "出现时间": "",
            "基准价格": 0,
            "其他信息": f"向上中枢数量为{up_zs_number(ka)}"
        }
        last_xd = ka.xd[-1]
        if last_xd['fx_mark'] == 'g':
            zs1 = [ka.xd[-2]['dt'], ka.xd[-1]['dt']]
            zs2 = [ka.xd[-4]['dt'], ka.xd[-3]['dt']]
            if is_bei_chi(ka, zs1, zs2, direction='up', mode='xd') or last_xd['xd'] <= ka.xd[-3]['xd']:
                detail['出现时间'] = last_xd['dt']
                price = last_xd['xd']
                detail["基准价格"] = price
                # 确保当前价格在容差范围内
                if (1 - tolerance) * price <= ka.kline[-1]['close'] <= (1 + tolerance) * price:
                    b = True

        if isinstance(ka1, KlineAnalyze) and ka1.bi[-1]['fx_mark'] == 'd':
            b = False
        if isinstance(ka2, KlineAnalyze) and ka2.xd[-1]['fx_mark'] == 'd':
            b = False
        return b, detail


class chanlun_system(CtaTemplate):
    """"""

    author = "用Python的交易员"
    # 这些参数都是整个类可以使用的参数
    atr_length = 22
    # 计算ATR指标的窗口数
    atr_ma_length = 10
    # ATR均线的窗口数
    rsi_length = 5
    # RSI的窗口期
    rsi_entry = 16
    # rsi开仓信号
    trailing_percent = 0.8
    fixed_size = 1

    atr_value = 0
    atr_ma = 0
    rsi_value = 0
    rsi_buy = 0
    rsi_sell = 0
    intra_trade_high = 0
    intra_trade_low = 0

    parameters = ["atr_length", "atr_ma_length", "rsi_length",
                  "rsi_entry", "trailing_percent", "fixed_size"]
    variables = ["atr_value", "atr_ma", "rsi_value", "rsi_buy", "rsi_sell"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        # cta_engine是怎么来的，从哪传过来的

        # 这种超类就是子类可以改写父类的方法，同时也还可以调用父类的方法，只是有先后顺序差别，这样就可以把一些函数部分共性放在父类，差异部分在自己的策略函数中写。
        self.bg = BarGenerator(self.on_bar)  # 简化书写过程
        self.am = ArrayManager()  # 同理

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")

        self.rsi_buy = '11'  # 初始化好买点
        self.rsi_sell = '11'   # 初始化好卖点

        # 母类template中的CtaTemplate策略中的方法，只加载十天的数据，那我们测试好几年的数据是怎么加载进去呢，这个会在后面调用回测中的load_data函数
        self.load_bar(10)
        # 如果你使用的是其他的分钟k线，就需要在这里面传入
        # 具体流程是先调用template中的load_bar,然后template中的load_bar再调用backtesting.py中的load_bar,把回调函数和天数加载进去，方便后面加载数据。

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")  # 输出提示文字，同时还会执行write_log里面的程序

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        pass

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        他这个地方是怎么接收bar
        """
        self.cancel_all()

        am = self.am
        am.update_bar(bar)
        # 数据一旦加载到初始化需要的数量就会自动启动inited，在run_backtesting里面启动
        # update_bar 这个函数是在Arraymanager里面
        if not am.inited:
            return

        atr_array = am.atr(self.atr_length, array=True)
        self.atr_value = atr_array[-1]
        self.atr_ma = atr_array[-self.atr_ma_length:].mean()
        self.rsi_value = am.rsi(self.rsi_length)

        if self.pos == 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            if self.atr_value > self.atr_ma:
                if self.rsi_value > self.rsi_buy:
                    self.buy(bar.close_price + 5, self.fixed_size)
                elif self.rsi_value < self.rsi_sell:
                    self.short(bar.close_price - 5, self.fixed_size)

        elif self.pos > 0:
            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.intra_trade_low = bar.low_price
            # low没有什么用，只是用来更新最近low价格
            long_stop = self.intra_trade_high * \
                (1 - self.trailing_percent / 100)
            self.sell(long_stop, abs(self.pos), stop=True)

        elif self.pos < 0:
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)
            self.intra_trade_high = bar.high_price

            short_stop = self.intra_trade_low * \
                (1 + self.trailing_percent / 100)
            self.cover(short_stop, abs(self.pos), stop=True)

        self.put_event()

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass


if __name__ == "__main__":

    filepath_d = r'C:\Users\Administrator\Desktop\000001.csv'
    filepath_w = r'C:\Users\Administrator\Desktop\000001_w.csv'
    filepath_m = r'C:\Users\Administrator\Desktop\000002_m.csv'
    kline_d = pd.read_csv(filepath_d, index_col=0, header=0)
    kline_w = pd.read_csv(filepath_w, index_col=0)
    kline_m = pd.read_csv(filepath_m, index_col=0)

    start_date = kline_d.index
    print(start_date[-1])
    # print(isinstance(kline_d.iloc[1], pd.DataFrame))
    # print(kline_d.iloc[1,0])
    # print(kline_d.head(10))

    # date_string = kline_d.iloc[1, 0]
    # print(date_string)
    # start_date = datetime.strptime(date_string, '%Y/%m/%d %H:%M') - timedelta(hours=24)
    # start_date = datetime.strftime(start_date, "%Y%m%d")
    # print(start_date)
