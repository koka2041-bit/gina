# API/code.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any

from models.request_models import CodeRequest, CodeResponse
from services.openrouter_service import openrouter_service
from utils.response_formatter import formatter

router = APIRouter()

@router.post("/code", response_model=Dict[str, Any])
async def generate_code(request: CodeRequest):
    """
    코드 생성 엔드포인트
    
    OpenRouter API를 사용하여 요구사항에 맞는 코드를 생성합니다.
    """
    try:
        # 입력 검증
        if not request.description or not request.description.strip():
            raise HTTPException(status_code=400, detail="코드 설명이 비어있습니다.")
        
        # 서비스 가용성 확인
        if not openrouter_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="OpenRouter 서비스를 사용할 수 없습니다. API 키를 확인해주세요."
            )
        
        # 코드 생성
        code_response = await openrouter_service.generate_code(request)
        
        # 응답 포맷팅
        formatted_response = formatter.format_code_response(
            code=code_response.code,
            language=code_response.language,
            explanation=code_response.explanation,
            complexity=code_response.complexity,
            processing_time=code_response.processing_time
        )
        
        return JSONResponse(content=formatted_response)
        
    except HTTPException:
        raise
    except Exception as e:
        error_response = formatter.format_error_response(
            error="코드 생성 실패",
            detail=str(e),
            error_code="CODE_GENERATION_ERROR"
        )
        return JSONResponse(content=error_response, status_code=500)

@router.get("/code/languages")
async def get_supported_languages():
    """지원되는 프로그래밍 언어 목록"""
    return {
        "languages": [
            {"value": "python", "name": "Python", "description": "데이터 분석, 웹 개발, AI/ML에 적합"},
            {"value": "javascript", "name": "JavaScript", "description": "웹 프론트엔드 및 Node.js 백엔드 개발"},
            {"value": "java", "name": "Java", "description": "엔터프라이즈 애플리케이션 및 안드로이드 개발"},
            {"value": "cpp", "name": "C++", "description": "시스템 프로그래밍 및 고성능 애플리케이션"},
            {"value": "csharp", "name": "C#", "description": ".NET 프레임워크 및 Windows 애플리케이션"},
            {"value": "html", "name": "HTML", "description": "웹 페이지 구조 및 마크업"},
            {"value": "css", "name": "CSS", "description": "웹 스타일링 및 레이아웃"},
            {"value": "sql", "name": "SQL", "description": "데이터베이스 쿼리 및 관리"},
            {"value": "bash", "name": "Bash", "description": "리눅스/유닉스 쉘 스크립팅"},
            {"value": "go", "name": "Go", "description": "클라우드 및 백엔드 서비스 개발"},
            {"value": "rust", "name": "Rust", "description": "시스템 프로그래밍 및 안전한 메모리 관리"}
        ]
    }

@router.get("/code/complexities")
async def get_complexity_levels():
    """지원되는 코드 복잡도 레벨"""
    return {
        "complexities": [
            {
                "value": "beginner",
                "name": "초보자",
                "description": "기본적인 문법과 간단한 로직, 상세한 주석 포함"
            },
            {
                "value": "intermediate", 
                "name": "중급자",
                "description": "효율적인 알고리즘과 구조화된 코드, 적절한 주석"
            },
            {
                "value": "advanced",
                "name": "고급자", 
                "description": "최적화된 성능과 고급 기술 활용, 핵심 주석만"
            }
        ]
    }

