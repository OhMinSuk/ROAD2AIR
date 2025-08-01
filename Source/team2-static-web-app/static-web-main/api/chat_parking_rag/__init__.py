import azure.functions as func
import logging
import json
import os
from openai import AzureOpenAI
from azure.cosmos import CosmosClient
from datetime import datetime, timezone
import pytz
import re

# 환경 변수 로드
AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_API_KEY = os.environ["AZURE_OPENAI_API_KEY"]
AZURE_OPENAI_DEPLOYMENT = os.environ["AZURE_OPENAI_DEPLOYMENT"]
OPENAI_API_VERSION = os.environ["OPENAI_API_VERSION"]
OPENAI_GPT_MODEL = os.environ["OPENAI_GPT_MODEL"]

COSMOS_ENDPOINT = os.environ["COSMOS_DB_ENDPOINT"]
COSMOS_KEY = os.environ["COSMOS_DB_KEY"]
COSMOS_DB = os.environ["COSMOS_DB_NAME"]
COSMOS_PARKING_CONTAINER = os.environ["COSMOS_DB_CONTAINER"]  # 주차장 컨테이너
COSMOS_FACILITY_CONTAINER = os.environ["COSMOS_FACILITY_CONTAINER"] # 시설 컨테이너
COSMOS_FLIGHT_CONTAINER = os.environ["COSMOS_FLIGHT_CONTAINER"]  # 항공편 컨테이너

APPLICATION_JSON = "application/json"

# 클라이언트 초기화
openai_client = AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    api_version=OPENAI_API_VERSION
)

cosmos_client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
db_client = cosmos_client.get_database_client(COSMOS_DB)
parking_container = db_client.get_container_client(COSMOS_PARKING_CONTAINER)
facility_container = db_client.get_container_client(COSMOS_FACILITY_CONTAINER)
flight_container = db_client.get_container_client(COSMOS_FLIGHT_CONTAINER)

# 항공편 번호 추출 함수 추가
def extract_flight_number(text):
    """텍스트에서 항공편 번호 추출"""
    # 항공편 번호 패턴: 영문 2-3자리 + 숫자 3-4자리
    flight_patterns = [
        r'\b[A-Z]{2}[0-9]{3,4}\b',  # KE123, AF5369
        r'\b[0-9][A-Z][0-9]{3,4}\b',  # 7C1301
        r'\b[A-Z][0-9][A-Z][0-9]{3,4}\b'  # 특수 패턴
    ]
    
    for pattern in flight_patterns:
        matches = re.findall(pattern, text.upper())
        if matches:
            return matches[0]
    
    return None

# 현재 시간 및 시간 관련 함수들
def get_current_time_info():
    """현재 한국 시간 정보 반환"""
    kst = pytz.timezone("Asia/Seoul")
    current_datetime = datetime.now(timezone.utc).astimezone(kst)
    
    return {
        "datetime": current_datetime,
        "date": current_datetime.strftime("%Y년 %m월 %d일"),
        "time": current_datetime.strftime("%H:%M"),
        "weekday": current_datetime.strftime("%A"),
        "weekday_ko": ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"][current_datetime.weekday()],
        "formatted": current_datetime.strftime("%Y년 %m월 %d일 %H:%M (%A)")
    }

def parse_flight_time(flight_data):
    """항공편 시간 정보를 파싱하여 datetime 객체로 변환"""
    try:
        if not flight_data:
            return None
            
        # 날짜와 시간 정보 추출
        date_str = str(flight_data.get('date', ''))
        scheduled_time = flight_data.get('scheduleDateTime', '')
        estimated_time = flight_data.get('estimatedDateTime', '')
        
        if not date_str or not scheduled_time:
            return None
            
        # 날짜 파싱 (YYYYMMDD 형태)
        if len(date_str) == 8:
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
        else:
            return None
            
        # 시간 파싱 (HH:MM 형태)
        time_to_use = estimated_time if estimated_time else scheduled_time
        if ':' in time_to_use:
            hour, minute = map(int, time_to_use.split(':'))
        else:
            return None
            
        # 한국 시간으로 datetime 객체 생성
        kst = pytz.timezone("Asia/Seoul")
        flight_datetime = datetime(year, month, day, hour, minute, tzinfo=kst)
        
        return flight_datetime
        
    except Exception as e:
        logging.error(f"항공편 시간 파싱 오류: {str(e)}")
        return None

def get_flight_recommendations(current_time, flight_data):
    """현재 시간과 항공편 시간을 비교하여 추천사항 제공"""
    try:
        recommendations = []
        
        for flight in flight_data[:3]:  # 최대 3개 항공편 분석
            flight_datetime = parse_flight_time(flight)
            if not flight_datetime:
                continue
                
            # 시간 차이 계산
            time_diff = flight_datetime - current_time['datetime']
            hours_diff = time_diff.total_seconds() / 3600
            
            flight_info = f"{flight.get('airline', '')} {flight.get('flightid', '')} ({flight.get('airport', '')})"
            
            if hours_diff < 0:
                # 이미 출발한 항공편
                recommendations.append(f"⚠️ {flight_info}는 이미 출발했습니다.")
            elif hours_diff <= 1:
                # 1시간 이내 출발
                recommendations.append(f"🚨 {flight_info}가 1시간 이내 출발합니다!\n   → 즉시 보안검색대로 이동하세요.")
            elif hours_diff <= 2:
                # 2시간 이내 출발
                recommendations.append(f"⏰ {flight_info}가 2시간 이내 출발합니다.\n   → 체크인 완료 후 보안검색대 통과를 권장합니다.")
            elif hours_diff <= 4:
                # 4시간 이내 출발
                recommendations.append(f"✅ {flight_info}까지 {int(hours_diff)}시간 여유가 있습니다.\n   → 식사, 쇼핑, 면세점 이용 가능합니다.")
            else:
                # 4시간 이상 여유
                recommendations.append(f"😊 {flight_info}까지 {int(hours_diff)}시간 이상 여유가 있습니다.\n   → 공항 시설을 충분히 이용하실 수 있습니다.")
                
        return recommendations
        
    except Exception as e:
        logging.error(f"항공편 추천 생성 오류: {str(e)}")
        return []

