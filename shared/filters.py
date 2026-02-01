import numpy as np

class KalmanFilter:
    """
    물체의 위치나 상태의 노이즈를 제거하여 부드럽게 추적하는 필터입니다.
    YOLO 탐지 좌표의 깜빡임(Flickering)을 방지하는 데 사용됩니다.
    """

    def __init__(self, process_variance=1e-5, measurement_variance=1e-1**2):
        """
        필터의 초기 변수들을 설정합니다.
        
        Args:
            process_variance: 시스템 모델의 불확실성 (작을수록 예측을 신뢰)
            measurement_variance: 측정값의 노이즈 (클수록 이전 값을 더 신뢰)
        """
        # 예측 오차 공분산 초기화
        self.post_error_cov = 1.0
        # 현재 추정 상태 값 (X, Y, Z 등)
        self.state_estimate = 0.0
        
        self.process_var = process_variance
        self.measure_var = measurement_variance
        
        # 첫 측정값으로 초기화했는지 여부
        self.is_initialized = False

    def update(self, measurement):
        """
        새로운 측정값을 받아 필터링된 상태를 반환합니다.
        
        Args:
            measurement: 센서나 알고리즘(YOLO)으로부터 얻은 실제 측정값
        Returns:
            filter_result: 노이즈가 제거된 부드러운 좌표 값
        """
        # 1. 첫 측정 시 초기화
        if not self.is_initialized:
            self.state_estimate = measurement
            self.is_initialized = True
            return self.state_estimate

        # 2. 예측 단계 (Time Update)
        # 이전 상태가 그대로 유지된다고 가정함
        prior_estimate = self.state_estimate
        prior_error_cov = self.post_error_cov + self.process_var

        # 2. 보정 단계 (Measurement Update)
        # 칼만 이득(Kalman Gain) 계산: 측정값과 예측값 중 어디에 더 비중을 둘지 결정
        kalman_gain = prior_error_cov / (prior_error_cov + self.measure_var)
        
        # 새로운 상태 추정 (예측값 + 칼만 이득 * 오차)
        self.state_estimate = prior_estimate + kalman_gain * (measurement - prior_estimate)
        
        # 오차 공분산 업데이트
        self.post_error_cov = (1 - kalman_gain) * prior_error_cov

        return self.state_estimate

    def reset(self, initial_value=0.0):
        """필터의 상태를 초기화합니다."""
        self.state_estimate = initial_value
        self.post_error_cov = 1.0