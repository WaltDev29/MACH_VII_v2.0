import logging
import time
from typing import Dict, Any, List

try:
    # falkordb 라이브러리 임포트 시도
    from falkordb import FalkorDB
    FALKOR_AVAILABLE = True
except ImportError:
    # 라이브러리가 없으면 플래그를 False로 설정하여 크래시 방지
    FALKOR_AVAILABLE = False

class FalkorDBManager:
    """
    FalkorDB 연결을 관리하고 에피소드 그래프(Episode Graph) 작업을 처리하는 클래스입니다.
    
    [그래프 데이터베이스 스키마 설계]
    1. 노드(Node):
       - (:Episode): 하나의 작업 단위 (속성: id, timestamp, result)
       - (:Action): 수행한 행동 (속성: type, target)
       - (:Emotion): 당시의 감정 상태 (속성: focus, effort, frustration...)
    
    2. 관계(Relationship):
       - (Episode)-[:EXECUTED]->(Action): 에피소드에서 수행된 행동
       - (Episode)-[:STARTED_WITH]->(Emotion): 에피소드 시작 시의 감정
       - (Episode)-[:ENDED_WITH]->(Emotion): 에피소드 종료 시의 감정
    """
    def __init__(self, host='localhost', port=6379):
        self.client = None
        self.graph = None
        self.host = host
        self.port = port
        self.connected = False
        
        if not FALKOR_AVAILABLE:
            logging.warning("[Memory] FalkorDB 라이브러리가 설치되지 않았습니다. 기억 기능이 비활성화됩니다.")

    def connect(self):
        """데이터베이스 서버에 연결을 시도하고 그래프를 선택합니다."""
        if not FALKOR_AVAILABLE: return
        try:
            self.client = FalkorDB(host=self.host, port=self.port)
            # 'MACH_VII_MEMORY' 라는 이름의 그래프를 생성하거나 선택합니다.
            self.graph = self.client.select_graph('MACH_VII_MEMORY')
            self.connected = True
            logging.info(f"[Memory] FalkorDB 연결 성공: {self.host}:{self.port}")
        except Exception as e:
            logging.error(f"[Memory] 연결 실패: {e}")
            self.connected = False

    def save_episode(self, episode_data: Dict[str, Any]):
        """
        완료된 에피소드 데이터를 그래프 데이터베이스에 영구 저장합니다.
        
        Args:
            episode_data (dict): 다음 필드를 포함해야 합니다.
                - id (str): 고유 식별자
                - timestamp (float): 유닉스 타임스탬프
                - result (str): 'success' 또는 'failure'
                - action (dict): {'type': ..., 'target': ...}
                - start_emotion (dict): 시작 시 감정 벡터
                - end_emotion (dict): 종료 시 감정 벡터
        """
        if not self.connected: 
            return

        try:
            # Cypher 쿼리를 사용하여 그래프 노드와 관계를 생성합니다.
            # MERGE: 이미 존재하면 재사용, 없으면 생성 (중복 방지)
            # CREATE: 무조건 생성 (감정 스냅샷은 매번 다르므로 새로 생성)
            query = """
            MERGE (e:Episode {id: $id, timestamp: $ts, result: $res})
            MERGE (a:Action {type: $act_type, target: $act_target})
            MERGE (e)-[:EXECUTED]->(a)
            
            CREATE (start_em:Emotion {focus: $s_focus, effort: $s_effort, frustration: $s_frust})
            CREATE (end_em:Emotion {focus: $e_focus, effort: $e_effort, frustration: $e_frust})
            
            MERGE (e)-[:STARTED_WITH]->(start_em)
            MERGE (e)-[:ENDED_WITH]->(end_em)
            """
            
            params = {
                'id': episode_data['id'],
                'ts': episode_data['timestamp'],
                'res': episode_data['result'],
                'act_type': episode_data['action'].get('type', 'unknown'),
                'act_target': str(episode_data['action'].get('target', 'none')),
                # 시작 감정
                's_focus': episode_data['start_emotion'].get('focus', 0.5),
                's_effort': episode_data['start_emotion'].get('effort', 0.0),
                's_frust': episode_data['start_emotion'].get('frustration', 0.0),
                # 종료 감정
                'e_focus': episode_data['end_emotion'].get('focus', 0.5),
                'e_effort': episode_data['end_emotion'].get('effort', 0.0),
                'e_frust': episode_data['end_emotion'].get('frustration', 0.0),
            }
            
            self.graph.query(query, params)
            logging.info(f"[Memory] 에피소드 저장됨: {episode_data['id']}")
            
        except Exception as e:
            logging.error(f"[Memory] 저장 오류: {e}")

    def get_recent_success_rate(self, action_type: str = None, target: str = None) -> float:
        """
        특정 행동(type)이나 대상(target)에 대한 과거 성공률을 조회합니다.
        
        Returns:
            float: 성공률 (0.0 ~ 1.0). 데이터가 없거나 연결되지 않은 경우 기본값 0.5 반환.
        """
        if not self.connected: return 0.5
        
        try:
            # 동적으로 쿼리 조건을 구성합니다.
            match_props = []
            params = {}
            
            if action_type:
                match_props.append("type: $act_type")
                params['act_type'] = action_type
            
            if target:
                match_props.append("target: $target")
                params['target'] = str(target)
                
            # 검색 조건이 없으면 기본값 반환
            if not match_props:
                return 0.5
                
            # Cypher 속성 매칭 문자열 생성 (예: "{type: $act_type, target: $target}")
            props_str = "{" + ", ".join(match_props) + "}"
            
            # 최신 5개 에피소드 조회 쿼리
            query = f"""
            MATCH (e:Episode)-[:EXECUTED]->(a:Action {props_str})
            RETURN e.result
            ORDER BY e.timestamp DESC
            LIMIT 5
            """
            
            res = self.graph.query(query, params)
            
            if not res.result_set: return 0.5
            
            # 'success' 개수 계산
            valid_results = [r[0] for r in res.result_set] # 결과 리스트 추출
            if not valid_results: return 0.5

            success_count = valid_results.count('success')
            return success_count / len(valid_results)
            
        except Exception as e:
            logging.error(f"[Memory] 쿼리 오류: {e}")
            return 0.5

# 싱글톤 인스턴스 생성
memory_manager = FalkorDBManager()
