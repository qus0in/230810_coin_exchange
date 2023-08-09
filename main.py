from market import Exchange
from dotenv import load_dotenv

if __name__ == '__main__':
    load_dotenv()
    exchange = Exchange()
    exchange.전체_계좌_조회() # exchange.계좌
    exchange.현재가_조회() # exchange.시세
    exchange.총자산_조회() # exchange.총자산
    # exchange.원화_입금()
    # TODO : 입금 내역 조회하여 금일 입금 있는지 확인
    # TODO : 1분씩 3번 확인 (T/F) -> if문
    # TODO : 입금이 제대로 안되면 Telegram 메세징 (케이뱅크 부족?)
    # exchange.전체_계좌_조회()
    # exchange.시장가_매수_주문()
    # TODO : Done 중에 금일 체결된게 있는지 확인
    exchange.기존_매도_주문_확인()
    exchange.기존_매도_주문_취소()
    exchange.전체_계좌_조회()
    exchange.지정가_매도_주문()