import logging
import os
import azure.functions as func
from azure.cosmos import CosmosClient
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential

app = func.FunctionApp()  # ✅ 반드시 전역에 선언

# ✅ 주차데이터 + 공항시설 + 항공편 임베딩

def get_cosmos_container(container_name=None):
    try:
        cosmos_client = CosmosClient(os.environ["COSMOS_DB_ENDPOINT"], os.environ["COSMOS_DB_KEY"])
        cosmos_db = cosmos_client.get_database_client(os.environ["COSMOS_DB_NAME"])
        
        # 컨테이너명이 지정되지 않으면 기본 주차장 컨테이너 사용
        if container_name is None:
            container_name = os.environ["COSMOS_DB_CONTAINER"]
            
        return cosmos_db.get_container_client(container_name)
    except Exception as e:
        logging.error(f"Cosmos DB 연결 오류: {e}")
        raise

def get_openai_client():
    try:
        return AzureOpenAI(
            api_version="2024-12-01-preview",
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"]
        )
    except Exception as e:
        logging.error(f"OpenAI 클라이언트 초기화 오류: {e}")
        raise

def get_embedding(text: str):
    try:
        openai_client = get_openai_client()
        response = openai_client.embeddings.create(
            input=[text],
            model=os.environ["AZURE_OPENAI_DEPLOYMENT"]
        )
        return response.data[0].embedding
    except Exception as e:
        logging.error(f"임베딩 생성 오류: {e}")
        raise

def process_parking_document(doc_dict):
    """주차장 데이터 임베딩 처리"""
    try:
        doc_id = doc_dict.get('id', 'unknown')
        logging.info(f"📄 주차장 데이터 처리 중: {doc_id}")
        
        # 이미 embedding이 있는 경우 스킵
        if 'embedding' in doc_dict:
            logging.info(f"⏭️ 문서 {doc_id}는 이미 임베딩이 있습니다.")
            return False
        
        # 임베딩할 내용 생성
        floor = doc_dict.get('floor', '')
        congestion_level = doc_dict.get('congestion_level', '')
        parking_count = doc_dict.get('parking_count', 0)
        parking_total = doc_dict.get('parking_total', 0)
        congestion_rate = doc_dict.get('congestion_rate', 0)
        
        content = f"주차장: {floor}, 혼잡도: {congestion_level}, 주차가능: {parking_count}대, 전체: {parking_total}대, 혼잡률: {congestion_rate}%"
        
        if not content.strip() or content.strip() == "주차장: , 혼잡도: , 주차가능: 0대, 전체: 0대, 혼잡률: 0%":
            logging.warning(f"⚠️ 문서 {doc_id}에 임베딩할 내용이 없습니다.")
            return False
        
        logging.info(f"🔄 주차장 임베딩 생성 중: {content}")
        embedding = get_embedding(content)
        
        # 문서 업데이트
        doc_dict['embedding'] = embedding
        doc_dict['content_type'] = 'parking'  # 데이터 타입 구분
        
        return True
        
    except Exception as e:
        logging.error(f"❌ 주차장 문서 처리 오류: {str(e)}")
        return False

def process_facility_document(doc_dict):
    """공항시설 데이터 임베딩 처리"""
    try:
        doc_id = doc_dict.get('id', 'unknown')
        logging.info(f"📄 공항시설 데이터 처리 중: {doc_id}")
        
        # 이미 embedding이 있는 경우 스킵
        if 'embedding' in doc_dict:
            logging.info(f"⏭️ 문서 {doc_id}는 이미 임베딩이 있습니다.")
            return False
        
        # 임베딩할 내용 생성
        entrpskoreannm = doc_dict.get('entrpskoreannm', '')  # 업체명
        trtmntprdlstkoreannm = doc_dict.get('trtmntprdlstkoreannm', '')  # 취급상품
        lckoreannm = doc_dict.get('lckoreannm', '')  # 위치
        servicetime = doc_dict.get('servicetime', '')  # 서비스시간
        arrordep = doc_dict.get('arrordep', '')  # 출국장/입국장
        tel = doc_dict.get('tel', '')  # 전화번호
        
        content = f"시설명: {entrpskoreannm}, 상품/서비스: {trtmntprdlstkoreannm}, 위치: {lckoreannm}, 운영시간: {servicetime}, 구역: {arrordep}, 전화번호: {tel}"
        
        if not content.strip() or content.strip() == "시설명: , 상품/서비스: , 위치: , 운영시간: , 구역: , 전화번호: ":
            logging.warning(f"⚠️ 문서 {doc_id}에 임베딩할 내용이 없습니다.")
            return False
        
        logging.info(f"🔄 공항시설 임베딩 생성 중: {content}")
        embedding = get_embedding(content)
        
        # 문서 업데이트
        doc_dict['embedding'] = embedding
        doc_dict['content_type'] = 'facility'  # 데이터 타입 구분
        
        return True
        
    except Exception as e:
        logging.error(f"❌ 공항시설 문서 처리 오류: {str(e)}")
        return False

