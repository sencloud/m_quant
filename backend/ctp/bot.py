# bot.py
from ctpbee import CtpBee
from ctpbee.constant import Direction, Exchange, Offset

app = CtpBee("mybot")

@app.on_start
def start():
    print("CTPbee 已启动")

@app.on_order
def handle_order(order):
    print(f"收到订单: {order}")

# 定义一个下单函数
def place_order(symbol: str, price: float, volume: int, direction: str, offset: str):
    direction_enum = Direction.LONG if direction.lower() == "long" else Direction.SHORT
    offset_enum = Offset.OPEN if offset.lower() == "open" else Offset.CLOSE
    app.send_order(
        price=price,
        volume=volume,
        symbol=symbol,
        exchange=Exchange.SHFE,  # 根据需要选择交易所
        direction=direction_enum,
        offset=offset_enum
    )
