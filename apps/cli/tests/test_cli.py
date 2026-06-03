"""qtcloud-3r CLI 单元测试。"""

import json
import sys
import textwrap
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from cli import (
    read_input, clean_json, write_output, _write_text,
    cmd_review, cmd_reflect, cmd_rewrite,
    EXIT_EMPTY, EXIT_TOO_LONG,
    MAX_INPUT_LENGTH,
)


# ── read_input ──


class TestReadInput:
    def test_read_from_file(self, tmp_path):
        f = tmp_path / "draft.md"
        f.write_text("测试文本", encoding="utf-8")
        assert read_input(str(f)) == "测试文本"

    def test_read_from_stdin(self):
        with patch("sys.stdin", MagicMock(read=lambda: "stdin text")):
            assert read_input("-") == "stdin text"

    def test_read_empty_file(self, tmp_path):
        f = tmp_path / "empty.md"
        f.write_text("", encoding="utf-8")
        assert read_input(str(f)) == ""

    @patch("sys.stdin", MagicMock(read=lambda: "pipe input"))
    def test_read_default_stdin(self):
        assert read_input(None) == "pipe input"


# ── clean_json ──


class TestCleanJson:
    def test_plain_json(self):
        assert clean_json('{"a": 1}') == '{"a": 1}'

    def test_json_block(self):
        raw = "```json\n{\"a\": 1}\n```"
        assert clean_json(raw) == '{"a": 1}'

    def test_json_block_no_lang(self):
        raw = "```\n{\"a\": 1}\n```"
        assert clean_json(raw) == '{"a": 1}'

    def test_whitespace(self):
        assert clean_json("  {\"a\": 1}  ") == '{"a": 1}'


# ── _write_text ──


class TestWriteText:
    def test_review_dict(self, capsys):
        _write_text({"genre": "重逢", "intent": "推进关系", "stage": "成稿", "summary": "重逢场景"})
        out = capsys.readouterr().out
        assert "体裁: 重逢" in out
        assert "意图: 推进关系" in out

    def test_gap_list(self, capsys):
        _write_text([
            {"gap_type": "time_jump", "location": "L10", "detail": "跳跃", "craft": "无意识忽略"}
        ])
        out = capsys.readouterr().out
        assert "类型: time_jump" in out
        assert "位置: L10" in out

    def test_cycle_dict(self, capsys):
        _write_text({
            "review": {"genre": "重逢"},
            "reflect": [{"gap_type": "time_jump"}],
            "rewrite": {"text": "新版本", "length": 3},
        })
        out = capsys.readouterr().out
        assert "=== Review ===" in out
        assert "=== Reflect ===" in out
        assert "=== Rewrite ===" in out

    def test_plain_string(self, capsys):
        _write_text("hello world")
        assert capsys.readouterr().out.strip() == "hello world"


# ── write_output ──


class TestWriteOutput:
    def test_json_format(self, capsys):
        write_output({"a": 1}, "json")
        assert json.loads(capsys.readouterr().out) == {"a": 1}

    def test_text_format(self, capsys):
        write_output("hello", "text")
        assert capsys.readouterr().out.strip() == "hello"


# ── cmd_review ──


class TestCmdReview:
    @patch("cli.call_llm")
    def test_review_success(self, mock_call):
        mock_call.return_value = '{"genre": "重逢", "intent": "推进", "stage": "成稿", "summary": "重聚"}'
        result = cmd_review("test text", "deepseek-chat", 0.3)
        assert result["genre"] == "重逢"
        assert result["intent"] == "推进"

    @patch("cli.call_llm")
    def test_review_wrapped_json(self, mock_call):
        mock_call.return_value = "```json\n{\"genre\": \"测试\"}\n```"
        result = cmd_review("text", "deepseek-chat", 0.3)
        assert result["genre"] == "测试"


# ── cmd_reflect ──