@router.post("/code/validate")
async def validate_code_request(request: CodeRequest):
    """
    코드 생성 요청 검증
    
    실제 생성 전에 요청이 유효한지 확인하고 예상 결과를 알려줍니다.
    """
    try:
        validation_result = {
            "valid": True,
            "warnings": [],
            "suggestions": [],
            "estimated_output": {}
        }
        
        # 언어별 특성 검증
        language_features = {
            "python": {"functions": True, "classes": True, "async": True},
            "javascript": {"functions": True, "classes": True, "async": True, "dom": True},
            "java": {"classes": True, "methods": True, "static": True},
            "cpp": {"functions": True, "classes": True, "pointers": True},
            "html": {"tags": True, "attributes": True, "semantic": True},
            "css": {"selectors": True, "properties": True, "responsive": True}
        }
        
        lang_features = language_features.get(request.language, {})
        
        # 복잡도별 예상 출력
        complexity_estimates = {
            "beginner": {
                "lines": "10-30줄",
                "features": "기본 문법 중심",
                "comments": "상세한 설명 주석"
            },
            "intermediate": {
                "lines": "30-80줄", 
                "features": "구조화된 코드",
                "comments": "핵심 기능 주석"
            },
            "advanced": {
                "lines": "50-150줄",
                "features": "최적화된 고급 기법",
                "comments": "필수 주석만"
            }
        }
        
        validation_result["estimated_output"] = complexity_estimates.get(
            request.complexity, complexity_estimates["intermediate"]
        )
        
        # 언어별 제안사항
        if request.language == "python" and "web" in request.description.lower():
            validation_result["suggestions"].append("Flask 또는 FastAPI 프레임워크 사용을 고려해보세요")
        
        if request.language == "javascript" and "api" in request.description.lower():
            validation_result["suggestions"].append("async/await 패턴 사용을 권장합니다")
        
        # 경고사항
        if request.max_tokens > 3000:
            validation_result["warnings"].append("토큰 수가 많으면 응답 시간이 오래 걸릴 수 있습니다")
        
        if request.temperature > 0.8:
            validation_result["warnings"].append("높은 temperature는 예측하기 어려운 코드를 생성할 수 있습니다")
        
        return JSONResponse(content=validation_result)
        
    except Exception as e:
        error_response = formatter.format_error_response(
            error="코드 요청 검증 실패",
            detail=str(e),
            error_code="CODE_VALIDATION_ERROR"
        )
        return JSONResponse(content=error_response, status_code=500)

@router.post("/code/explain")
async def explain_code(code: str, language: str = "python"):
    """
    제공된 코드의 기능을 설명합니다.
    """
    try:
        if not code.strip():
            raise HTTPException(status_code=400, detail="분석할 코드가 비어있습니다.")
        
        if not openrouter_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="OpenRouter 서비스를 사용할 수 없습니다."
            )
        
        # 코드 설명 요청
        explanation_prompt = f"""
다음 {language} 코드를 분석하고 설명해주세요:

```{language}
{code}
```

다음 항목들을 포함해서 설명해주세요:
1. 코드의 전반적인 기능
2. 주요 함수/메서드의 역할
3. 입력과 출력
4. 사용된 주요 개념이나 알고리즘
5. 개선할 점이 있다면 제안
"""
        
        explanation = await openrouter_service.generate_chat_response(explanation_prompt)
        
        # 코드 메트릭 계산
        lines = code.strip().split('\n')
        metrics = {
            "total_lines": len(lines),
            "non_empty_lines": len([line for line in lines if line.strip()]),
            "estimated_complexity": "보통",
            "language": language
        }
        
        return JSONResponse(content={
            "explanation": explanation,
            "metrics": metrics,
            "timestamp": formatter._get_timestamp()
        })
        
    except HTTPException:
        raise
    except Exception as e:
        error_response = formatter.format_error_response(
            error="코드 설명 생성 실패",
            detail=str(e),
            error_code="CODE_EXPLANATION_ERROR"
        )
        return JSONResponse(content=error_response, status_code=500)

@router.get("/code/examples")
async def get_code_examples():
    """코드 생성 요청 예시들"""
    return {
        "examples": [
            {
                "category": "웹 개발",
                "requests": [
                    "간단한 Flask 웹 애플리케이션 만들기",
                    "React 컴포넌트로 Todo 리스트 구현",
                    "REST API 엔드포인트 작성"
                ]
            },
            {
                "category": "데이터 처리",
                "requests": [
                    "CSV 파일 읽어서 데이터 분석하기",
                    "pandas로 데이터 전처리 함수 만들기",
                    "matplotlib으로 그래프 그리기"
                ]
            },
            {
                "category": "알고리즘",
                "requests": [
                    "퀵정렬 알고리즘 구현하기",
                    "이진 검색 함수 작성",
                    "피보나치 수열 생성기"
                ]
            },
            {
                "category": "유틸리티",
                "requests": [
                    "파일 백업 스크립트 만들기",
                    "이메일 발송 함수 구현",
                    "암호 생성기 프로그램"
                ]
            }
        ]
    }

@router.get("/code/status")
async def code_service_status():
    """코드 생성 서비스 상태"""
    return {
        "service": "code_generation",
        "provider": "OpenRouter (Claude-3-Sonnet)",
        "available": openrouter_service.is_available(),
        "supported_languages": 10,
        "supported_complexities": 3,
        "features": [
            "다중 언어 지원",
            "복잡도 조절",
            "주석 포함/제외",
            "코드 설명 생성",
            "실시간 검증"
        ]
    }