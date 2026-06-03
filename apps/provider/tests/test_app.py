"""qtcloud-3r 测试。"""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app import (
    cmd_review, cmd_reflect, cmd_rewrite, cmd_cycle,
    clean_json, call_llm, read_text, MAX_INPUT_LENGTH,
)
from app.app import app

client = TestClient(app)


# ── read_text ──


class TestReadText:
    def test_read_existing_file(self, tmp_path):
        f = tmp_path / "draft.md"
        f.write_text("内容", encoding="utf-8")
        assert read_text(str(f)) == "内容"

    def test_read_raw_string(self):
        assert read_text("直接文本") == "直接文本"


# ── clean_json ──


class TestCleanJson:
    def test_plain(self):
        assert clean_json('{"a":1}') == '{"a":1}'

    def test_wrapped(self):
        assert clean_json("```json\n{\"a\":1}\n```") == '{"a":1}'


# ── cmd_review ──


class TestCmdReview:
    @patch("app.call_llm")
    def test_success(self, mock_call):
        mock_call.return_value = '{"genre":"g","intent":"i","stage":"s","summary":"x"}'
        r = cmd_review("text")
        assert r["genre"] == "g"

    @patch("app.call_llm")
    def test_wrapped(self, mock_call):
        mock_call.return_value = "```\n{\"genre\":\"g\"}\n```"
        r = cmd_review("text")
        assert r["genre"] == "g"


# ── cmd_reflect ──


class TestCmdReflect:
    @patch("app.call_llm")
    def test_returns_list(self, mock_call):
        mock_call.side_effect = [
            '{"genre":"g"}',
            '[{"gap_type":"t"}]',
        ]
        r = cmd_reflect("text")
        assert r[0]["gap_type"] == "t"

    @patch("app.call_llm")
    def test_returns_analysis_key(self, mock_call):
        mock_call.side_effect = [
            '{"genre":"g"}',
            '{"analysis":[{"gap_type":"t"}]}',
        ]
        r = cmd_reflect("text")
        assert r[0]["gap_type"] == "t"

    @patch("app.call_llm")
    def test_empty_on_unexpected(self, mock_call):
        mock_call.side_effect = [
            '{"genre":"g"}',
            '{"x":"y"}',
        ]
        assert cmd_reflect("text") == []


# ── cmd_rewrite ──


class TestCmdRewrite:
    @patch("app.call_llm")
    def test_rewrite(self, mock_call):
        mock_call.side_effect = [
            '{"genre":"g","intent":"","stage":""}',
            '{"genre":"g","intent":"","stage":""}',
            '[{"gap_type":"t","detail":"x"}]',
            "修改后",
        ]
        assert cmd_rewrite("原文") == "修改后"

    @patch("app.call_llm")
    def test_no_gaps_returns_original(self, mock_call):
        mock_call.side_effect = [
            '{"genre":"g","intent":"","stage":""}',
            '{"genre":"g","intent":"","stage":""}',
            "[]",
        ]
        assert cmd_rewrite("原文") == "原文"


# ── cmd_cycle ──


class TestCmdCycle:
    @patch("app.cmd_review")
    @patch("app.cmd_reflect")
    @patch("app.cmd_rewrite")
    def test_cycle(self, mock_rw, mock_rf, mock_rv):
        mock_rv.return_value = {"genre": "g", "intent": "", "stage": "", "summary": ""}
        mock_rf.return_value = [{"gap_type": "t"}]
        mock_rw.return_value = "新版本"
        r = cmd_cycle("text")
        assert r["review"]["genre"] == "g"
        assert r["reflect"][0]["gap_type"] == "t"
        assert r["rewrite"] == "新版本"


# ── API ──


class TestAPI:
    def test_review(self):
        with patch("app.call_llm") as mock:
            mock.return_value = '{"genre":"g","intent":"i","stage":"s","summary":"x"}'
            resp = client.post("/review", json={"text": "测试"})
            assert resp.status_code == 200
            assert resp.json()["genre"] == "g"

    def test_review_empty_text(self):
        resp = client.post("/review", json={"text": ""})
        assert resp.status_code == 422

    def test_review_too_long(self):
        resp = client.post("/review", json={"text": "x" * (MAX_INPUT_LENGTH + 1)})
        assert resp.status_code == 422

    def test_reflect(self):
        with patch("app.app.cmd_reflect") as mock:
            mock.return_value = [{"gap_type": "t", "detail": "x"}]
            resp = client.post("/reflect", json={"text": "测试"})
            assert resp.status_code == 200
            assert resp.json()[0]["gap_type"] == "t"

    def test_reflect_empty(self):
        with patch("app.app.cmd_reflect", return_value=[]):
            resp = client.post("/reflect", json={"text": "测试"})
            assert resp.status_code == 200
            assert resp.json() == []

    def test_rewrite(self):
        with patch("app.app.cmd_rewrite") as mock:
            mock.return_value = "修改后"
            resp = client.post("/rewrite", json={"text": "原文"})
            assert resp.status_code == 200
            assert resp.json()["text"] == "修改后"
            assert resp.json()["length"] == 3

    def test_cycle(self):
        with patch("app.app.cmd_review") as rv, patch("app.app.cmd_reflect") as rf, patch("app.app.cmd_rewrite") as rw:
            rv.return_value = {"genre": "g", "intent": "", "stage": "", "summary": ""}
            rf.return_value = [{"gap_type": "t"}]
            rw.return_value = "新版本"
            resp = client.post("/cycle", json={"text": "测试"})
            assert resp.status_code == 200
            body = resp.json()
            assert body["review"]["genre"] == "g"
            assert body["reflect"][0]["gap_type"] == "t"
            assert body["rewrite"]["text"] == "新版本"

    def test_api_error_502(self):
        """所有端点在命令失败时返回 502"""
        for endpoint, cmd in [("/review", "app.app.cmd_review"), ("/reflect", "app.app.cmd_reflect"),
                              ("/rewrite", "app.app.cmd_rewrite"), ("/cycle", "app.app.cmd_review")]:
            with patch(cmd) as mock:
                mock.side_effect = RuntimeError("fail")
                resp = client.post(endpoint, json={"text": "测试"})
                assert resp.status_code == 502, f"{endpoint} should return 502"

    def test_health(self):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200


# ── call_llm ──


class TestCallLLM:
    def test_no_api_key(self):
        import app
        with patch.object(app, "DEEPSEEK_API_KEY", ""):
            with pytest.raises(RuntimeError, match="未设置"):
                app.call_llm("test")

    @patch("app.requests.post")
    def test_with_system_prompt(self, mock_post):
        mock_post.return_value.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
        import app
        result = app.call_llm("提示词", system="你是一个助手")
        assert result == "ok"

    @patch("app.requests.post")
    def test_http_success(self, mock_post):
        mock_post.return_value.json.return_value = {"choices": [{"message": {"content": "回复"}}]}
        import app
        result = app.call_llm("test")
        assert result == "回复"
        mock_post.assert_called_once()