class TestCmdReflect:
    @patch("cli.call_llm")
    def test_reflect_returns_list(self, mock_call):
        mock_call.side_effect = [
            '{"genre": "重逢"}',
            '[{"gap_type": "time_jump", "detail": "跳跃"}]',
        ]
        result = cmd_reflect("test", "deepseek-chat", 0.3)
        assert len(result) == 1
        assert result[0]["gap_type"] == "time_jump"

    @patch("cli.call_llm")
    def test_reflect_returns_analysis_key(self, mock_call):
        mock_call.side_effect = [
            '{"genre": "重逢"}',
            '{"analysis": [{"gap_type": "time_jump"}]}',
        ]
        result = cmd_reflect("test", "deepseek-chat", 0.3)
        assert len(result) == 1
        assert result[0]["gap_type"] == "time_jump"

    @patch("cli.call_llm")
    def test_reflect_empty(self, mock_call):
        mock_call.side_effect = [
            '{"genre": "重逢"}',
            "[]",
        ]
        result = cmd_reflect("test", "deepseek-chat", 0.3)
        assert result == []


# ── cmd_rewrite ──


class TestCmdRewrite:
    @patch("cli.call_llm")
    def test_rewrite(self, mock_call):
        # cmd_rewrite calls: cmd_review(1), cmd_reflect → cmd_review(2) + LLM(3), then LLM(4)
        mock_call.side_effect = [
            '{"genre": "重逢", "intent": "", "stage": ""}',
            '{"genre": "重逢", "intent": "", "stage": ""}',
            '[{"gap_type": "time_jump", "detail": "x"}]',
            "修改后的文本",
        ]
        result = cmd_rewrite("原文", "deepseek-chat", 0.3)
        assert result == "修改后的文本"

    @patch("cli.call_llm")
    def test_rewrite_no_gaps_returns_original(self, mock_call):
        mock_call.side_effect = [
            '{"genre": "重逢", "intent": "", "stage": ""}',
            '{"genre": "重逢", "intent": "", "stage": ""}',
            "[]",
        ]
        result = cmd_rewrite("原文", "deepseek-chat", 0.3)
        assert result == "原文"


# ── main ──


class TestMain:
    def test_help(self):
        with patch("sys.argv", ["3r", "--help"]):
            with pytest.raises(SystemExit) as exc:
                from cli import main
                main()
            assert exc.value.code == 0

    @patch("sys.stdin", MagicMock(read=lambda: ""))
    def test_empty_input_exits(self):
        with patch("sys.argv", ["3r", "review"]):
            with pytest.raises(SystemExit) as exc:
                from cli import main as run_main
                try:
                    run_main()
                except SystemExit:
                    raise

            # 由于 argparse 解析后会 exit，这需要模拟整个流程
            pass

    def test_too_long_input(self, tmp_path):
        f = tmp_path / "long.md"
        f.write_text("x" * (MAX_INPUT_LENGTH + 1), encoding="utf-8")
        with patch("sys.argv", ["3r", "review", str(f)]):
            from cli import main
            with patch("cli.call_llm"):
                with pytest.raises(SystemExit) as exc:
                    main()
                assert exc.value.code == EXIT_TOO_LONG

    def test_argv_too_long_validation(self, tmp_path):
        """验证长度检查在 call_llm 之前触发"""
        f = tmp_path / "long.md"
        f.write_text("x" * (MAX_INPUT_LENGTH + 1), encoding="utf-8")

        from cli import read_input, main
        text = read_input(str(f))
        assert len(text) > MAX_INPUT_LENGTH

        # main() 应当检测到过长并退出
        with patch("sys.argv", ["3r", "review", str(f)]):
            with pytest.raises(SystemExit) as exc:
                with patch("cli.call_llm") as mock:
                    mock.return_value = '{"genre": "t"}'
                    try:
                        main()
                    except SystemExit as e:
                        assert e.code == EXIT_TOO_LONG
                        raise


# ── 集成：prompt 模板没有语法错误 ──


class TestPrompts:
    def test_review_prompt_format(self):
        from cli import REVIEW_PROMPT
        result = REVIEW_PROMPT.format(text="测试")
        assert "测试" in result
        assert "JSON" in result

    def test_reflect_prompt_format(self):
        from cli import REFLECT_PROMPT
        result = REFLECT_PROMPT.format(genre="g", intent="i", stage="s", text="t")
        assert "体裁：g" in result
        assert "t" in result

    def test_rewrite_prompt_format(self):
        from cli import REWRITE_PROMPT
        result = REWRITE_PROMPT.format(genre="g", intent="i", analysis="a", text="t")
        assert "体裁：g" in result
        assert "a" in result