# 시설 상호명 추출 함수 추가
def extract_facility_names(user_query):
    """사용자 입력에서 시설 상호명 추출"""
    try:
        # 일반적인 상호명 패턴들
        common_brands = [
            # 도넛
            "크리스피크림", "크리스피 크림", "크리스피크림도넛", "던킨도너츠", "던킨", "미스터도넛",
            # 카페
            "스타벅스", "이디야", "투썸플레이스", "투썸", "엔젤인어스", "파스쿠찌", "할리스",
            # 패스트푸드
            "맥도날드", "버거킹", "KFC", "롯데리아", "맘스터치", "서브웨이",
            # 편의점
            "세븐일레븐", "GS25", "CU", "이마트24", "미니스톱",
            # 한식
            "백반집", "한정식", "김밥천국", "고봉민김밥", "죽이야기", "본죽",
            # 중식
            "홍콩반점", "북경", "중국집", "짜장면", "짬뽕",
            # 일식
            "초밥", "회", "라멘", "우동", "돈가스", "카츠", "텐동",
            # 기타
            "피자헛", "파파존스", "도미노피자", "배스킨라빈스", "베라", "하겐다즈",
            # 은행/환전
            "신한은행", "우리은행", "국민은행", "하나은행", "기업은행", "농협", "환전소",
            # 쇼핑
            "롯데면세점", "신라면세점", "현대면세점", "신세계면세점", "면세점"
        ]
        
        extracted_names = []
        query_upper = user_query.upper()
        
        # 브랜드명 매칭
        for brand in common_brands:
            if brand.upper() in query_upper:
                extracted_names.append(brand)
        
        # 입력 텍스트 자체도 상호명으로 추가 (공백 제거 버전도)
        query_cleaned = user_query.strip()
        if query_cleaned:
            extracted_names.append(query_cleaned)
            # 공백 제거 버전
            query_no_space = query_cleaned.replace(" ", "")
            if query_no_space != query_cleaned:
                extracted_names.append(query_no_space)
        
        # 중복 제거
        unique_names = list(set(extracted_names))
        
        logging.info(f"추출된 상호명들: {unique_names}")
        return unique_names
        
    except Exception as e:
        logging.error(f"상호명 추출 오류: {str(e)}")
        return [user_query.strip()]  # 오류시 원본 반환

