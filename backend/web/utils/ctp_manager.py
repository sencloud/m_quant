import threading
from threading import Thread, Lock
from queue import Queue
import logging
import json
import os
import time
from ...ctp.trade import CTPStore

logger = logging.getLogger(__name__)

# 全局队列用于处理交易请求
trade_queue = Queue()

class CTPManager(Thread):
    """CTP管理器，负责CTPStore的初始化和维护"""
    
    def __init__(self):
        super().__init__(daemon=True)
        self.store = None
        self.running = True
        self.initialized = False
        self.init_lock = Lock()

    def initialize_store(self):
        """初始化CTPStore"""
        try:
            params_path = os.path.join(os.path.dirname(__file__), '..', '..', 'ctp', 'params.json')
            with open(params_path, 'r') as f:
                ctp_setting = json.load(f)
            
            with self.init_lock:
                self.store = CTPStore(ctp_setting, debug=True)
                self.initialized = True
            logger.info("CTPStore initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize CTPStore: {e}")
            self.initialized = False

    def get_store(self):
        """获取CTPStore实例"""
        with self.init_lock:
            return self.store if self.initialized else None

    def run(self):
        """线程主循环"""
        self.initialize_store()
        
        while self.running:
            try:
                if not trade_queue.empty():
                    trade_request = trade_queue.get()
                    self.process_trade(trade_request)
                time.sleep(0.1)  # 避免CPU过度使用
            except Exception as e:
                logger.error(f"Error in CTP manager loop: {e}")

    def process_trade(self, trade_request):
        """处理交易请求"""
        from ..services.trade_service import TradeService
        
        try:
            if not self.initialized:
                raise Exception("CTPStore not initialized")

            # 更新交易状态为处理中
            TradeService.update_trade_status(trade_request['id'], 'processing')

            # 执行交易
            with self.init_lock:
                result = self.execute_trade(trade_request)

            # 更新交易状态为完成
            TradeService.update_trade_status(trade_request['id'], 'completed')
            logger.info(f"Trade processed successfully: {trade_request}")

        except Exception as e:
            logger.error(f"Error processing trade: {e}")
            TradeService.update_trade_status(trade_request['id'], 'failed', str(e))

    def execute_trade(self, trade_request):
        """执行具体的交易操作"""
        # 实现具体的交易逻辑
        pass

    def stop(self):
        """停止CTP管理器"""
        self.running = False
        if self.store:
            self.store.close()

# 创建全局CTP管理器实例
ctp_manager = CTPManager()