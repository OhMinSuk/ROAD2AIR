import azure.functions as func
import logging
import json
import os

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Navigation function processed a request.')
    
    try:
        config = {
            "TMAP_API_KEY": os.environ.get("TMAP_API_KEY", ""),
            "KAKAO_JAVASCRIPT_KEY": os.environ.get("KAKAO_JAVASCRIPT_KEY", ""),
            "KAKAO_MAPS_REST_API": os.environ.get("KAKAO_MAPS_REST_API", ""),
            "OPENAI_API_VERSION": os.environ.get("OPENAI_API_VERSION", ""),
            "OPENAI_GPT_MODEL": os.environ.get("OPENAI_GPT_MODEL", "")
        }

        return func.HttpResponse(
            json.dumps(config, ensure_ascii=False),
            status_code=200,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            }
        )

    except Exception as e:
        logging.error(f"Navigation error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Navigation service error"}, ensure_ascii=False),
            status_code=500,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Access-Control-Allow-Origin": "*"
            }
        )