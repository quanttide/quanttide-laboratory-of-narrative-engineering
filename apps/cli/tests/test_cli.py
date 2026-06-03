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
    EXIT_EMPTY, EXIT_TOO_LONG, EXIT_PARSE_ERROR, EXIT_API_ERROR,
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


# ── 边缘情况 ──


class TestEdgeCases:
    def test_write_text_unknown_dict(self, capsys):
        """不匹配 review/cycle 的 dict 走 key-value 兜底"""
        _write_text({"foo": "bar", "num": 42})
        out = capsys.readouterr().out
        assert "foo: bar" in out
        assert "num: 42" in out

    def test_call_llm_no_api_key(self):
        """API key 缺失时调用 cmd_review 应报错退出"""
        import cli
        with patch.object(cli, "DEEPSEEK_API_KEY", ""):
            with pytest.raises(SystemExit) as exc:
                cli.cmd_review("text", "deepseek-chat", 0.3)
            assert exc.value.code == 1

    def test_main_cycle_command(self, tmp_path):
        f = tmp_path / "d.md"
        f.write_text("测试文本", encoding="utf-8")
        with patch("sys.argv", ["3r", "cycle", str(f)]):
            from cli import main
            with patch("cli.cmd_review") as r, patch("cli.cmd_reflect") as rf, patch("cli.cmd_rewrite") as rw:
                r.return_value = {"genre": "t"}
                rf.return_value = [{"gap_type": "time_jump"}]
                rw.return_value = "新版本"
                main()
                r.assert_called_once()
                rf.assert_called_once()
                rw.assert_called_once()

    def test_main_json_decode_error(self, tmp_path):
        f = tmp_path / "d.md"
        f.write_text("测试文本", encoding="utf-8")
        with patch("sys.argv", ["3r", "review", str(f)]):
            from cli import main
            with patch("cli.call_llm") as mock:
                mock.return_value = "not json"
                with pytest.raises(SystemExit) as exc:
                    main()
                assert exc.value.code == EXIT_PARSE_ERROR

    def test_main_api_error(self, tmp_path):
        f = tmp_path / "d.md"
        f.write_text("测试文本", encoding="utf-8")
        with patch("sys.argv", ["3r", "review", str(f)]):
            from cli import main
            with patch("cli.call_llm") as mock:
                from requests import RequestException
                mock.side_effect = RequestException("connection failed")
                with pytest.raises(SystemExit) as exc:
                    main()
                assert exc.value.code == EXIT_API_ERROR

    def test_main_reflect_command(self, tmp_path):
        """main() reflect 分支"""
        f = tmp_path / "d.md"
        f.write_text("测试文本", encoding="utf-8")
        with patch("sys.argv", ["3r", "reflect", str(f)]):
            from cli import main
            with patch("cli.cmd_reflect") as mock:
                mock.return_value = [{"gap_type": "t"}]
                main()

    def test_main_rewrite_json(self, tmp_path):
        """main() rewrite json 分支"""
        f = tmp_path / "d.md"
        f.write_text("测试文本", encoding="utf-8")
        with patch("sys.argv", ["3r", "rewrite", str(f), "--format", "json"]):
            from cli import main
            with patch("cli.cmd_rewrite") as mock:
                mock.return_value = "修改后"
                main()

    def test_main_rewrite_text(self, tmp_path):
        """main() rewrite text 分支"""
        f = tmp_path / "d.md"
        f.write_text("测试文本", encoding="utf-8")
        with patch("sys.argv", ["3r", "rewrite", str(f), "--format", "text"]):
            from cli import main
            with patch("cli.cmd_rewrite") as mock:
                mock.return_value = "修改后"
                main()

    def test_main_reflect_empty(self, tmp_path):
        """main() reflect 空结果 → exit 4"""
        f = tmp_path / "d.md"
        f.write_text("测试文本", encoding="utf-8")
        with patch("sys.argv", ["3r", "reflect", str(f)]):
            from cli import main
            with patch("cli.cmd_reflect") as mock:
                mock.return_value = []
                with pytest.raises(SystemExit) as exc:
                    main()
                assert exc.value.code == EXIT_EMPTY


class TestCallLLM:
    """直接测试 call_llm 的 HTTP 调用层"""

    @patch("cli.requests.post")
    def test_call_llm_success(self, mock_post):
        mock_post.return_value.json.return_value = {
            "choices": [{"message": {"content": "回复内容"}}]
        }
        import cli
        result = cli.call_llm("提示词", model="deepseek-chat", temp=0.3)
        assert result == "回复内容"
        mock_post.assert_called_once()

    @patch("cli.requests.post")
    def test_call_llm_with_system(self, mock_post):
        mock_post.return_value.json.return_value = {
            "choices": [{"message": {"content": "回复"}}]
        }
        import cli
        result = cli.call_llm("提示词", system="你是一个助手", model="deepseek-chat", temp=0.3)
        assert result == "回复"

    @patch("cli.requests.post")
    def test_call_llm_http_error(self, mock_post):
        """HTTP 错误经 main() 捕获后 exit(2)"""
        from requests import HTTPError
        mock_resp = mock_post.return_value
        mock_resp.raise_for_status.side_effect = HTTPError("403 Forbidden")
        import cli

        # 通过 cmd_review 触发 call_llm，异常会上抛到 main 的 except
        with patch("sys.argv", ["3r", "review", "/dev/null"]):
            with patch("cli.read_input", return_value="test"):
                with pytest.raises(SystemExit) as exc:
                    cli.main()
                assert exc.value.code == EXIT_API_ERROR


class TestCmdReflectFallback:
    """cmd_reflect 的 JSON 解析兜底"""

    @patch("cli.call_llm")
    def test_reflect_unexpected_format_returns_empty(self, mock_call):
        """LLM 返回既不是数组也不是 analysis 键 → 返回 []"""
        mock_call.side_effect = [
            '{"genre": "t"}',
            '{"unexpected": "format"}',
        ]
        result = cmd_reflect("text", "deepseek-chat", 0.3)
        assert result == []


class TestMainModule:
    """__main__.py 入口调用"""

    def test_main_module(self):
        """python -m cli 等价于调用 main()"""
        with patch("cli.main") as mock_main:
            import cli.__main__
            mock_main.assert_called_once()


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
