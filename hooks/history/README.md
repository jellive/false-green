# hooks/history

측정에 쓴 옛 훅 버전. 배포하는 것은 `../coverage-gate.py`(v3)다.

| 파일 | 내용 해시 | 무엇 |
|---|---|---|
| `coverage-gate.v1.py` | `0f66f71f` | 첫 판. holdout 에서 버그 3개가 드러났다(cwd · 커밋 · pnpm 파서) |
| `coverage-gate.v2.py` | `5436cf8d` | 셋을 고친 판. **README·RESULTS 의 holdout 수치는 이 버전의 것이다** |

재현 테스트를 옛 버전에 돌리면 고친 케이스가 실패한다 — 그게 테스트가 진짜라는 증거다:

```bash
python3 ../test_coverage_gate.py coverage-gate.v2.py    # 6/15
python3 ../test_coverage_gate.py                        # 15/15 (v3)
```
