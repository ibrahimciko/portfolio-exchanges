import pandas as pd
import os
from math import isclose, inf, floor
from time import time
from typing import List, Dict
import sys
from datetime import datetime
import traceback



def _get_market_value(target_query, orders, cost=0.001, type="buy", abs_tol=1e-5):
    query_is_zero = isclose(target_query, 0., abs_tol=abs_tol)
    num_orders = len(orders)
    if query_is_zero:
        return 0
    else:
        # orders are consumed but query is not fully obtained
        if num_orders == 0:
            return -1 * inf
        else:
            if type == "buy":
                fee_coef = (1 + cost)
            else:
                fee_coef = ( 1 - cost)
            
            assert len(orders) >= 1
            p, q = map(float, orders[0])

            if target_query >= q:
                value = q * p * fee_coef
                target_query -= q
                return value + _get_market_value(target_query, orders[1:], cost, type)
            else:
                # query is smaller
                value = target_query * p * fee_coef
                target_query = 0
                return value + _get_market_value(target_query, orders[1:], cost, type)

def create_error_message(exception:Exception):
    error_msg = "Time: " + get_current_time() +  f"Exception: {str(exception.__class__)} \n"
    if hasattr(exception, "message"):
        error_msg += f"Message:  {exception.message} \n"
    # traceback
    tb_str = ''.join(traceback.format_exception(None, exception, exception.__traceback__))
    error_msg += f"Traceback:\n {tb_str}\n"
    
    return error_msg


def get_current_time():
    now = datetime.now()
    return now.strftime("%d.%m.%Y, %H:%M:%S.%f")[:-3]


def get_saving_dir(root_saving_dir):
    # count number of files in the data dir
    data_files = os.listdir(root_saving_dir)
    if not data_files:
        data_num = 0
    else:
        data_num = len(data_files)
    
    saving_dir = os.path.join(root_saving_dir, f"{data_num}/")
    os.makedirs(saving_dir)

    return saving_dir


def _get_amount(amountQuote, orders, cost=0.001, type="buy", abs_tol=1e-10):
    # 5000lik btc satmak istiyorum kac btc satmaliyim
    # btc alicilarina git
    # ilk adam diyelim ki 10 btc almak istiyor x pricestan : q:10, p:x
    # value = 10x
    # adama 5000 olana kadar tum btclerimi satacagim
    # my btc amount = y
    # y = 5000 * (1 - cost) / p
    
    # diyelim adamda daha az btc var
    # adamin tum btclerini al maaliyeti hesapla
    # maaliyet = p * q ( 1 + cost)
    quote_is_zero = isclose(amountQuote, 0., abs_tol=abs_tol)
    num_orders = len(orders)
    if quote_is_zero:
        return 0
    else:
        if num_orders == 0:
            return -1 * inf
        else:
                
            p, q = map(float, orders[0])
            
            value = q * p
            if amountQuote <= value * ( 1 + cost):
                amount = amountQuote * (1 - cost) / p
                amountQuote = 0
                return amount + _get_amount(amountQuote, orders[1:], cost, type)
            
            else:
                amountQuote -= value * (1 + cost)
                amount = q
                return amount + _get_amount(amountQuote, orders[1:], cost, type)
            
            
                

def _get_amountQuote(amount, orders, cost=0.001, type="buy", abs_tol=1e-10):
        query_is_zero = isclose(amount, 0., abs_tol=abs_tol)
        num_orders = len(orders)
        if query_is_zero:
            return 0
        else:
            # orders are consumed but query is not fully obtained
            if num_orders == 0:
                return -1 * inf
            else:
                if type == "buy":
                    fee_coef = (1 + cost)
                else:
                    fee_coef = ( 1 - cost)
                
                assert len(orders) >= 1
                p, q = map(float, orders[0])

                if amount >= q:
                    value = q * p * fee_coef
                    amount -= q
                    return value + _get_amountQuote(amount, orders[1:], cost, type)
                else:
                    # query is smaller
                    value = amount * p * fee_coef
                    amount = 0
                    return value + _get_amountQuote(amount, orders[1:], cost, type)


def timer_func(func):
    # This function shows the execution time of 
    # the function object passed
    def wrap_func(*args, **kwargs):
        t1 = time()
        result = func(*args, **kwargs)
        t2 = time()
        print(f'Function {func.__name__!r} executed in {(t2-t1):.4f}s')
        return result
    return wrap_func



def merge_dicts(dicts:List[Dict]) -> Dict:
    """[Merges sequence of dictionaries where the values can either be atomic data type
        or dictionaries themselves.]

    Args:
        dicts (List[Dict]):

    Returns:
        [dict]:
    """
    final_dict = {}
    for dict in dicts:
        for k,v in dict.items():
            if k not in final_dict.keys():
                final_dict[k] = v
            else:
                if isinstance(v, Dict):
                    final_dict[k] = merge_dicts([v, final_dict[k]])
                else:
                    final_dict[k] += v
                
    return final_dict


def round_decimals_down(number:float, decimals:int=2):
    """
    Returns a value rounded down to a specific number of decimal places.
    """
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more")
    elif decimals == 0:
        return floor(number)

    factor = 10 ** decimals
    return floor(number * factor) / factor

def is_close_enough(v1:float, v2:float):
    isclose(v1, 0., abs_tol=1e-7)


def test_merge_dicts():
    d1 = {"a": {"x":10, "y":20}, "b": {"x":1, "y": 3}}
    d2 = {"a": {"x":10, "y":20}, "b": {"x":224, "y": 0}}
    dicts = [d1,d2]
    final_dict = merge_dicts(dicts)
    print(final_dict)