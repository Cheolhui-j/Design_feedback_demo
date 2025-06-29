import openai
import base64

client = openai.OpenAI(api_key="")

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# ===== 1단계: OCR 추출 =====
def extract_ocr_text(image_path):
    base64_img = encode_image_to_base64(image_path)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "당신은 OCR 전문 비전 모델입니다."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "이 이미지에서 OCR처럼 텍스트만 정확하게 추출해줘."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                ]
            }
        ]
    )
    return response.choices[0].message.content

# ===== 2단계: UI 구조 분석 =====
def extract_ui_structure(image_path):
    base64_img = encode_image_to_base64(image_path)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "당신은 UI 레이아웃을 분석하는 UX 분석 전문가입니다."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "이 이미지에서 UI의 구성요소(사이드바, 테이블, 버튼 등)를 영역별로 분석해줘."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                ]
            }
        ]
    )
    return response.choices[0].message.content

# ===== 3단계: HTML 코드 생성 =====
def generate_ui_code(image_path, ocr_text, layout_description):
    base64_img = encode_image_to_base64(image_path)

    full_prompt = f"""
이 UI 화면의 OCR 결과는 다음과 같습니다:

--- OCR 결과 ---
{ocr_text}

UI 구조 분석 결과는 다음과 같습니다:

--- UI 구조 설명 ---
{layout_description}

위의 텍스트 + 이미지 + 분석 정보를 바탕으로,
React JSX가 아닌 **순수 HTML + Tailwind CSS** 형식으로 전체 UI 코드를 작성해주세요.

조건:
- HTML 문서 전체 구조 포함 (`<!DOCTYPE html>`, `<html>`, `<head>`, `<body>` 등)
- 시나리오 테이블, 입력폼, 탐지 조건, 활성화 스위치 등 포함
- 구조적 레이아웃 (왼쪽 사이드바, 오른쪽 메인 등)을 반영
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "당신은 UI 화면을 HTML로 생성하는 프론트엔드 전문가입니다."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": full_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                ]
            }
        ],
        max_tokens=4000,
    )
    return response.choices[0].message.content

# ===== 실행 통합 =====
def build_ui_code_from_image(image_path, output_path="final_ui.html"):
    ocr_text = extract_ocr_text(image_path)
    layout = extract_ui_structure(image_path)
    html_code = generate_ui_code(image_path, ocr_text, layout)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_code)
    print(f"✅ 최종 UI HTML 코드가 '{output_path}'에 저장되었습니다.")
    return html_code


build_ui_code_from_image('test.jpeg')