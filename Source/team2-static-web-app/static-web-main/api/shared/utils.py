"""
공통 유틸리티 함수들
"""
import math
from datetime import datetime
from typing import Tuple, Dict, Any

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    하버사인 공식을 사용하여 두 지점 간의 거리를 계산합니다.
    
    Args:
        lat1, lon1: 첫 번째 지점의 위도, 경도
        lat2, lon2: 두 번째 지점의 위도, 경도
    
    Returns:
        거리 (킬로미터)
    """
    R = 6371  # 지구 반지름 (km)
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def calculate_walking_time(distance_km: float, walking_speed_kmh: float = 5) -> int:
    """
    도보 시간을 계산합니다.
    
    Args:
        distance_km: 거리 (킬로미터)
        walking_speed_kmh: 걸음 속도 (km/h, 기본값 5)
    
    Returns:
        도보 시간 (분)
    """
    time_hours = distance_km / walking_speed_kmh
    return max(1, int(time_hours * 60))

def get_cors_headers() -> Dict[str, str]:
    """
    CORS 헤더를 반환합니다.
    """
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Content-Type': 'application/json'
    }

def validate_coordinates(lat: float, lng: float) -> bool:
    """
    좌표의 유효성을 검사합니다.
    
    Args:
        lat: 위도
        lng: 경도
    
    Returns:
        유효하면 True, 그렇지 않으면 False
    """
    return (-90 <= lat <= 90) and (-180 <= lng <= 180)

def format_response(success: bool, data: Any = None, error: str = None) -> Dict[str, Any]:
    """
    API 응답을 표준화합니다.
    
    Args:
        success: 성공 여부
        data: 응답 데이터
        error: 오류 메시지
    
    Returns:
        표준화된 응답 딕셔너리
    """
    response = {
        'success': success,
        'timestamp': datetime.now().isoformat()
    }
    
    if success and data is not None:
        response['data'] = data
    elif not success and error:
        response['error'] = error
    
    return response