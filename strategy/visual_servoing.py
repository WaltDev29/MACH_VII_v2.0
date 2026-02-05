# strategy/visual_servoing.py

import logging
import time
import threading
import math
from typing import Dict, Callable, Optional
from enum import Enum, auto

from state.system_state import system_state
from shared.state_broadcaster import broadcaster

class ServoState(Enum):
    """비주얼 서보잉 상태"""
    IDLE = auto()
    DETECT = auto()
    VISUAL_SERVO = auto()  # 연속 제어 루프
    # [Thinking Eye] 능동 인지 상태 추가
    AUTO_FOCUS = auto()    # Z축 최적화 (광학적 선명도 확보)
    VLM_CHECK = auto()     # VLM 검증 ("이거 확실해?")
    SCANNING = auto()      # 그리퍼 회전/이동 (더 잘 보이는 각도 찾기)
    
    GRASP = auto()
    # LIFT, VERIFY 제거 (Agent 주도)
    SUCCESS = auto()
    FAIL = auto()

class VisualServoing:
    """
    연속 제어 기반 비주얼 서보잉
    
    핵심 아이디어:
    - 20Hz 피드백 루프로 실시간 위치 보정
    - 비례 제어 (P-Control)로 오차를 점진적으로 감소
    - PyBullet에서 실시간 수신하는 엔드이펙터 좌표 활용
    - 서버 ACK 불필요 (매 루프에서 현재 위치 확인)
    """
    
    def __init__(self):
        self.lock = threading.Lock()
        self.current_state = ServoState.IDLE
        self.cancel_token = threading.Event()
        self.is_running = False
        
        # 제어 파라미터 (정밀도 우선)
        self.LOOP_HZ = 10           # 루프 주파수 (Hz) - 안정성 우선
        self.GAIN = 0.8             # 비례 제어 게인 (80%씩 보정) - 안정적 이동
        self.XY_THRESHOLD = 1.0     # XY 정렬 판정 (cm) - 정밀 제어
        self.Z_THRESHOLD = 0.5      # Z 도달 판정 (cm) - 정밀 제어
        self.APPROACH_HEIGHT = 8.0  # 접근 높이 오프셋 (cm) - 여유 있게 진입
        self.GRASP_DEPTH = 0.0      # 파지 깊이 오프셋 (cm) - Vision이 정확한 중심을 주므로 오프셋 0
    
    def stop(self):
        """외부에서 호출 가능한 긴급 정지"""
        logging.warning("[VisualServoing] 🛑 긴급 정지 요청!")
        self.cancel_token.set()
    
    def find_target_object(self, target_label: str) -> Optional[Dict]:
        """시스템 상태에서 목표 물체 탐지"""
        objects = system_state.perception_data.get("detected_objects", [])
        candidates = [obj for obj in objects 
                     if target_label.lower() in obj["name"].lower()]
        return candidates[0] if candidates else None
    
    def execute_approach_and_grasp(self,
                             target_label: str,
                             get_ee_position: Callable[[], Dict[str, float]],
                             move_robot: Callable[[float, float, float, int, bool, float], bool],  # wait_arrival, timeout 추가
                             move_gripper: Callable[[float], bool],
                             get_gripper_ratio: Optional[Callable[[], float]] = None,
                             grasp_offset_z: float = -1.5) -> bool:
        """
        비주얼 서보잉 접근 및 파지 (Lift 제외)
        
        Args:
            target_label: 목표 물체 이름
            get_ee_position: 엔드이펙터 위치 조회 함수
            move_robot: 로봇 이동 명령 함수
            move_gripper: 그리퍼 제어 함수
            get_gripper_ratio: 그리퍼 상태 조회 (사용 안 함)
            grasp_offset_z: 파지 깊이 오프셋
        
        Returns:
            성공 여부 (파지 완료 시 True)
        """
        with self.lock:
            if self.is_running:
                logging.warning("[VisualServoing] 이미 실행 중")
                return False
            self.is_running = True
            self.cancel_token.clear()
            self.current_state = ServoState.IDLE
        
        logging.info(f"[VisualServoing] '{target_label}' 접근 및 파지 시작 (Lift 제외)")
        broadcaster.publish("agent_thought", 
                          f"[VisualServoing] '{target_label}' 접근 및 파지 시작")
        
        success = False
        self.GRASP_DEPTH = grasp_offset_z
        
        try:
            # State Machine Loop
            while not self.cancel_token.is_set():
                
                if self.current_state == ServoState.IDLE:
                    self._transition(ServoState.DETECT)
                
                elif self.current_state == ServoState.DETECT:
                    target = self.find_target_object(target_label)
                    if target:
                        logging.info(f"[DETECT] 물체 발견: {target['name']} at {target['position']}")
                        broadcaster.publish("agent_thought", 
                                          f"[VisualServoing] '{target['name']}' 발견")
                        self._transition(ServoState.VISUAL_SERVO)
                    else:
                        logging.warning(f"[DETECT] '{target_label}' 미발견, 재시도...")
                        if self.cancel_token.wait(1.0): break
                        # 3초 동안 3회 재시도
                        retry_count = getattr(self, '_detect_retry', 0)
                        if retry_count >= 3:
                            logging.error(f"[DETECT] '{target_label}' 탐지 실패 (3회)")
                            self._transition(ServoState.FAIL)
                        else:
                            self._detect_retry = retry_count + 1
                
                elif self.current_state == ServoState.VISUAL_SERVO:
                    # 연속 제어 피드백 루프 (접근 단계)
                    if self._visual_servo_loop(target_label, get_ee_position, move_robot):
                        logging.info("[VisualServo] 1차 접근 완료. 정밀 인지 단계로 진입합니다.")
                        # 바로 GRASP하지 않고, Auto-Focus -> VLM Check 로 진입
                        self._transition(ServoState.AUTO_FOCUS)
                    else:
                        self._transition(ServoState.FAIL)
                        
                elif self.current_state == ServoState.AUTO_FOCUS:
                    # [Step 1] 광학적 초점 최적화 (Hill Climbing)
                    if self._execute_auto_focus(get_ee_position, move_robot):
                        self._transition(ServoState.VLM_CHECK)
                    else:
                        logging.warning("[AUTO_FOCUS] 초점 확보 실패 (또는 범위 초과). 그대로 진행합니다.")
                        self._transition(ServoState.VLM_CHECK)
                        
                elif self.current_state == ServoState.VLM_CHECK:
                    # [Step 2] VLM 검증 ("확실한가?")
                    # 로봇 정지 후 이미지 분석 요청
                    check_result = self._execute_vlm_check()
                    
                    if check_result == "CONFIDENT":
                        logging.info("[VLM] 인지 확신! 파지 단계로 이동.")
                        self._transition(ServoState.GRASP)
                    elif check_result == "UNCERTAIN":
                        logging.warning("[VLM] 인지 불확실. 능동 탐색(Scanning) 시작.")
                        self._transition(ServoState.SCANNING)
                    else:
                        logging.error("[VLM] 판단 불가. 실패 처리.")
                        self._transition(ServoState.FAIL)
                        
                elif self.current_state == ServoState.SCANNING:
                    # [Step 3] 능동 탐색 (그리퍼 회전)
                    # 현재 각도에서 +/- 30도 회전하며 후보지 탐색
                    if self._execute_active_scanning(get_ee_position, move_robot):
                        # 자세 변경 후 다시 초점 -> VLM 체크
                        self._transition(ServoState.AUTO_FOCUS)
                    else:
                        logging.error("[SCANNING] 모든 탐색 시도 실패.")
                        self._transition(ServoState.FAIL)
                        
                elif self.current_state == ServoState.GRASP:
                    logging.info("[GRASP] 그리퍼 닫기")
                    broadcaster.publish("agent_thought", 
                                      "[VisualServoing] 그리퍼로 파지 중...")
                    
                    # 그리퍼 닫기 명령 전송
                    move_gripper(0)
                    logging.info("[GRASP] 그리퍼 닫는 중... (3.5초 대기)")
                    
                    # [Improvement] 동적 그리퍼 상태 모니터링
                    # 고정 3.5초 대기 대신, 그리퍼가 움직임을 멈출 때까지 감시합니다.
                    
                    start_grasp_time = time.time()
                    last_gripper_val = system_state.robot.gripper_state
                    stable_count = 0
                    
                    logging.info("[GRASP] 그리퍼 상태 모니터링 시작...")
                    
                    while time.time() - start_grasp_time < 3.5:
                        if self.cancel_token.is_set():
                            break
                            
                        current_val = system_state.robot.gripper_state
                        
                        # 변화량이 미미하면 stable 카운트 증가
                        if abs(current_val - last_gripper_val) < 0.0005:
                            stable_count += 1
                        else:
                            stable_count = 0 # 다시 움직이면 리셋
                            
                        last_gripper_val = current_val
                        
                        # 0.5초(10틱) 이상 변화 없으면 동작 완료로 판단
                        if stable_count >= 10:
                            logging.info(f"[GRASP] 그리퍼 동작 완료 감지 (Stable at {current_val:.4f})")
                            break
                            
                        time.sleep(0.05)
                        
                    if self.cancel_token.is_set():
                        logging.warning("[GRASP] 취소됨")
                        break
                    
                    # [Grasp Verification] 그리퍼 상태 확인
                    # system_state.robot.gripper_state는 두 핑거 각도의 합(또는 너비)입니다.
                    # 0.0에 가까우면(완전히 닫힘) 공기를 잡은 것이고, 
                    # 0.0보다 크면(중간에 멈춤) 물체를 잡은 것입니다.
                    current_gripper = system_state.robot.gripper_state
                    logging.info(f"[GRASP] 그리퍼 최종 상태: {current_gripper:.4f}")
                    
                    if current_gripper > 0.005: # 완전히 닫히지 않음 (=물체 파지)
                        logging.info("[GRASP] ✅ 물체 파지 확인 (Grasp Success)")
                        broadcaster.publish("agent_thought", f"[VisualServoing] 물체 파지 성공 (Width: {current_gripper:.3f})")
                        success = True
                    else:
                        logging.warning("[GRASP] ❌ 빈손 감지 (Grasp Failed - Fully Closed)")
                        broadcaster.publish("agent_thought", "[VisualServoing] 파지 실패 (빈손)")
                        success = False
                        self._transition(ServoState.FAIL)
                        break

                    logging.info("[GRASP] 제어권을 반환합니다.")
                    break
                
                # LIFT, VERIFY 단계 제거됨
                
                elif self.current_state == ServoState.SUCCESS:
                    broadcaster.publish("agent_thought", 
                                      f"[VisualServoing] '{target_label}' 파지 성공! ✅")
                    break
                
                elif self.current_state == ServoState.FAIL:
                    broadcaster.publish("agent_thought", 
                                      "[VisualServoing] 파지 실패 ❌")
                    break
                
                time.sleep(0.01)  # State Machine 루프 주기
        
        except Exception as e:
            logging.error(f"[VisualServoing] 예외 발생: {e}")
            import traceback
            logging.error(traceback.format_exc())
            success = False
        
        finally:
            self.is_running = False
            # [Fix] 성공적인 종료 후에는 취소 토큰이 설정되어도 취소로 간주하지 않음
            if self.cancel_token.is_set() and not success:
                logging.warning("[VisualServoing] 작업이 취소되었습니다")
                broadcaster.publish("agent_thought", 
                                  "[VisualServoing] 작업 취소됨")
                success = False
        
        return success
    
    def _visual_servo_loop(self,
                          target_label: str,
                          get_ee_position: Callable[[], Dict[str, float]],
                          move_robot: Callable[[float, float, float, int], bool]) -> bool:
        """
        연속 제어 피드백 루프
        
        Phase 1 (APPROACH): XY 정렬 (Z는 물체 위 5cm 유지)
        Phase 2 (DESCEND): Z축 하강 (XY 고정)
        
        Returns:
            성공 여부
        """
        phase = "APPROACH"
        timeout = 60.0  # 타임아웃 60초
        start_time = time.time()
        
        logging.info("[VisualServo] 연속 제어 루프 시작 (20Hz)")
        
        while not self.cancel_token.is_set():
            loop_start = time.time()
            
            # 타임아웃 체크
            if time.time() - start_time > timeout:
                logging.warning(f"[VisualServo] 타임아웃 (30초 경과)")
                return False
            
            # 1. 현재 상태 획득
            current_ee = get_ee_position()
            target_obj = self.find_target_object(target_label)
            
            if not target_obj:
                # [개선] 무한 대기 방지
                retry_tracker = getattr(self, '_loop_retry_start', None)
                if retry_tracker is None:
                    self._loop_retry_start = time.time()
                    retry_tracker = time.time()
                
                elapsed_retry = time.time() - retry_tracker
                if elapsed_retry > 2.0:  # 2초간 못 찾으면 실패
                    logging.error("[VisualServo] 물체 소실 타임아웃 (2초)")
                    return False
                
                logging.warning(f"[VisualServo] 물체 소실, 재탐지 대기... ({elapsed_retry:.1f}s)")
                time.sleep(0.1)
                continue
            else:
                self._loop_retry_start = None  # 찾으면 리셋
            
            target_pos = target_obj['position']
            
            # 2. Phase별 목표 위치 설정
            if phase == "APPROACH":
                # Phase 1: XY 정렬 (물체 바로 위)
                goal = {
                    'x': target_pos['x'],
                    'y': target_pos['y'],
                    'z': target_pos['z'] + self.APPROACH_HEIGHT
                }
                
                # XY 오차 계산
                xy_error = math.sqrt(
                    (current_ee['x'] - goal['x'])**2 +
                    (current_ee['y'] - goal['y'])**2
                )
                
                # XY 정렬 완료 판정
                if xy_error < self.XY_THRESHOLD:
                    phase = "DESCEND"
                    logging.info(f"[VisualServo] ✅ XY 정렬 완료 (오차: {xy_error:.2f}cm)")
                    logging.info(f"[VisualServo] Phase 전환: APPROACH → DESCEND")
            
            elif phase == "DESCEND":
                # Phase 2: Z축 하강 (XY 고정)
                goal = {
                    'x': target_pos['x'],
                    'y': target_pos['y'],
                    'z': target_pos['z'] + self.GRASP_DEPTH
                }
                
                # Z 오차 계산
                z_error = abs(current_ee['z'] - goal['z'])
                
                # Z 도달 판정 (매우 엄격: 1.0cm 이내)
                if z_error < self.Z_THRESHOLD:
                    logging.info(f"[VisualServo] ✅ 목표 정밀 도달! (Z 오차: {z_error:.2f}cm)")
                    # 추가 안정화: 0.3초 대기 후 그리퍼 단계로
                    time.sleep(0.3)
                    return True  # 성공
                elif z_error > 3.0:
                    logging.warning(f"[VisualServo] ⚠️ Z 오차 과다: {z_error:.2f}cm (계속 접근 중...)")
            
            # 3. 오차 계산
            error_x = goal['x'] - current_ee['x']
            error_y = goal['y'] - current_ee['y']
            error_z = goal['z'] - current_ee['z']
            
            total_error = math.sqrt(error_x**2 + error_y**2 + error_z**2)
            
            # 4. 비례 제어 (P-Control)
            cmd_x = current_ee['x'] + error_x * self.GAIN
            cmd_y = current_ee['y'] + error_y * self.GAIN
            cmd_z = current_ee['z'] + error_z * self.GAIN
            
            # 5. 속도 조절 (오차가 크면 빠르게, 작으면 느리게)
            if total_error < 3.0:
                speed = 15  # 정밀 모드
            elif total_error < 10.0:
                speed = 30  # 중간 속도
            else:
                speed = 60  # 빠른 접근
            
            # 6. 명령 전송 (중복 필터링 적용)
            # 이전 명령과 거의 동일하면 전송 생략 (통신 부하 및 로그 스팸 방지)
            should_send = True
            if hasattr(self, '_last_sent_cmd'):
                lx, ly, lz, ls = self._last_sent_cmd
                dist = math.sqrt((cmd_x - lx)**2 + (cmd_y - ly)**2 + (cmd_z - lz)**2)
                
                # 위치 변화 0.1cm 미만이고 속도가 같으면 전송 스킵
                if dist < 0.1 and speed == ls:
                    should_send = False
            
            if should_send:
                move_robot(cmd_x, cmd_y, cmd_z, speed)
                self._last_sent_cmd = (cmd_x, cmd_y, cmd_z, speed)
            
            # 7. 주기적 디버그 로그 (5초마다)
            elapsed = time.time() - start_time
            if int(elapsed * 2) % 10 == 0 and elapsed > 0.5:
                logging.debug(
                    f"[VisualServo] Phase={phase}, "
                    f"오차={total_error:.1f}cm, "
                    f"목표=({goal['x']:.1f}, {goal['y']:.1f}, {goal['z']:.1f}), "
                    f"현재=({current_ee['x']:.1f}, {current_ee['y']:.1f}, {current_ee['z']:.1f})"
                )
            
            # 8. 루프 주기 유지 (20Hz = 50ms)
            elapsed_loop = time.time() - loop_start
            sleep_time = (1.0 / self.LOOP_HZ) - elapsed_loop
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        logging.warning("[VisualServo] 취소됨 (cancel_token)")
        return False
    
    def _transition(self, next_state: ServoState):
        """상태 전이 및 로깅"""
        logging.info(f"[VisualServoing] 상태 전환: {self.current_state.name} → {next_state.name}")
        self.current_state = next_state

    def _execute_auto_focus(self, get_ee_position, move_robot) -> bool:
        """
        [AUTO_FOCUS] Hill Climbing 알고리즘으로 Z축 최적화 (선명도 최대화)
        """
        logging.info("[AUTO_FOCUS] 오토 포커스(Hill Climbing) 시작")
        
        step_size = 0.5 # 0.5cm 단위 이동
        max_range = 5.0 # 최대 5cm 탐색
        current_z_offset = 0.0
        
        # 초기 Score 측정
        best_score = system_state.focus_score
        direction = 1 # +Z 방향 (위로) 먼저 시도
        
        # 안전 장치: 시작 위치 저장
        start_pos = get_ee_position()
        
        for i in range(10): # 최대 10회 이동 제한
            if self.cancel_token.is_set(): return False
            
            # 이동
            target_z = start_pos['z'] + current_z_offset + (step_size * direction)
            
            # 범위 체크
            if abs(target_z - start_pos['z']) > max_range:
                logging.warning("[AUTO_FOCUS] 최대 탐색 범위 도달")
                break
                
            move_robot(start_pos['x'], start_pos['y'], target_z, 15) # 느린 속도로 이동
            time.sleep(0.5) # 안정화 대기
            
            new_score = system_state.focus_score
            logging.info(f"[AUTO_FOCUS] Z={target_z:.2f}, Score={new_score:.2f} (Best={best_score:.2f})")
            
            if new_score > best_score + 10.0: # 유의미한 향상 (Threshold 10.0)
                best_score = new_score
                current_z_offset += (step_size * direction)
            else:
                # 점수가 떨어지거나 비슷하면 방향 전환 또는 중단
                if direction == 1:
                    logging.info("[AUTO_FOCUS] 방향 전환 (+Z -> -Z)")
                    direction = -1 # 반대 방향 시도
                    # 다시 원점으로 (약간의 백트래킹)
                    current_z_offset = 0.0 
                    move_robot(start_pos['x'], start_pos['y'], start_pos['z'], 20)
                    time.sleep(0.5)
                else:
                    logging.info("[AUTO_FOCUS] 양방향 탐색 완료. 최적 위치로 복귀.")
                    # 최적 위치 복귀
                    final_z = start_pos['z'] + current_z_offset
                    move_robot(start_pos['x'], start_pos['y'], final_z, 20)
                    return True
                    
        return True

    def _execute_vlm_check(self) -> str:
        """
        [VLM_CHECK] LogicBrain에 VLM 분석 요청 및 Confidence 확인
        Returns: "CONFIDENT", "UNCERTAIN", "FAIL"
        """
        logging.info("[VLM_CHECK] VLM 분석 요청 중...")
        broadcaster.publish("agent_thought", "[Intelligent Eye] 이 위치에서 자세히 보고 있습니다...")
        
        # TODO: LogicBrain과의 비동기 연동 포인트. 
        # 실제 구현에서는 'REQUEST_VLM' 이벤트를 날리고, SystemState에 결과가 업데이트되길 기다려야 함.
        # 이번 단계에서는 개념 증명을 위해 'Focus Score'를 대리 지표(Proxy Metric)로 사용합니다.
        
        time.sleep(1.0) # VLM 처리 대기 시뮬레이션
        
        current_score = system_state.focus_score
        logging.info(f"[VLM_CHECK] 현재 Focus Score: {current_score}")
        
        # Mock Logic: 점수가 50 이상이면 확신으로 간주 (테스트용 Threshold)
        if current_score > 50.0:
            return "CONFIDENT"
        else:
             return "UNCERTAIN"

    def _execute_active_scanning(self, get_ee_position, move_robot) -> bool:
        """
        [SCANNING] 그리퍼 회전 및 미세 이동으로 새로운 관측점 확보
        """
        logging.info("[SCANNING] 능동 탐색: 그리퍼 회전/이동 시도")
        broadcaster.publish("agent_thought", "[Active Perception] 잘 안보여서 각도를 바꿔보는 중입니다...")
        
        # 현재 회전 상태 관리 (단순화를 위해 toggle 방식)
        if not hasattr(self, '_scan_step'):
            self._scan_step = 0
            
        self._scan_step = (self._scan_step + 1) % 4
        
        # 현재 위치 획득
        current_pos = get_ee_position()
        
        # 4방향 미세 이동 (십자 패턴) + Z축 약간 상승(시야 확보)
        # 0: +X, 1: -X, 2: +Y, 3: -Y
        offset_amount = 2.0 # 2cm 이동
        target_x = current_pos['x']
        target_y = current_pos['y']
        
        if self._scan_step == 0: target_x += offset_amount
        elif self._scan_step == 1: target_x -= offset_amount
        elif self._scan_step == 2: target_y += offset_amount
        elif self._scan_step == 3: target_y -= offset_amount
        
        logging.info(f"[SCANNING] 시점 변경 -> ({target_x:.1f}, {target_y:.1f})")
        
        move_robot(target_x, target_y, current_pos['z'], 20)
        time.sleep(1.0)
        return True

# 싱글톤 인스턴스
visual_servoing = VisualServoing()
