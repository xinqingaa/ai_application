"""
chat_cli.py
第七章综合项目：支持多轮对话、流式输出、JSON 模式、导出和状态管理的命令行工具

运行方式：
    python chat_cli.py
    python chat_cli.py --demo
    python chat_cli.py --script commands.txt
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))

from llm_service import ProjectLLMService, load_env_if_possible


HELP_TEXT = """
可用命令：
/help                     显示帮助
/provider <name>          切换 provider，例如 /provider deepseek
/model <name>             切换 model
/system <text>            设置 system prompt
/json [on|off]            开启或关闭 JSON 模式
/stream [on|off]          开启或关闭流式输出
/temperature <float>      设置 temperature
/max_tokens <int>         设置 max_tokens
/prompt <path>            从文件读取 prompt 并立即发送
/stats                    查看当前会话统计
/export                   导出当前会话到 exports/
/clear                    清空当前会话历史
/new                      新建会话
/session                  查看当前 session_id
/quit                     退出
""".strip()


class ProjectCLI:
    """把命令行交互、命令分发和输出展示收束在一起的入口对象。"""

    def __init__(self) -> None:
        """创建服务层，并初始化当前会话。"""
        self.service = ProjectLLMService()
        self.session = self.service.get_or_create_session()

    def print_state_summary(self) -> None:
        """在进入交互前，先把当前会话的关键配置打印出来。"""
        state = self.service.get_cli_state(self.session.session_id)
        print("当前会话配置：")
        print(f"- session_id: {state.session_id}")
        print(f"- provider: {state.provider}")
        print(f"- model: {state.model}")
        print(f"- json_mode: {state.json_mode}")
        print(f"- stream_mode: {state.stream_mode}")
        print(f"- temperature: {state.temperature}")
        print(f"- max_tokens: {state.max_tokens}")

    def _set_toggle(self, field_name: str, value_text: str | None) -> bool:
        """把 on/off 命令统一映射成 session 上的布尔字段更新。"""
        current = getattr(self.session, field_name)
        if value_text is None:
            new_value = not current
        else:
            normalized = value_text.strip().lower()
            new_value = normalized in {"1", "true", "on", "yes"}
        self.session = self.service.update_session_settings(self.session.session_id, **{field_name: new_value})
        return new_value

    def _send_message(self, text: str) -> None:
        """把普通输入交给服务层，并按流式或非流式两种模式打印结果。"""
        if self.session.stream_mode:
            started = False
            for event in self.service.stream_chat(self.session.session_id, text, quota_subject=self.session.session_id):
                if event["type"] == "start":
                    started = True
                    print(
                        f"AI({event['provider']}/{event['model']})"
                        f"{' [cache]' if event.get('from_cache') else ''}: ",
                        end="",
                        flush=True,
                    )
                elif event["type"] == "token":
                    print(event["delta"], end="", flush=True)
                elif event["type"] == "done":
                    print()
                    result = event["result"]
                    print(
                        f"[done] total_tokens={result['usage']['total_tokens'] if result['usage'] else 'n/a'} "
                        f"elapsed_ms={result['elapsed_ms']:.2f} mocked={result['mocked']}"
                    )
                elif event["type"] == "error":
                    if started:
                        print()
                    error = event["error"]
                    print(f"[error] {error['category']}: {error['message']}")
                    print(f"提示：{error['user_hint']}")
        else:
            result = self.service.chat(self.session.session_id, text, quota_subject=self.session.session_id)
            if result.ok:
                print(f"AI({result.provider}/{result.model}):")
                print(result.reply)
                if result.usage:
                    print(
                        f"[stats] total_tokens={result.usage.total_tokens} "
                        f"elapsed_ms={result.elapsed_ms:.2f} from_cache={result.from_cache}"
                    )
            else:
                print(f"[error] {result.error.category}: {result.error.message}")
                print(f"提示：{result.error.user_hint}")

    def _send_prompt_file(self, path_text: str) -> None:
        """读取 prompt 文件内容，再复用普通消息发送链路。"""
        path = Path(path_text).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        if not path.exists():
            print(f"文件不存在：{path}")
            return
        content = path.read_text(encoding="utf-8")
        print(f"已从文件加载 prompt：{path}")
        self._send_message(content)

    def _new_session(self) -> None:
        """创建一个新的 session，并切到这个 session 上继续聊。"""
        self.session = self.service.get_or_create_session(None)
        print(f"已创建新会话：{self.session.session_id}")

    def handle_command(self, line: str) -> bool:
        """把一行输入分成普通消息或斜杠命令，并返回是否继续运行。"""
        if not line.startswith("/"):
            self._send_message(line)
            return True

        parts = line.strip().split(" ", 1)
        command = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else None

        if command == "/help":
            print(HELP_TEXT)
            return True
        # 这组命令只更新当前 session 配置，不直接触发模型调用。
        if command == "/provider":
            if not arg:
                print("用法：/provider <name>")
                return True
            config = self.service.resolve_config(arg.strip(), model_override=None)
            self.session = self.service.update_session_settings(self.session.session_id, provider=config.provider, model=config.model)
            print(f"已切换 provider -> {config.provider}, model -> {config.model}")
            return True
        if command == "/model":
            if not arg:
                print("用法：/model <name>")
                return True
            self.session = self.service.update_session_settings(self.session.session_id, model=arg.strip())
            print(f"已切换 model -> {self.session.model}")
            return True
        if command == "/system":
            if not arg:
                print("用法：/system <text>")
                return True
            self.session = self.service.update_session_settings(self.session.session_id, system_prompt=arg.strip())
            print("已更新 system prompt。")
            return True
        if command == "/json":
            enabled = self._set_toggle("json_mode", arg)
            print(f"JSON 模式已{'开启' if enabled else '关闭'}。")
            return True
        if command == "/stream":
            enabled = self._set_toggle("stream_mode", arg)
            print(f"流式输出已{'开启' if enabled else '关闭'}。")
            return True
        if command == "/temperature":
            if not arg:
                print("用法：/temperature <float>")
                return True
            try:
                value = float(arg)
            except ValueError:
                print("temperature 必须是数字。")
                return True
            self.session = self.service.update_session_settings(self.session.session_id, temperature=value)
            print(f"temperature 已更新为 {value}")
            return True
        if command == "/max_tokens":
            if not arg:
                print("用法：/max_tokens <int>")
                return True
            try:
                value = int(arg)
            except ValueError:
                print("max_tokens 必须是整数。")
                return True
            self.session = self.service.update_session_settings(self.session.session_id, max_tokens=value)
            print(f"max_tokens 已更新为 {value}")
            return True
        # 这组命令会消费服务层已有能力，或管理当前会话本身。
        if command == "/prompt":
            if not arg:
                print("用法：/prompt <path>")
                return True
            self._send_prompt_file(arg.strip())
            return True
        if command == "/stats":
            print(self.service.format_stats_text(self.session.session_id))
            return True
        if command == "/export":
            path = self.service.export_session(self.session.session_id)
            print(f"会话已导出：{path}")
            return True
        if command == "/clear":
            self.session = self.service.clear_session(self.session.session_id)
            print("当前会话历史已清空。")
            return True
        if command == "/new":
            self._new_session()
            return True
        if command == "/session":
            print(f"当前 session_id: {self.session.session_id}")
            return True
        if command == "/quit":
            return False

        print(f"未知命令：{command}")
        print("输入 /help 查看帮助。")
        return True

    def run_interactive(self) -> None:
        """交互式运行，适合真实使用和逐步学习。"""
        self.print_state_summary()
        print("输入 /help 查看命令。")
        while True:
            try:
                line = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n已退出。")
                return
            if not line:
                continue
            if not self.handle_command(line):
                print("已退出。")
                return

    def run_scripted(self, lines: list[str]) -> None:
        """按脚本顺序执行命令流，适合演示和回归验证。"""
        self.print_state_summary()
        for raw in lines:
            line = raw.strip()
            if not line:
                continue
            print(f"> {line}")
            if not self.handle_command(line):
                print("已退出。")
                return


def load_script_commands(path: Path) -> list[str]:
    """把命令脚本按行读取进来。"""
    return path.read_text(encoding="utf-8").splitlines()


def build_demo_commands() -> list[str]:
    """提供一组最小演示命令，方便快速验证项目链路。"""
    return [
        "/stats",
        "请介绍一下这个 CLI 项目能帮助我练习哪些能力？",
        "/json on",
        "请把本章学习重点整理成 JSON",
        "/stream on",
        "请用流式方式给我一个简短总结",
        "/stats",
        "/export",
        "/quit",
    ]


def main() -> None:
    """CLI 入口：解析参数后选择 demo、脚本或交互模式。"""
    load_env_if_possible()
    parser = argparse.ArgumentParser(description="第七章综合项目 CLI")
    parser.add_argument("--demo", action="store_true", help="运行内置演示命令流")
    parser.add_argument("--script", type=str, default=None, help="从文件读取命令脚本")
    args = parser.parse_args()

    cli = ProjectCLI()
    if args.demo:
        cli.run_scripted(build_demo_commands())
        return
    if args.script:
        cli.run_scripted(load_script_commands(Path(args.script)))
        return
    cli.run_interactive()


if __name__ == "__main__":
    main()
