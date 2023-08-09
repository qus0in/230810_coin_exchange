import requests
import os
import jwt
import uuid
import pandas as pd
import hashlib
from urllib.parse import urlencode, unquote
import math
import time

class Exchange:
    def __init__(self):
        self.access_key = os.getenv('access_key')
        self.secret_key = os.getenv('secret_key')
        # print(self.access_key, self.secret_key)
    
    @property
    def header_no_parameter(self):
        payload = dict(
            access_key=self.access_key,
            nonce=str(uuid.uuid4()),
        )
        jwt_token = jwt.encode(payload, self.secret_key)
        authorization = f'Bearer {jwt_token}'
        return dict(Authorization = authorization)
    
    def header_with_parameter(self, params):
        query_string = unquote(urlencode(params, doseq=True)).encode("utf-8")
        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()
        payload = dict(
            access_key=self.access_key,
            nonce=str(uuid.uuid4()),
            query_hash=query_hash,
            query_hash_alg='SHA512',
        )
        jwt_token = jwt.encode(payload, self.secret_key)
        authorization = f'Bearer {jwt_token}'
        return dict(Authorization = authorization)

    def 전체_계좌_조회(self):
        print('[전체 계좌 조회]')
        URL = 'https://api.upbit.com/v1/accounts'
        res = requests.get(URL, headers=self.header_no_parameter)
        json = res.json()
        row = ['BTC', 'KRW', 'ETH']
        col = ['balance', 'avg_buy_price']
        df = pd.DataFrame(json).set_index('currency')
        df.balance = df.balance.astype('float') + df.locked.astype('float')
        df.avg_buy_price = df.avg_buy_price.astype('float')
        self.계좌 = df.loc[row, col]
        print(self.계좌)
    
    def 현재가_조회(self):
        print('[현재가 조회]')
        URL = "https://api.upbit.com/v1/ticker"
        headers = {"accept": "application/json"}
        params = dict(markets='KRW-BTC,KRW-ETH')
        res = requests.get(URL, params=params, headers=headers)
        json = res.json()
        df = pd.DataFrame(json)[['market', 'trade_price']]
        df.market = df.market.str.split('-', expand=True)[1]
        df.trade_price = df.trade_price.astype('float')
        self.시세 = df.copy().set_index('market')
        print(self.시세)

    @property    
    def 보유_현금(self):
        return self.계좌.loc['KRW', 'balance']

    def 총자산_조회(self):
        print('[총자산 조회]')
        df = self.계좌.join(self.시세)
        평가자산 = (df.balance * df.trade_price).sum()
        self.총자산 = int(평가자산 + self.보유_현금)
        print(f'₩{self.총자산:,}')

    def 원화_입금(self):
        print('[원화 입금]')
        URL = 'https://api.upbit.com/v1/deposits/krw'
        self.투자단위 = math.ceil(max(self.총자산 * 0.05, 5000))
        self.수수료포함 = math.ceil(self.투자단위 * (1 + 0.05 / 100))
        if self.보유_현금 < self.수수료포함 * 2:
            차액 = max(math.ceil(self.수수료포함 * 2 - self.보유_현금), 5000)
            print(f'입금이 필요합니다 (₩{차액:,})')
            params = dict(amount=차액, two_factor_type='naver')
            requests.post(URL, json=params, headers=self.header_with_parameter(params))
            # TODO : 입금 확인될 때까지 루프 돌기
            time.sleep(60)
        else:
            print('입금이 필요 없습니다')
    
    def 시장가_매수_주문(self):
        print('[시장가 매수 주문]')
        print(self.보유_현금, self.수수료포함 * 2)
        if self.보유_현금 < self.수수료포함 * 2:
            print('매수 자금 부족')
            return
        print('매수 자금 충분')
        URL = 'https://api.upbit.com/v1/orders'
        for symbol in ['BTC', 'ETH']:
            params = dict(
                market=f'KRW-{symbol}',
                side='bid',
                price=self.투자단위,
                ord_type='price'
            )
            requests.post(URL,
                json=params,
                headers=self.header_with_parameter(params))

    def 지정가_매도_주문(self):
        print('[지정가 매도 주문]')
        URL = 'https://api.upbit.com/v1/orders'
        for symbol in ['BTC', 'ETH']:
            print(symbol)
            data = self.계좌.loc[symbol]
            price = math.ceil(data.avg_buy_price * 1.1 / 1000) * 1000
            print(f'매도 목표가 : {price}')
            params = dict(
                market=f'KRW-{symbol}',
                side='ask',
                volume=data.balance,
                price=price,
                ord_type='limit',
            )
            res = requests.post(URL,
                json=params,
                headers=self.header_with_parameter(params))
            print(res.status_code)
    def 기존_매도_주문_확인(self):
        print('[기존 매도 주문 확인]')
        URL = 'https://api.upbit.com/v1/orders'
        params = dict(
            state='wait'
        )
        res = requests.get(URL,
                params=params,
                headers=self.header_with_parameter(params))        
        df = pd.DataFrame(res.json())
        self.기존_매도_주문 = None
        if len(df):
            self.기존_매도_주문 = df.loc[:, 'uuid']
        print(self.기존_매도_주문)
    
    def 기존_매도_주문_취소(self):
        print('[기존 매도 주문 취소]')
        if self.기존_매도_주문 is None:
            print('취소할 기존 주문이 없습니다')
            return
        URL = 'https://api.upbit.com/v1/order'
        for id in self.기존_매도_주문:
            params = dict(uuid=id)
            res = requests.delete(URL,
                    params=params,
                    headers=self.header_with_parameter(params))        
            print(res.json())
        print('모든 주문 취소 완료')