# 질문 분류 함수 개선
def classify_question(user_query):
    """사용자 질문을 카테고리별로 분류 - 상호명 검색 개선"""
    # 먼저 항공편 번호 추출 시도
    flight_number = extract_flight_number(user_query)
    
    # 상호명 패턴 확인
    facility_keywords = [
        "크리스피크림", "던킨도너츠", "스타벅스", "맥도날드", "버거킹", "세븐일레븐",
        "위치", "어디", "찾아", "알려줘", "매장", "상호", "브랜드", "가게"
    ]
    
    has_facility_keyword = any(keyword in user_query for keyword in facility_keywords)
    
    messages = [
        {"role": "system", "content": """
            사용자의 질문을 다음 카테고리 중 하나로 분류하세요:
            
            1. "parking" - 주차장 관련 질문 (혼잡도, 잔여공간, 주차비 등)
            2. "facility" - 공항 시설 관련 질문 (환전소, 식당, 쇼핑, 편의시설, 특정 상호명 등)
            3. "flight" - 항공편 관련 질문 (출발/도착 시간, 게이트, 날씨, 항공사 등)
            4. "general" - 여행 준비물, 일반적인 공항 이용 팁 등
            5. "mixed" - 여러 카테고리가 섞인 복합 질문
            6. "time" - 현재 시간 관련 질문 ("지금 몇시", "현재 시간" 등)
            
            특별 규칙:
            - 항공편 번호(KE1234, 7C1301 등)가 있으면 "flight"
            - 특정 상호명(크리스피크림, 스타벅스 등)이 있으면 "facility"
            - "위치", "어디", "찾아", "알려줘" 등과 상호명이 함께 있으면 "facility"
            - "지금 몇시", "현재 시간" 등이 있으면 "time"
            
            JSON 형태로만 응답하세요:
            {"category": "분류결과", "confidence": 0.95}
        """},
        {"role": "user", "content": user_query}
    ]
    
    try:
        response = openai_client.chat.completions.create(
            model=OPENAI_GPT_MODEL,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # 추출된 항공편 번호가 있으면 추가
        if flight_number:
            result["flight_number"] = flight_number
            result["category"] = "flight"
        else:
            result["flight_number"] = None
            
        # 상호명 관련 키워드가 있으면 facility로 강제 분류
        if has_facility_keyword and result["category"] not in ["flight", "time"]:
            result["category"] = "facility"
            result["confidence"] = 0.9
            
        logging.info(f"질문 분류 결과: {result}")
        return result
        
    except Exception as e:
        logging.error(f"질문 분류 오류: {str(e)}")
        category = "facility" if has_facility_keyword else "general"
        return {
            "category": category, 
            "confidence": 0.5, 
            "flight_number": flight_number
        }

# 기존 주차장 관련 함수들
def get_entities(user_query):
    kst = pytz.timezone("Asia/Seoul")
    current_datetime = datetime.now(timezone.utc).astimezone(kst)
    base_date = current_datetime.strftime("%Y%m%d")
    current_hour = current_datetime.strftime("%H")
    
    extracted_keywords = []
    query_upper = user_query.upper()
    query_clean = user_query.replace(" ", "").upper()
    
    # 터미널 키워드 매칭 - 실제 데이터 구조에 맞게 수정
    terminal_patterns = [
        ("T1", ["T1", "터미널1", "1터미널", "제1터미널", "터미널 1", "1 터미널"]),
        ("T2", ["T2", "터미널2", "2터미널", "제2터미널", "터미널 2", "2 터미널"])
    ]
    
    for terminal_code, patterns in terminal_patterns:
        for pattern in patterns:
            if pattern.upper() in query_upper or pattern.replace(" ", "").upper() in query_clean:
                extracted_keywords.append(terminal_code)
                break
    
    # 주차장 유형 키워드 매칭 - 실제 데이터에 맞게 수정
    parking_type_patterns = [
        ("단기", ["단기", "단기주차", "단기주차장", "SHORT", "단기 주차"]),
        ("장기", ["장기", "장기주차", "장기주차장", "LONG", "장기 주차"])
    ]
    
    for parking_type, patterns in parking_type_patterns:
        for pattern in patterns:
            if pattern.upper() in query_upper or pattern.replace(" ", "").upper() in query_clean:
                extracted_keywords.append(parking_type)
                break
    
    # 층 정보 키워드 매칭 - 실제 데이터 구조에 맞게 수정
    import re
    
    # P1, P2, P3 등의 주차장 구역 매칭
    parking_area_matches = re.findall(r'P([0-9]+)', query_upper)
    for match in parking_area_matches:
        extracted_keywords.append(f"P{match}")
    
    # 지상/지하 층 정보 매칭
    floor_matches = re.findall(r'지상\s*([0-9]+)', user_query)
    for match in floor_matches:
        extracted_keywords.append(f"지상{match}층")
    
    floor_matches = re.findall(r'지하\s*([0-9]+)', user_query)
    for match in floor_matches:
        extracted_keywords.append(f"지하{match}층")
    
    # 일반 층수 매칭
    floor_matches = re.findall(r'([0-9]+)층', user_query)
    for match in floor_matches:
        extracted_keywords.append(f"{match}층")
    
    # 잔여/여유 관련 키워드 추가
    availability_keywords = ["잔여", "남은", "빈", "사용가능", "여유", "공간", "대수"]
    has_availability_query = any(keyword in user_query for keyword in availability_keywords)
    
    if has_availability_query:
        extracted_keywords.append("잔여공간")
    
    # 중복 제거
    extracted_keywords = list(set(extracted_keywords))
    
    result = {
        "floor_keywords": extracted_keywords,
        "date": base_date,
        "time": current_hour,
        "has_availability_query": has_availability_query
    }
    
    logging.info(f"키워드 추출 결과: {result}")
    return json.dumps(result)

def query_similar_parking_data(user_query, entities, top_k=15):
    """주차장 데이터 검색 - 실제 데이터 구조에 맞게 수정"""
    
    # 임베딩 생성
    embedding_res = openai_client.embeddings.create(
        input=user_query,
        model=AZURE_OPENAI_DEPLOYMENT
    )
    query_vector = embedding_res.data[0].embedding

    # 기본 벡터 검색
    base_query = f"""
    SELECT TOP {top_k * 2}
        c.floor, c.parking_count, c.parking_total,
        c.congestion_rate, c.congestion_level, c.date, c.time,
        VectorDistance(c.embedding, @query_vector) as similarity_score
    FROM c
    WHERE IS_DEFINED(c.embedding)
    ORDER BY VectorDistance(c.embedding, @query_vector)
    """
    
    parameters = [{"name": "@query_vector", "value": query_vector}]
    
    try:
        results = list(parking_container.query_items(
            query=base_query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        logging.info(f"벡터 검색 결과 수: {len(results)}")
        
        # 키워드 기반 필터링 및 점수 계산 - 실제 데이터 구조에 맞게 수정
        if entities and results:
            filtered_results = []
            floor_keywords = entities.get("floor_keywords", [])
            has_availability_query = entities.get("has_availability_query", False)
            
            logging.info(f"필터링 키워드: {floor_keywords}")
            
            for result in results:
                score = 0
                floor_text = result.get("floor", "").upper()
                
                # 실제 데이터 형태: "T1 장기 P3 주차장", "T2 단기 P1 주차장" 등
                for keyword in floor_keywords:
                    keyword_upper = keyword.upper()
                    
                    # 터미널 매칭
                    if keyword_upper in ["T1", "T2"]:
                        if floor_text.startswith(keyword_upper):
                            score += 10
                    
                    # 주차장 유형 매칭
                    elif keyword_upper in ["단기", "장기"]:
                        if keyword_upper in floor_text:
                            score += 8
                    
                    # 주차장 구역 매칭 (P1, P2, P3 등)
                    elif keyword_upper.startswith("P") and keyword_upper[1:].isdigit():
                        if keyword_upper in floor_text:
                            score += 7
                    
                    # 층 정보 매칭 (실제 데이터에 층 정보가 있는 경우)
                    elif "층" in keyword_upper:
                        if keyword_upper in floor_text:
                            score += 6
                    
                    # 일반 부분 매칭
                    elif keyword_upper in floor_text:
                        score += 5
                
                # 잔여 공간 질문에 대한 가중치
                if has_availability_query:
                    parking_total = result.get('parking_total', 0)
                    parking_count = result.get('parking_count', 0)
                    available_spaces = parking_total - parking_count
                    
                    if available_spaces > 0:
                        score += 3
                        # 잔여 공간 비율에 따른 추가 점수
                        availability_ratio = available_spaces / parking_total if parking_total > 0 else 0
                        score += int(availability_ratio * 5)
                
                # 날짜/시간 매칭
                try:
                    result_date = str(result.get("date", ""))
                    target_date = str(entities.get("date", ""))
                    if result_date == target_date:
                        score += 4
                except:
                    pass
                
                result["relevance_score"] = score
                filtered_results.append(result)
                
                logging.info(f"'{floor_text}' -> 점수: {score}")
            
            # 점수순 정렬
            filtered_results.sort(key=lambda x: (x["relevance_score"], -x["similarity_score"]), reverse=True)
            
            # 높은 점수 결과 우선 반환
            high_score_results = [r for r in filtered_results if r["relevance_score"] >= 8]
            if high_score_results:
                return high_score_results[:top_k]
            
            # 중간 점수 결과 반환
            medium_score_results = [r for r in filtered_results if r["relevance_score"] >= 5]
            if medium_score_results:
                return medium_score_results[:top_k]
            
            return filtered_results[:top_k]
        
        return results[:top_k]
        
    except Exception as e:
        logging.error(f"벡터 검색 오류: {str(e)}")
        return []
        
def direct_keyword_search(entities):
    """키워드 기반 직접 검색"""
    try:
        if not entities or not entities.get("floor_keywords"):
            return []
        
        floor_keywords = entities.get("floor_keywords", [])
        
        # 키워드별로 직접 검색
        all_results = []
        
        for keyword in floor_keywords:
            if keyword in ["T1", "T2", "단기주차장", "장기주차장", "지상층", "지하층"]:
                # 정확한 매칭을 위한 쿼리
                query = """
                SELECT TOP 10
                    c.floor, c.parking_count, c.parking_total,
                    c.congestion_rate, c.congestion_level, c.date, c.time
                FROM c
                WHERE CONTAINS(UPPER(c.floor), UPPER(@keyword))
                ORDER BY c.date DESC, c.time DESC
                """
                
                parameters = [{"name": "@keyword", "value": keyword}]
                
                try:
                    results = list(parking_container.query_items(
                        query=query,
                        parameters=parameters,
                        enable_cross_partition_query=True
                    ))
                    
                    all_results.extend(results)
                    logging.info(f"키워드 '{keyword}' 직접 검색 결과: {len(results)}개")
                    
                except Exception as e:
                    logging.error(f"키워드 '{keyword}' 검색 오류: {str(e)}")
                    continue
        
        # 중복 제거
        unique_results = []
        seen = set()
        for result in all_results:
            key = (result.get('floor', ''), result.get('date', ''), result.get('time', ''))
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        logging.info(f"직접 키워드 검색 최종 결과: {len(unique_results)}개")
        return unique_results[:10]
        
    except Exception as e:
        logging.error(f"직접 키워드 검색 전체 오류: {str(e)}")
        return []

def fallback_search(entities):
    try:
        where_clauses = []
        parameters = []
        
        if entities and entities.get("floor_keywords"):
            floor_conditions = []
            for i, keyword in enumerate(entities["floor_keywords"]):
                param_name = f"@floor_keyword_{i}"
                floor_conditions.append(f"CONTAINS(UPPER(c.floor), UPPER({param_name}))")
                parameters.append({"name": param_name, "value": keyword})
            
            if floor_conditions:
                where_clauses.append(f"({' OR '.join(floor_conditions)})")
        
        if entities and entities.get("date"):
            where_clauses.append("c.date = @date")
            parameters.append({"name": "@date", "value": int(entities["date"])})
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = f"""
        SELECT TOP 5
            c.floor, c.parking_count, c.parking_total,
            c.congestion_rate, c.congestion_level, c.date, c.time
        FROM c
        WHERE {where_sql}
        ORDER BY c.date DESC, c.time DESC
        """
        
        results = list(parking_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        logging.info(f"Fallback 검색 결과 수: {len(results)}")
        return results
        
    except Exception as e:
        logging.error(f"Fallback 검색 오류: {str(e)}")
        return []

# 시설 검색 함수들 - 대폭 개선된 버전
def search_exact_facility_name(user_query):
    """상호명 정확한 매칭 검색"""
    try:
        # 사용자 입력에서 상호명 추출
        facility_names = extract_facility_names(user_query)
        
        results = []
        for name in facility_names:
            # 정확한 매칭 쿼리
            exact_query = """
            SELECT TOP 10
                c.entrpskoreannm, c.trtmntprdlstkoreannm, c.lckoreannm,
                c.servicetime, c.arrordep, c.tel
            FROM c
            WHERE UPPER(c.entrpskoreannm) = UPPER(@facility_name)
            """
            
            parameters = [{"name": "@facility_name", "value": name}]
            
            exact_results = list(facility_container.query_items(
                query=exact_query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            results.extend(exact_results)
        
        return results
        
    except Exception as e:
        logging.error(f"정확한 상호명 검색 오류: {str(e)}")
        return []

def search_partial_facility_name(user_query):
    """상호명 부분 매칭 검색"""
    try:
        # 사용자 입력에서 상호명 추출
        facility_names = extract_facility_names(user_query)
        
        results = []
        for name in facility_names:
            # 부분 매칭 쿼리 (CONTAINS 사용)
            partial_query = """
            SELECT TOP 10
                c.entrpskoreannm, c.trtmntprdlstkoreannm, c.lckoreannm,
                c.servicetime, c.arrordep, c.tel
            FROM c
            WHERE CONTAINS(UPPER(c.entrpskoreannm), UPPER(@facility_name))
               OR CONTAINS(UPPER(c.trtmntprdlstkoreannm), UPPER(@facility_name))
            ORDER BY c.entrpskoreannm
            """
            
            parameters = [{"name": "@facility_name", "value": name}]
            
            partial_results = list(facility_container.query_items(
                query=partial_query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            results.extend(partial_results)
        
        # 중복 제거
        unique_results = []
        seen = set()
        for result in results:
            key = (result.get('entrpskoreannm', ''), result.get('lckoreannm', ''))
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        return unique_results
        
    except Exception as e:
        logging.error(f"부분 상호명 검색 오류: {str(e)}")
        return []

def search_facility_by_vector(user_query, top_k=10):
    """기존 벡터 검색 방식"""
    try:
        # 임베딩 생성
        embedding_res = openai_client.embeddings.create(
            input=user_query,
            model=AZURE_OPENAI_DEPLOYMENT
        )
        query_vector = embedding_res.data[0].embedding
        
        # 벡터 검색
        query = f"""
        SELECT TOP {top_k}
            c.entrpskoreannm, c.trtmntprdlstkoreannm, c.lckoreannm,
            c.servicetime, c.arrordep, c.tel,
            VectorDistance(c.embedding, @query_vector) as similarity_score
        FROM c
        WHERE IS_DEFINED(c.embedding)
        ORDER BY VectorDistance(c.embedding, @query_vector)
        """
        
        parameters = [{"name": "@query_vector", "value": query_vector}]
        
        results = list(facility_container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        
        return results
        
    except Exception as e:
        logging.error(f"벡터 검색 오류: {str(e)}")
        return []

# 시설 관련 함수들 대폭 개선 - 메인 함수
def query_facility_data(user_query, top_k=10):
    """공항 시설 정보 검색 - 상호명 직접 검색 기능 추가"""
    try:
        # 1단계: 상호명 직접 검색 (정확한 매칭)
        exact_results = search_exact_facility_name(user_query)
        if exact_results:
            logging.info(f"상호명 직접 검색 성공: {len(exact_results)}개")
            return exact_results
        
        # 2단계: 부분 매칭 검색
        partial_results = search_partial_facility_name(user_query)
        if partial_results:
            logging.info(f"부분 매칭 검색 성공: {len(partial_results)}개")
            return partial_results
        
        # 3단계: 기존 벡터 검색
        vector_results = search_facility_by_vector(user_query, top_k)
        if vector_results:
            logging.info(f"벡터 검색 성공: {len(vector_results)}개")
            return vector_results
        
        logging.info("모든 검색 방법 실패")
        return []
        
    except Exception as e:
        logging.error(f"시설 검색 전체 오류: {str(e)}")
        return []

# 항공편 관련 함수들 대폭 개선
def query_flight_data(user_query, flight_number=None, top_k=10):
    """항공편 정보 검색 - 개선된 버전"""
    try:
        # 항공편 번호가 있으면 우선 정확한 매칭 시도
        if flight_number:
            logging.info(f"항공편 번호로 검색 시도: {flight_number}")
            
            # 정확한 매칭 시도
            exact_query = """
            SELECT TOP 20
                c.date, c.hr, c.min, c.yoil, c.airline, c.flightid,
                c.scheduleDateTime, c.estimatedDateTime, c.airport, c.remark,
                c.gatenumber, c.temp, c.senstemp, c.himidity, c.wind
            FROM c
            WHERE UPPER(c.flightid) = UPPER(@flight_number)
            ORDER BY c.date DESC, c.hr DESC, c.min DESC
            """
            
            exact_params = [{"name": "@flight_number", "value": flight_number}]
            
            try:
                exact_results = list(flight_container.query_items(
                    query=exact_query,
                    parameters=exact_params,
                    enable_cross_partition_query=True
                ))
                
                logging.info(f"정확한 항공편 매칭 결과 수: {len(exact_results)}")
                
                if exact_results:
                    return exact_results
                else:
                    # 부분 매칭 시도
                    partial_query = """
                    SELECT TOP 20
                        c.date, c.hr, c.min, c.yoil, c.airline, c.flightid,
                        c.scheduleDateTime, c.estimatedDateTime, c.airport, c.remark,
                        c.gatenumber, c.temp, c.senstemp, c.himidity, c.wind
                    FROM c
                    WHERE CONTAINS(UPPER(c.flightid), UPPER(@flight_number))
                    ORDER BY c.date DESC, c.hr DESC, c.min DESC
                    """
                    
                    partial_results = list(flight_container.query_items(
                        query=partial_query,
                        parameters=exact_params,
                        enable_cross_partition_query=True
                    ))
                    
                    logging.info(f"부분 항공편 매칭 결과 수: {len(partial_results)}")
                    
                    if partial_results:
                        return partial_results
                    
            except Exception as e:
                logging.error(f"항공편 직접 검색 오류: {str(e)}")
        
        # 벡터 검색 시도
        logging.info("항공편 벡터 검색 시도")
        
        embedding_res = openai_client.embeddings.create(
            input=user_query,
            model=AZURE_OPENAI_DEPLOYMENT
        )
        query_vector = embedding_res.data[0].embedding
        
        vector_query = f"""
        SELECT TOP {top_k}
            c.date, c.hr, c.min, c.yoil, c.airline, c.flightid,
            c.scheduleDateTime, c.estimatedDateTime, c.airport, c.remark,
            c.gatenumber, c.temp, c.senstemp, c.himidity, c.wind,
            VectorDistance(c.embedding, @query_vector) as similarity_score
        FROM c
        WHERE IS_DEFINED(c.embedding)
        ORDER BY VectorDistance(c.embedding, @query_vector)
        """
        
        vector_params = [{"name": "@query_vector", "value": query_vector}]
        
        results = list(flight_container.query_items(
            query=vector_query,
            parameters=vector_params,
            enable_cross_partition_query=True
        ))
        
        logging.info(f"항공편 벡터 검색 결과 수: {len(results)}")
        return results
        
    except Exception as e:
        logging.error(f"항공편 검색 전체 오류: {str(e)}")
        return []

# 통합 응답 생성 함수 개선
def generate_comprehensive_response(user_query, category, flight_number=None):
    try:
        context_parts = []
        current_time = get_current_time_info()
        
        # 현재 시간 정보가 필요한 경우 (즉시 반환)
        if category == "time":
            context_parts.append(f"🕐 현재 시간: {current_time['formatted']}")
            return f"현재 시간은 {current_time['formatted']}입니다."
        
        # 기본적으로 현재 시간 정보 추가
        context_parts.append(f"🕐 현재 시간: {current_time['formatted']}")
        
        # 주차장 정보 처리
        if category in ["parking", "mixed"]:
            entities_str = get_entities(user_query)
            try:
                entities = json.loads(entities_str)
            except:
                entities = {}
            
            logging.info(f"주차장 검색 엔티티: {entities}")
            
            # 주차장 데이터 검색
            parking_data = query_similar_parking_data(user_query, entities, top_k=10)
            
            if parking_data:
                context_parts.append("🚗 주차장 현황 (실시간 데이터):")
                
                # 잔여 공간 질문인지 확인
                has_availability_query = entities.get("has_availability_query", False)
                availability_keywords = ["잔여", "남은", "빈", "사용가능", "여유", "공간", "대수"]
                is_availability_question = has_availability_query or any(keyword in user_query for keyword in availability_keywords)
                
                # 구체적인 주차장 검색인지 확인 (예: T2 단기주차장 지상 1층)
                floor_keywords = entities.get("floor_keywords", [])
                is_specific_parking_query = len(floor_keywords) >= 2  # 터미널 + 주차장 유형 등
                
                # 결과 표시 로직 개선
                displayed_results = []
                
                # 높은 점수 결과 우선 처리
                high_score_results = [r for r in parking_data if r.get("relevance_score", 0) >= 8]
                medium_score_results = [r for r in parking_data if r.get("relevance_score", 0) >= 5 and r.get("relevance_score", 0) < 8]
                
                # 구체적인 질문인 경우 정확한 매칭 결과만 표시
                if is_specific_parking_query and high_score_results:
                    displayed_results = high_score_results[:3]
                    logging.info(f"구체적 질문 - 고점수 결과 {len(displayed_results)}개 표시")
                elif medium_score_results:
                    displayed_results = medium_score_results[:5]
                    logging.info(f"일반 질문 - 중간점수 결과 {len(displayed_results)}개 표시")
                else:
                    displayed_results = parking_data[:5]
                    logging.info(f"기본 - 모든 결과 {len(displayed_results)}개 표시")
                
                # 매칭된 결과가 없는 경우 처리
                if not displayed_results:
                    context_parts.append("🚗 해당 조건의 주차장 정보를 찾을 수 없습니다.")
                    context_parts.append(f"검색 키워드: {floor_keywords}")
                    
                    # 대안 제시
                    if "T2" in floor_keywords:
                        context_parts.append("💡 T2 터미널의 다른 주차장을 찾아보시겠습니까?")
                    elif "T1" in floor_keywords:
                        context_parts.append("💡 T1 터미널의 다른 주차장을 찾아보시겠습니까?")
                else:
                    # 결과 표시
                    for i, item in enumerate(displayed_results, 1):
                        try:
                            parking_total = item.get('parking_total', 0)
                            parking_count = item.get('parking_count', 0)
                            available = parking_total - parking_count
                            usage_rate = (parking_count / parking_total * 100) if parking_total > 0 else 0
                            
                            floor_name = item.get('floor', '알 수 없음')
                            congestion_level = item.get('congestion_level', '알 수 없음')
                            congestion_rate = item.get('congestion_rate', 0)
                            
                            # 디버깅 정보 로깅
                            logging.info(f"주차장 {i}: {floor_name}, 전체:{parking_total}, 사용:{parking_count}, 잔여:{available}")
                            
                            # 잔여 공간 질문인 경우 더 상세한 정보 제공
                            if is_availability_question:
                                context_parts.append(
                                    f"{i}. 📍 {floor_name}\n"
                                    f"   • 잔여 공간: {available}대 (전체 {parking_total}대 중)\n"
                                    f"   • 사용률: {usage_rate:.1f}%\n"
                                    f"   • 혼잡도: {congestion_level} ({congestion_rate}%)\n"
                                    f"   • 업데이트: {item.get('date', '')}-{item.get('time', '')}"
                                )
                            else:
                                context_parts.append(
                                    f"{i}. {floor_name} - "
                                    f"혼잡도: {congestion_level}({congestion_rate}%), "
                                    f"잔여: {available}대/{parking_total}대"
                                )
                            
                            # 구체적인 질문에 대한 정확한 답변 제공
                            if is_specific_parking_query and i == 1:
                                if available > 0:
                                    context_parts.append(f"✅ 현재 {available}대의 주차 공간이 이용 가능합니다.")
                                else:
                                    context_parts.append(f"❌ 현재 주차 공간이 가득 찼습니다.")
                                    
                        except Exception as e:
                            logging.error(f"주차장 데이터 처리 오류: {str(e)}")
                            context_parts.append(f"{i}. 데이터 처리 오류: {item.get('floor', '알 수 없음')}")
                            continue
                    
                    # 요약 정보 추가
                    if is_availability_question and displayed_results:
                        try:
                            total_available = sum(
                                (item.get('parking_total', 0) - item.get('parking_count', 0)) 
                                for item in displayed_results
                            )
                            context_parts.append(f"\n💡 검색된 주차장 총 잔여 공간: {total_available}대")
                        except Exception as e:
                            logging.error(f"요약 정보 계산 오류: {str(e)}")
                    
                    # 추가 정보 제공
                    if is_specific_parking_query and displayed_results:
                        context_parts.append(f"\n📊 관련도 점수: {displayed_results[0].get('relevance_score', 0)}점")
                        
            else:
                context_parts.append("🚗 해당 조건의 주차장 정보를 찾을 수 없습니다.")
                context_parts.append(f"검색 키워드: {entities.get('floor_keywords', [])}")
                
                # 검색 실패 시 대안 제시
                if entities.get('floor_keywords'):
                    context_parts.append("💡 다른 검색어로 시도해보시거나, 전체 주차장 현황을 문의해보세요.")
        
        # 시설 정보 처리 - 더 많은 결과 표시
        if category in ["facility", "mixed", "general"]:
            facility_data = query_facility_data(user_query, top_k=15)
            if facility_data:
                context_parts.append("🏢 공항 시설 정보:")
                # 최대 8개까지 표시 (기존 3개에서 증가)
                for i, item in enumerate(facility_data[:8], 1):
                    location = item.get('lckoreannm', '')
                    service_time = item.get('servicetime', '')
                    tel = item.get('tel', '')
                    arrordep = item.get('arrordep', '')
                    
                    context_parts.append(
                        f"{i}. {item.get('entrpskoreannm', '')}\n"
                        f"   • 서비스: {item.get('trtmntprdlstkoreannm', '')}\n"
                        f"   • 위치: {location}\n"
                        f"   • 구분: {arrordep}\n"
                        f"   • 운영시간: {service_time}\n"
                        f"   • 연락처: {tel}"
                    )
        
        # 항공편 정보 처리
        flight_data = None
        if category in ["flight", "mixed"] or flight_number:
            flight_data = query_flight_data(user_query, flight_number)
            if flight_data:
                context_parts.append("✈️ 항공편 정보:")
                for i, item in enumerate(flight_data[:5], 1):
                    weather_info = ""
                    if item.get('temp'):
                        weather_info = f"날씨: {item['temp']}°C (체감 {item.get('senstemp', 'N/A')}°C), 습도: {item.get('himidity', 'N/A')}%"
                    
                    context_parts.append(
                        f"{i}. {item.get('airline', '')} {item.get('flightid', '')}\n"
                        f"   • 목적지: {item.get('airport', '')}\n"
                        f"   • 날짜: {item.get('date', '')} ({item.get('yoil', '')})\n"
                        f"   • 예정시간: {item.get('scheduleDateTime', '')}\n"
                        f"   • 예상시간: {item.get('estimatedDateTime', '')}\n"
                        f"   • 게이트: {item.get('gatenumber', '')}\n"
                        f"   • 구분: {item.get('remark', '')}\n"
                        f"   • {weather_info}"
                    )
                
                # 항공편 시간 기반 추천사항 생성
                recommendations = get_flight_recommendations(current_time, flight_data)
                if recommendations:
                    context_parts.append("\n💡 추천사항:")
                    for rec in recommendations:
                        context_parts.append(f"   {rec}")
            else:
                context_parts.append("✈️ 항공편 정보를 찾을 수 없습니다.")
                if flight_number:
                    context_parts.append(f"검색한 항공편 번호: {flight_number}")
        
        # 최종 응답 생성
        if not context_parts or len(context_parts) <= 1:  # 현재 시간 정보만 있는 경우
            context_parts.append("죄송합니다. 요청하신 정보를 찾을 수 없습니다.")
            context_parts.append("다른 질문을 해보시거나, 더 구체적인 정보를 제공해주세요.")
        
        # 컨텍스트 조합
        context = "\n".join(context_parts)
        
        # 주차장 질문에 대한 특별 처리
        parking_keywords = ['잔여', '남은', '빈', '사용 가능', '주차 가능', '여유', '공간']
        is_parking_availability_question = any(keyword in user_query for keyword in parking_keywords)
        
        # GPT 응답 생성
        system_prompt = """
        당신은 인천국제공항의 종합 안내 챗봇입니다.
        
        중요한 지침:
        1. 주차장 정보는 실시간 데이터베이스에서 가져온 정확한 정보입니다.
        2. 주차장 잔여 공간 질문에는 반드시 제공된 데이터를 기반으로 정확한 숫자를 제공하세요.
        3. "확인할 수 없습니다"라는 답변은 데이터가 없는 경우에만 사용하세요.
        4. 제공된 컨텍스트에 주차장 데이터가 있으면 반드시 활용하세요.
        5. 영어로 질문을 받았을 경우, 영어로 대답하세요.
        
        역할:
        1. 현재 시간 기준 정보 제공 (한국 시간 기준)
        2. 주차장 정보 (혼잡도, 잔여공간 등) 안내
        3. 공항 시설 (환전소, 식당, 편의시설 등) 안내 - 가능한 많은 옵션 제공
        4. 항공편 정보 (출발/도착 시간, 게이트, 날씨 등) 안내
        5. 항공편 시간 기반 맞춤형 추천사항 제공
        6. 여행 준비물 및 공항 이용 팁 제공
        
        응답 가이드라인:
        - 친절하고 도움이 되는 톤으로 답변
        - 구체적이고 실용적인 정보 제공
        - 이모지를 적절히 사용하여 가독성 향상
        - 사용자의 구체적인 상황을 고려한 맞춤형 답변
        - 시설 정보 요청시 가능한 많은 옵션 (최소 3개 이상 5개 이하)를 제공하여 선택의 폭을 넓혀주세요
        - 항공편 정보를 찾을 수 없는 경우 명확히 안내해주세요
        - 현재 시간과 항공편 시간을 비교하여 실용적인 조언을 제공하세요
        - 추가적인 팁이나 주의사항이 있으면 함께 제공
        - 질문이 공항 및 항공편과 거리가 먼 경우, 정중하게 관련없는 질문의 답변은 할 수 없다고 답변하세요.
        - 정보가 불확실하거나 확인할 수 없는 경우에는 추측하지 말고 "확인할 수 없습니다"라고 명확히 답변하세요.
        - 실시간 정보(항공편, 주차장, 환전소 운영 등)는 반드시 최신 데이터를 기반으로 응답하세요. 실시간 정보가 없으면 이를 명확히 고지하세요.
        - 질문을 외국어로 받았을 경우, 외국인일 경우가 높으니 해당 언어로 답변하세요.
        
        주차장 정보 특별 지침:
        - 주차장 데이터는 실시간으로 업데이트되는 정확한 정보입니다.
        - 잔여 공간, 잔여 대수 질문에는 제공된 숫자를 명확히 제시하세요.
        - "실시간 데이터가 필요합니다" 같은 답변은 하지 마세요.
        - 주차장 관련 질문: {is_parking_availability_question}
        
        특별 지침:
        - 현재 시간 질문에는 간단명료하게 답변하세요
        - 항공편 관련 질문에는 시간 비교를 통한 맞춤형 추천을 반드시 포함하세요
        - 긴급상황(1-2시간 이내 출발)에는 명확한 행동 지침을 제공하세요
        - 절대 정확하지 않은 정보는 제공하지 마세요
        - 다른 언어로 질문을 받았을 경우 해당 언어로 답변하세요
        - 영어로 질문을 받았을 경우, 영어로 대답하세요.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"질문: {user_query}\n\n관련 정보:\n{context}"}
        ]
        
        response = openai_client.chat.completions.create(
            model=OPENAI_GPT_MODEL,
            messages=messages,
            temperature=0.2,
            max_tokens=1500  # 토큰 수 증가
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logging.error(f"통합 응답 생성 오류: {str(e)}")
        return f"죄송합니다. 처리 중 오류가 발생했습니다: {str(e)}"

# 기존 주차장 전용 함수 (하위 호환성 유지)
def generate_parking_response(user_query):
    """주차장 전용 응답 생성 (기존 호환성 유지)"""
    return generate_comprehensive_response(user_query, "parking")

# Static Web App용 메인 함수
async def main(req: func.HttpRequest) -> func.HttpResponse:
    """Static Web App에서 호출되는 메인 함수"""
    
    # CORS 헤더 설정
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization"
    }
    
    try:
        # OPTIONS 요청 처리 (CORS preflight)
        if req.method == "OPTIONS":
            return func.HttpResponse(
                "",
                headers=headers,
                status_code=200
            )
        
        # POST 요청만 처리
        if req.method != "POST":
            return func.HttpResponse(
                json.dumps({"status": "error", "message": "POST 요청만 지원됩니다"}),
                mimetype=APPLICATION_JSON,
                headers=headers,
                status_code=405
            )
        
        # 요청 본문 파싱
        body = req.get_json()
        if not body or "question" not in body:
            return func.HttpResponse(
                json.dumps({"status": "error", "message": "질문을 입력해주세요"}),
                mimetype=APPLICATION_JSON,
                headers=headers,
                status_code=400
            )
        
        question = body.get("question", "").strip()
        if not question:
            return func.HttpResponse(
                json.dumps({"status": "error", "message": "질문이 비어있습니다"}),
                mimetype=APPLICATION_JSON,
                headers=headers,
                status_code=400
            )
        
        logging.info(f"질문 수신: {question}")
        
        # 질문 분류
        classification = classify_question(question)
        category = classification.get("category", "general")
        flight_number = classification.get("flight_number")
        
        logging.info(f"분류된 카테고리: {category}, 항공편 번호: {flight_number}")
        
        # 통합 응답 생성
        answer = generate_comprehensive_response(question, category, flight_number)
        
        return func.HttpResponse(
            json.dumps({
                "status": "success", 
                "answer": answer,
                "category": category,
                "flight_number": flight_number,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, ensure_ascii=False),
            mimetype=APPLICATION_JSON,
            headers=headers,
            status_code=200
        )

    except Exception as e:
        logging.error(f"전체 처리 오류: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "status": "error", 
                "message": "서버 오류가 발생했습니다",
                "error_detail": str(e)
            }),
            mimetype=APPLICATION_JSON,
            headers=headers,
            status_code=500
        )
