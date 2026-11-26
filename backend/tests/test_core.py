from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.services.difficulty import evaluate_next_difficulty


def test_difficulty_engine_upgrade_and_downgrade():
    up = evaluate_next_difficulty(
        current_difficulty=3.0,
        score_comprehension=5,
        score_accuracy=4,
        score_completion=5,
        score_engagement=4,
        instructor_suggestion="UP",
    )
    assert up.new_difficulty > 3.0
    assert up.delta > 0

    down = evaluate_next_difficulty(
        current_difficulty=3.0,
        score_comprehension=1,
        score_accuracy=2,
        score_completion=2,
        score_engagement=2,
        instructor_suggestion="DOWN",
    )
    assert down.new_difficulty < 3.0
    assert down.delta < 0

    # 防震盪：微小波動維持不變
    keep = evaluate_next_difficulty(
        current_difficulty=3.0,
        score_comprehension=3,
        score_accuracy=3,
        score_completion=3,
        score_engagement=3,
        instructor_suggestion="KEEP",
    )
    assert keep.new_difficulty == 3.0
    assert keep.delta == 0.0


def test_full_api_workflow_and_pdf_generation():
    with TestClient(app) as client:
        # 1. 講師登入
        res = client.post("/api/auth/login", json={"username": "teacher_lin", "password": "teacher123"})
        assert res.status_code == 200
        t_token = res.json()["access_token"]
        t_headers = {"Authorization": f"Bearer {t_token}"}

        # 講師只看得到自己的 2 個班級
        res = client.get("/api/classes", headers=t_headers)
        assert res.status_code == 200
        t_classes = res.json()
        assert len(t_classes) == 2
        target_class = t_classes[0]

        # 2. 預覽自動排課計畫
        res = client.post(
            "/api/lessons/preview-plan",
            headers=t_headers,
            json={
                "class_id": target_class["id"],
                "unit_id": target_class["current_unit_id"],
                "duration_min": 180,
                "include_cover": True,
            },
        )
        assert res.status_code == 200
        plan = res.json()
        selected_ids = [item["slide"]["id"] for item in plan["items"] if item["selected"]]
        assert len(selected_ids) >= 6

        # 3. 產出真實 A4 PDF
        res = client.post(
            "/api/lessons/generate-pdf",
            headers=t_headers,
            json={
                "class_id": target_class["id"],
                "unit_id": target_class["current_unit_id"],
                "duration_min": 180,
                "include_cover": True,
                "selected_slide_ids": selected_ids[:5],
            },
        )
        assert res.status_code == 200
        doc = res.json()
        assert doc["page_count"] == 6  # 1 封面 + 5 板書頁
        dl_res = client.get(doc["download_url"])
        assert dl_res.status_code == 200
        assert dl_res.headers["content-type"] == "application/pdf"
        assert len(dl_res.content) > 10000

        # 4. 講師提交課後回報並觸發難度重算
        res = client.post(
            "/api/lessons/logs",
            headers=t_headers,
            json={
                "class_id": target_class["id"],
                "unit_id": target_class["current_unit_id"],
                "score_comprehension": 5,
                "score_accuracy": 5,
                "score_completion": 5,
                "score_engagement": 5,
                "instructor_suggestion": "UP",
                "completed_slide_order": 10,
                "notes": "全班吸收極佳，可挑戰更高難度",
            },
        )
        assert res.status_code == 200
        log = res.json()
        assert log["calc_difficulty_after"] > log["calc_difficulty_before"]

        # 5. 講師無權執行管理員 Override
        res = client.post(
            f"/api/classes/{target_class['id']}/override",
            headers=t_headers,
            json={"new_difficulty": 2.5, "reason": "越權測試"},
        )
        assert res.status_code == 403

        # 6. 管理員登入並覆寫難度與進度
        res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        assert res.status_code == 200
        a_headers = {"Authorization": f"Bearer {res.json()['access_token']}"}

        res = client.get("/api/classes", headers=a_headers)
        assert res.status_code == 200
        assert len(res.json()) == 3

        res = client.post(
            f"/api/classes/{target_class['id']}/override",
            headers=a_headers,
            json={
                "new_difficulty": 4.5,
                "last_completed_slide_order": 12,
                "admin_note": "管理員核定：下堂直接進入資優 B/C 壓軸題",
                "reason": "管理員審核後直接拉升至 Lv.5",
            },
        )
        assert res.status_code == 200
        updated = res.json()
        assert updated["current_difficulty"] == 4.5
        assert updated["last_completed_slide_order"] == 12

        # 7. 上傳教材自動解析並組成備課單元
        sample_material = (
            "觀念 1 平行四邊形面積 (P.90)\n"
            "核心公式：底 × 高\n"
            "速解：高必須垂直於底邊\n\n"
            "演練 1 P.91\n"
            "1. 底 12 公分、高 8 公分，面積 = 96\n"
        )
        res = client.post(
            "/api/units/upload-material",
            headers=a_headers,
            data={
                "unit_code": "G5-U11",
                "unit_title": "五上11 面積計算",
                "grade_term": "五上",
                "save_to_db": "true",
                "use_ai": "false",
                "raw_text": sample_material,
            },
        )
        assert res.status_code == 200
        up_data = res.json()
        assert up_data["parsed_count"] >= 2
        assert up_data["unit_id"] is not None

        # 8. 跨單元／頁碼範圍自動組卷並產出 PDF
        res = client.post(
            "/api/lessons/range-preview",
            headers=t_headers,
            json={
                "class_id": target_class["id"],
                "unit_ids": [target_class["current_unit_id"], up_data["unit_id"]],
                "page_start": 70,
                "page_end": 92,
                "duration_min": 180,
                "include_cover": True,
            },
        )
        assert res.status_code == 200
        r_plan = res.json()
        r_selected = [i["slide"]["id"] for i in r_plan["items"] if i["selected"]]
        assert len(r_selected) >= 3

        res = client.post(
            "/api/lessons/generate-range-pdf",
            headers=t_headers,
            json={
                "class_id": target_class["id"],
                "unit_ids": [target_class["current_unit_id"], up_data["unit_id"]],
                "range_title": "P.70~P.92 跨單元複習",
                "duration_min": 180,
                "include_cover": True,
                "selected_slide_ids": r_selected[:4],
            },
        )
        assert res.status_code == 200
        assert res.json()["page_count"] == 5

