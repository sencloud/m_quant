from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.style import Style
from rich.text import Text
from typing import Dict, Optional
from datetime import datetime
from loguru import logger

console = Console()


class AgentProgress:
    """管理多个代理的进度跟踪"""

    def __init__(self):
        self.agent_status: Dict[str, Dict[str, str]] = {}
        self.table = Table(show_header=False, box=None, padding=(0, 1))
        self.live = Live(self.table, console=console, refresh_per_second=4)
        self.started = False

    def start(self):
        """开始进度显示"""
        if not self.started:
            self.live.start()
            self.started = True
            logger.info("开始显示进度")

    def stop(self):
        """停止进度显示"""
        if self.started:
            self.live.stop()
            self.started = False
            logger.info("停止显示进度")

    def update_status(self, agent_name: str, ticker: Optional[str] = None, status: str = ""):
        """更新代理状态"""
        if agent_name not in self.agent_status:
            self.agent_status[agent_name] = {"status": "", "ticker": None}

        if ticker:
            self.agent_status[agent_name]["ticker"] = ticker
        if status:
            self.agent_status[agent_name]["status"] = status
            logger.info(f"代理 {agent_name} 状态更新: {status}")

        self._refresh_display()

    def _refresh_display(self):
        """刷新进度显示"""
        self.table.columns.clear()
        self.table.add_column(width=100)

        # 对代理进行排序，风险管理和投资组合管理放在底部
        def sort_key(item):
            agent_name = item[0]
            if "risk_management" in agent_name:
                return (2, agent_name)
            elif "portfolio_management" in agent_name:
                return (3, agent_name)
            else:
                return (1, agent_name)

        for agent_name, info in sorted(self.agent_status.items(), key=sort_key):
            status = info["status"]
            ticker = info["ticker"]

            # 创建带有适当样式的状态文本
            if status.lower() == "done":
                style = Style(color="green", bold=True)
                symbol = "✓"
            elif status.lower() == "error":
                style = Style(color="red", bold=True)
                symbol = "✗"
            else:
                style = Style(color="yellow")
                symbol = "⋯"

            agent_display = agent_name.replace("_agent", "").replace("_", " ").title()
            status_text = Text()
            status_text.append(f"{symbol} ", style=style)
            status_text.append(f"{agent_display:<20}", style=Style(bold=True))

            if ticker:
                status_text.append(f"[{ticker}] ", style=Style(color="cyan"))
            status_text.append(status, style=style)

            self.table.add_row(status_text)


# 创建全局实例
progress = AgentProgress()
