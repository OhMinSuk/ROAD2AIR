import logging
import os
import json
import azure.functions as func
from azure.cosmos import CosmosClient, exceptions
from datetime import datetime, timedelta

# Azure Portal의 애플리케이션 설정에서 환경 변수 가져오기
COSMOS_DB_ENDPOINT = os.environ.get('COSMOS_DB_ENDPOINT')
COSMOS_DB_KEY = os.environ.get('COSMOS_DB_KEY')
COSMOS_DB_DATABASE_NAME = os.environ.get('COSMOS_DB_NAME')
COSMOS_DB_CONTAINER_NAME = os.environ.get('COSMOS_DB_CONTAINER_NAME')

# 지연 관련 키워드 (소문자로 통일하여 검색)
DELAY_KEYWORDS_LOWER = ["지연", "연착", "취소", "결항", "변경", "지체"]

def get_cosmos_container():
    env_vars = {
        'COSMOS_DB_ENDPOINT': COSMOS_DB_ENDPOINT,
        'COSMOS_DB_KEY': COSMOS_DB_KEY,
        'COSMOS_DB_DATABASE_NAME': COSMOS_DB_DATABASE_NAME,
        'COSMOS_DB_CONTAINER_NAME': COSMOS_DB_CONTAINER_NAME
    }
    
    missing_vars = [k for k, v in env_vars.items() if not v]
    if missing_vars:
        logging.error(f"Missing environment variables: {missing_vars}")
        return None

    try:
        client = CosmosClient(COSMOS_DB_ENDPOINT, COSMOS_DB_KEY)
        database = client.get_database_client(COSMOS_DB_DATABASE_NAME)
        container = database.get_container_client(COSMOS_DB_CONTAINER_NAME)
        
        # 연결 테스트 (실제 데이터를 읽어올 필요는 없음)
        # container.read() # 이 부분은 컨테이너가 존재하지 않을 때만 오류 발생
        logging.info("Successfully attempted to connect to Cosmos DB container.")
        return container
        
    except exceptions.CosmosHttpResponseError as e:
        logging.error(f"Cosmos DB HTTP error during connection test: {e.message} (Status: {e.status_code})")
        return None
    except Exception as e:
        logging.error(f"Failed to initialize Cosmos DB client or connect: {str(e)}")
        return None

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing flight data request')

    try:
        container = get_cosmos_container()
        if not container:
            return func.HttpResponse(
                json.dumps({
                    "error": "Database connection failed", 
                    "message": "Unable to connect to Cosmos DB or retrieve container."
                }, ensure_ascii=False),
                mimetype="application/json",
                status_code=500
            )

        # 지연 항공편 조회
        items = [] # 기본값은 빈 리스트
        try:
            # 쿼리: 오늘 또는 미래의 eventDate를 가진 아이템만 가져옴
            # remark 필터링은 Cosmos DB에서 처리
            today = datetime.now().strftime('%Y%m%d')
            today_int = int(today)
            
            # DELAY_KEYWORDS_LOWER를 사용하여 쿼리 조건 동적 생성
            remark_conditions = " OR ".join([f"CONTAINS(LOWER(c.remark), \"{keyword}\")" for keyword in DELAY_KEYWORDS_LOWER])

            query = f"""
                SELECT DISTINCT
                    c.airline,
                    c.flightId,
                    c.scheduleTimeFormatted,
                    c.estimatedTimeFormatted,
                    c.destination,
                    c.remark,
                    c.gatenumber,
                    c.eventDate
                FROM c
                WHERE c.eventDate >= {today_int}
                AND ({remark_conditions})
                ORDER BY c.eventDate ASC
            """
            
            logging.info(f"Executing query for delayed flights: {query}")
            items = list(container.query_items(
                query=query, 
                enable_cross_partition_query=True
            ))
            logging.info(f"Found {len(items)} raw items from Cosmos DB.")

        except Exception as e:
            logging.error(f"Failed to query delayed flights from Cosmos DB: {str(e)}")
            # 쿼리 실패 시 items는 빈 리스트로 유지되어 다음 처리 단계로 넘어감

        # 시간 기반 파싱, 필터링 및 정렬
        final_output_items = [] # 최종 반환할 리스트
        
        # 한국 현재 시간 (정확한 필터링 기준)
        now_korea = datetime.now() + timedelta(hours=9) 
        
        # 오늘 날짜 (YYYYMMDD) 정수형
        today_korea_int = int(now_korea.strftime('%Y%m%d'))

        # 루프를 돌면서 파싱하고 필터링합니다.
        processed_and_filtered_items_for_sort = []
        
        for item in items:
            event_date_str = str(item.get("eventDate"))
            estimated_time_str = item.get("estimatedTimeFormatted")
            
            try:
                # 필수 필드 확인 및 유효성 검사 강화
                if (not all(key in item for key in ['eventDate', 'estimatedTimeFormatted']) or
                    len(event_date_str) != 8 or not estimated_time_str or ':' not in estimated_time_str):
                    
                    logging.warning(f"필수 필드 누락 또는 날짜/시간 형식 오류: {item.get('id', 'unknown')} (eventDate: {event_date_str}, estimatedTimeFormatted: {estimated_time_str}) - Skipping for sort.")
                    # 파싱/필터링 단계에서 유효하지 않은 데이터는 최종 출력에서 제외 (혹은 필요에 따라 포함)
                    # 여기서는 제외하여 깨끗한 정렬 결과만 만듭니다.
                    continue
                    
                # 날짜 시간 파싱 및 결합
                full_datetime_str = f"{event_date_str[:4]}-{event_date_str[4:6]}-{event_date_str[6:]} {estimated_time_str}"
                parsed_datetime = datetime.strptime(full_datetime_str, '%Y-%m-%d %H:%M')
                
                # --- 중요: 시간 기반 필터링 로직 ---
                # 1. eventDate가 오늘인 경우: estimatedTimeFormatted가 현재 시간(now_korea)보다 미래여야 함
                # 2. eventDate가 오늘보다 미래인 경우: 무조건 포함
                if (parsed_datetime.date() == now_korea.date() and parsed_datetime >= now_korea) or \
                   (parsed_datetime.date() > now_korea.date()):
                    
                    # 정렬을 위해 datetime 객체를 item에 추가
                    item['__sort_key_datetime'] = parsed_datetime 
                    
                    # YYYYMMDDHHMM 형식의 문자열 추가 (선택 사항)
                    item['combined_datetime_string'] = parsed_datetime.strftime('%Y%m%d%H%M')
                    
                    processed_and_filtered_items_for_sort.append(item)
                else:
                    # 오늘 날짜인데 이미 시간이 지난 항공편이거나, 과거 날짜의 항공편 (쿼리에서 걸러지지만 혹시 몰라)
                    logging.info(f"Filtered out past event: {item.get('id', 'unknown')} (eventDate: {event_date_str}, estimatedTimeFormatted: {estimated_time_str})")

            except ValueError as ve: # datetime.strptime 오류 처리
                logging.error(f"날짜/시간 파싱 오류 발생 (item: {item.get('id', 'unknown')}): {str(ve)}")
            except Exception as e: # 기타 예외 처리
                logging.error(f"아이템 처리 중 예상치 못한 오류 발생 (item: {item.get('id', 'unknown')}): {str(e)}")
        
        # --- 최종 정렬 ---
        # 필터링된 아이템만 정렬합니다.
        processed_and_filtered_items_for_sort.sort(key=lambda x: x['__sort_key_datetime'])

        # JSON 응답에 포함하기 전에 임시 정렬 키 제거
        for item in processed_and_filtered_items_for_sort:
            del item['__sort_key_datetime']

        # 최종 출력 리스트는 필터링되고 정렬된 아이템만 포함합니다.
        final_output_items = processed_and_filtered_items_for_sort

        ## 결과 반환
        logging.info(f"Returning {len(final_output_items)} processed, filtered, and sorted items.")
        
        return func.HttpResponse(
            json.dumps(final_output_items, ensure_ascii=False, default=str),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"메인 함수에서 예상치 못한 오류 발생: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }, ensure_ascii=False),
            mimetype="application/json",
            status_code=500
        )
