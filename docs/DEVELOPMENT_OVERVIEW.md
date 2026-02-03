# 🚀 MACH_VII v2.0 개발 현황

## 👵 최종 목적: Silver Physical AI Sitter
본 프로젝트는 어르신의 시각 보조(약 읽기 등), 물리 케어(안경 가져오기, 등 긁어주기 등), 정서 교감을 수행하며 스스로 성장하는 AI 시터 구축을 최종 목표로 합니다.

2026.02.04

---

## 🏗️ 레이어별 개발 진척도 요약

| 레이어 | 상태 | 주요 현황 요약 |
| :--- | :---: | :--- |
| **L1. Sensor** | 🟢 완료/확장 중 | 기초 리팩토링 완료. 그리퍼-월드 멀티 카메라 시스템 고도화 중. |
| **L2. State** | 🟡 고도화 중 | 전역 상태 중앙 관리. `arm_status`, `focus_score` 등 관제탑 필드 추가 예정. |
| **L3. Brain** | 🟡 운용 중 | 시터 페르소나 및 자가 수정(Self-Correction) 로직 구축 예정. |
| **L4. Strategy** | 🟡 설계 중 | **3-Mode (Safety/Exploration/Exploitation)** 책임 분리 아키텍처 설계 중. |
| **L5. Expression** | ⚪ 대기 | 어르신 친화적 시표정 및 감정 레이어 통합 예정. |
| **L6. Embodiment** | 🟡 연동 중 | 시뮬레이션 서버(pybullet_deploy) 연동 갱신 및 서보잉 최적화 진행 중. |
| **L7. Memory** | 🟡 운용 중 | FalkorDB 기반 에피소드 저장 및 개인화 학습 엔진 가동. |

---

## 🛠️ 섹션별 상세 고도화 계획 (Advanced Roadmap)

### 🧿 1. 계층적 시각 및 정밀 인지 (Vision Assistant)
*   **Hierarchical Mapping**: 그리퍼 카메라(Main)와 월드 카메라(Sub)의 데이터를 결합하여 광역 탐색 후 정밀 파지 수행.
*   **VLM Steadycam**: 약병/처방전 읽기 시 로봇을 고정(`Soft Lock`)하여 고해상도 이미지 분석 수행 (Gemma 3 연동).
*   **Dynamic Kinematics**: 로봇 관절값과 연동된 실시간 3D 좌표 변환으로 그리퍼 회전 시 생기는 시차 오차 제거.

### 🦾 2. 상태 관제탑 및 안전 제어 (Control Tower)
*   **실시간 모니터링**: `sim_client.py`를 통해 서버의 `gripper_state`, `joints` 피드백을 실시간 수용.
*   **Safety Loop**: 신체 접촉 시 `arm_status`(STUCK)를 감시하여 즉각적인 보호 동작 및 사과 피드백 실행.
*   **Focus Score**: 영상 선명도 측정 알고리즘을 통해 인지 결과의 신뢰도 보장.

### 🧠 3. 성장하는 시터 (3-Mode & Self-Learning)
*   **3-Mode 책임 분리**:
    *   **Safety**: 자율성 배제, 절대 안전(헌법) 준수.
    *   **Exploration**: LLM이 DB의 실패 기록을 보고 스스로 계획을 수정하여 시도.
    *   **Exploitation**: 성공 데이터 기반의 안정적이고 숙련된 동작 재현.
*   **DB-Driven Intelligence**: FalkorDB 성공률과 현재 상황의 일치도(`db_sync_level`)에 따른 지능형 하이퍼 루프 구축.

---

## 🚩 주요 마일스톤 (Milestones)

1.  **[26.02] 하위 레이어 기초 리팩토링** (완료)
2.  **[26.02] 시뮬레이션 서버(pybullet_deploy) 핵심 연동** (진행 중)
    - `sim_client` EE 카메라 및 그리퍼 피드백 수용
    - `visual_servoing` 루프 최적화
3.  **[26.02] 상태 관제탑(Control Tower) 및 3-Mode 구축** (예정)
4.  **[26.03] 실버 시터 시입 시나리오(약 읽기, 등 긁기) 실증** (예정)

---
*본 문서는 실버 시터 비전을 실현하기 위한 기술적 로드맵을 포함하며, 매 수정 시 최신화됩니다.*
