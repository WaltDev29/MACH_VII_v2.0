from enum import Enum

# 현재는 대화를 진행하며 사용자 명령 자연어에 따른 동작 모션을 수행하는 의도로 제작된 열거형으로, Brain 레이어에서 결정되어 Pipeline을 통해 하위 레이어로 전달됩니다.
# 추후 동작 추가나 새로운 방식으로 개선하는 등 개선의 여지가 있습니다.(아직 방법은 생각 안남)

class ActionIntent(str, Enum):
    """
    맹칠이(MACH-VII)의 최종 판단 결과(의도)를 표준화한 열거형입니다.
    Brain 레이어에서 결정되어 Pipeline을 통해 하위 레이어로 전달됩니다.
    """
    # 1. 상호작용 (Interaction)
    GREET = "GREET"               # 인사, 환영
    TALK = "TALK"                 # 일반 대화 (현재 동작 없음)
    
    # 2. 물체 조작 (Manipulation)
    PICK_UP = "PICK_UP"           # 물체 집기
    PLACE = "PLACE"               # 물체 놓기
    GIVE = "GIVE"                 # 물체 건네주기
    
    # 3. 이동 및 위치 제어 (Mobility)
    MOVE = "MOVE"                 # 특정 좌표로 이동
    LOOK_AT = "LOOK_AT"           # 특정 물체/좌표 주시
    
    # 4. 상태 및 안전 (Safety & State)
    STOP = "STOP"                 # 즉시 정지
    IDLE = "IDLE"                 # 대기 상태
    RECOVER = "RECOVER"           # 오류 복구 시도
    
    # 5. 기타 (System)
    UNKNOWN = "UNKNOWN"           # 정의되지 않은 의도

    @classmethod
    def from_str(cls, text: str):
        """문자열로부터 ActionIntent를 추출하는 유틸리티 메서드"""
        if not text:
            return cls.IDLE
            
        text_upper = text.upper()
        
        # 1. 직접 매칭 확인
        for intent in cls:
            if intent.value in text_upper:
                return intent
                
        # 2. 한국어 키워드 기반 매칭 (Heuristic)
        mapping = {
            "인사": cls.GREET,
            "안녕": cls.GREET,
            "반가워": cls.GREET,
            "잡아": cls.PICK_UP,
            "집어": cls.PICK_UP,
            "가져와": cls.PICK_UP,
            "놓아": cls.PLACE,
            "멈춰": cls.STOP,
            "정지": cls.STOP,
            "이동": cls.MOVE,
            "움직여": cls.MOVE,
            "봐": cls.LOOK_AT,
        }
        
        for keyword, intent in mapping.items():
            if keyword in text:
                return intent
                
        return cls.UNKNOWN