def process_flight_document(doc_dict):
    """항공편 데이터 임베딩 처리"""
    try:
        doc_id = doc_dict.get('id', 'unknown')
        logging.info(f"📄 항공편 데이터 처리 중: {doc_id}")
        
        # 이미 embedding이 있는 경우 스킵
        if 'embedding' in doc_dict:
            logging.info(f"⏭️ 문서 {doc_id}는 이미 임베딩이 있습니다.")
            return False
        
        # 임베딩할 내용 생성
        airline = doc_dict.get('airline', '')  # 항공사
        flightid = doc_dict.get('flightid', '')  # 항공편 번호
        airport = doc_dict.get('airport', '')  # 공항
        scheduleDateTime = doc_dict.get('scheduleDateTime', '')  # 예정시간
        estimatedDateTime = doc_dict.get('estimatedDateTime', '')  # 실제시간
        remark = doc_dict.get('remark', '')  # 출발/도착
        gatenumber = doc_dict.get('gatenumber', '')  # 게이트 번호
        date = doc_dict.get('date', '')  # 날짜
        yoil = doc_dict.get('yoil', '')  # 요일
        
        # 시간 포맷 변환 (0720 -> 07:20)
        schedule_time = f"{scheduleDateTime[:2]}:{scheduleDateTime[2:]}" if scheduleDateTime and len(scheduleDateTime) == 4 else scheduleDateTime
        estimated_time = f"{estimatedDateTime[:2]}:{estimatedDateTime[2:]}" if estimatedDateTime and len(estimatedDateTime) == 4 else estimatedDateTime
        
        content = f"항공편: {airline} {flightid}, 목적지: {airport}, 예정시간: {schedule_time}, 실제시간: {estimated_time}, 구분: {remark}, 게이트: {gatenumber}번, 날짜: {date}, 요일: {yoil}"
        
        if not content.strip() or flightid == '':
            logging.warning(f"⚠️ 문서 {doc_id}에 임베딩할 내용이 없습니다.")
            return False
        
        logging.info(f"🔄 항공편 임베딩 생성 중: {content}")
        embedding = get_embedding(content)
        
        # 문서 업데이트
        doc_dict['embedding'] = embedding
        doc_dict['content_type'] = 'flight'  # 데이터 타입 구분
        
        return True
        
    except Exception as e:
        logging.error(f"❌ 항공편 문서 처리 오류: {str(e)}")
        return False

# 주차장 데이터 Change Feed 트리거
@app.function_name(name="Parking_CosmosDBChangeFeedTrigger")
@app.cosmos_db_trigger(
    arg_name="documents",
    database_name="%COSMOS_DB_NAME%",
    container_name="%COSMOS_DB_CONTAINER%",
    connection="COSMOS_DB_CONNECTION_STRING",
    lease_container_name="leases",
    create_lease_container_if_not_exists=True,
    start_from_beginning=False,
    preferred_locations=None
)
def parking_cosmos_trigger(documents: func.DocumentList):
    logging.info(f"🔥 주차장 Change Feed 트리거 호출됨! 문서 수: {len(documents)}")
    
    if not documents:
        logging.info("변경된 주차장 문서가 없습니다.")
        return
    
    try:
        cosmos_container = get_cosmos_container()
        
        for doc in documents:
            try:
                doc_dict = dict(doc)
                doc_id = doc_dict.get('id', 'unknown')
                
                if process_parking_document(doc_dict):
                    cosmos_container.upsert_item(doc_dict)
                    logging.info(f"✅ 주차장 임베딩 완료 및 업데이트: {doc_id}")
                
            except Exception as e:
                logging.error(f"❌ 주차장 문서 {doc_dict.get('id', 'unknown')} 처리 오류: {str(e)}")
                continue
                
    except Exception as e:
        logging.error(f"❌ 주차장 Change Feed 처리 전체 오류: {str(e)}")
        raise

# 공항시설 데이터 Change Feed 트리거
@app.function_name(name="Facility_CosmosDBChangeFeedTrigger")
@app.cosmos_db_trigger(
    arg_name="documents",
    database_name="%COSMOS_DB_NAME%",
    container_name="%COSMOS_DB_FACILITY_CONTAINER%",  # 공항시설 컨테이너
    connection="COSMOS_DB_CONNECTION_STRING",
    lease_container_name="facility_leases",  # 별도의 리스 컨테이너
    create_lease_container_if_not_exists=True,
    start_from_beginning=False,
    preferred_locations=None
)
def facility_cosmos_trigger(documents: func.DocumentList):
    logging.info(f"🔥 공항시설 Change Feed 트리거 호출됨! 문서 수: {len(documents)}")
    
    if not documents:
        logging.info("변경된 공항시설 문서가 없습니다.")
        return
    
    try:
        cosmos_container = get_cosmos_container(os.environ["COSMOS_DB_FACILITY_CONTAINER"])
        
        for doc in documents:
            try:
                doc_dict = dict(doc)
                doc_id = doc_dict.get('id', 'unknown')
                
                if process_facility_document(doc_dict):
                    cosmos_container.upsert_item(doc_dict)
                    logging.info(f"✅ 공항시설 임베딩 완료 및 업데이트: {doc_id}")
                
            except Exception as e:
                logging.error(f"❌ 공항시설 문서 {doc_dict.get('id', 'unknown')} 처리 오류: {str(e)}")
                continue
                
    except Exception as e:
        logging.error(f"❌ 공항시설 Change Feed 처리 전체 오류: {str(e)}")
        raise

# 항공편 데이터 Change Feed 트리거
@app.function_name(name="Flight_CosmosDBChangeFeedTrigger")
@app.cosmos_db_trigger(
    arg_name="documents",
    database_name="%COSMOS_DB_NAME%",
    container_name="%COSMOS_DB_FLIGHT_CONTAINER%",  # 항공편 컨테이너
    connection="COSMOS_DB_CONNECTION_STRING",
    lease_container_name="flight_leases",  # 별도의 리스 컨테이너
    create_lease_container_if_not_exists=True,
    start_from_beginning=False,
    preferred_locations=None
)
def flight_cosmos_trigger(documents: func.DocumentList):
    logging.info(f"🔥 항공편 Change Feed 트리거 호출됨! 문서 수: {len(documents)}")
    
    if not documents:
        logging.info("변경된 항공편 문서가 없습니다.")
        return
    
    try:
        cosmos_container = get_cosmos_container(os.environ["COSMOS_DB_FLIGHT_CONTAINER"])
        
        for doc in documents:
            try:
                doc_dict = dict(doc)
                doc_id = doc_dict.get('id', 'unknown')
                
                if process_flight_document(doc_dict):
                    cosmos_container.upsert_item(doc_dict)
                    logging.info(f"✅ 항공편 임베딩 완료 및 업데이트: {doc_id}")
                
            except Exception as e:
                logging.error(f"❌ 항공편 문서 {doc_dict.get('id', 'unknown')} 처리 오류: {str(e)}")
                continue
                
    except Exception as e:
        logging.error(f"❌ 항공편 Change Feed 처리 전체 오류: {str(e)}")
        raise

# 테스트용 HTTP 트리거
@app.function_name(name="TestChangeFeed")
@app.route(route="test-changefeed", methods=["GET"])
def test_changefeed(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("🧪 Change Feed 테스트 시작")
    
    try:
        # 환경 변수 확인
        required_vars = [
            "COSMOS_DB_ENDPOINT", "COSMOS_DB_KEY", "COSMOS_DB_NAME", 
            "COSMOS_DB_CONTAINER", "COSMOS_DB_FACILITY_CONTAINER", "COSMOS_DB_FLIGHT_CONTAINER", 
            "COSMOS_DB_CONNECTION_STRING", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", 
            "AZURE_OPENAI_DEPLOYMENT"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            return func.HttpResponse(
                f"❌ 누락된 환경 변수: {', '.join(missing_vars)}",
                status_code=400
            )
        
        # 주차장 Cosmos DB 연결 테스트
        parking_container = get_cosmos_container()
        logging.info("✅ 주차장 Cosmos DB 연결 성공")
        
        # 공항시설 Cosmos DB 연결 테스트
        facility_container = get_cosmos_container(os.environ["COSMOS_DB_FACILITY_CONTAINER"])
        logging.info("✅ 공항시설 Cosmos DB 연결 성공")
        
        # 항공편 Cosmos DB 연결 테스트
        flight_container = get_cosmos_container(os.environ["COSMOS_DB_FLIGHT_CONTAINER"])
        logging.info("✅ 항공편 Cosmos DB 연결 성공")
        
        # OpenAI 연결 테스트
        openai_client = get_openai_client()
        test_embedding = get_embedding("테스트")
        logging.info("✅ OpenAI 연결 및 임베딩 성공")
        
        return func.HttpResponse(
            "✅ 모든 연결 테스트 성공! 주차장, 공항시설, 항공편 Change Feed가 정상 작동할 것입니다.",
            status_code=200
        )
        
    except Exception as e:
        logging.error(f"❌ 테스트 오류: {str(e)}")
        return func.HttpResponse(
            f"❌ 테스트 실패: {str(e)}",
            status_code=500
        )