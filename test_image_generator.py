# ✅ UI 피드백 → 개선사항 → 재설계 이미지 생성 자동화 (설명+이미지 기반 개선)
import openai
import requests
import base64
from PIL import Image
from io import BytesIO

# OpenAI 클라이언트 설정
client = openai.OpenAI(api_key="")  # 🔁 API 키 설정 필요

# 🔹 1. 이미지 base64 인코딩
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

# 🔹 2. GPT-4o로 이미지 설명 생성
def generate_ui_description(image_path):
    base64_image = encode_image_to_base64(image_path)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that analyzes UI design images."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Please describe this UI design layout in detail."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        temperature=0.5,
        max_tokens=500
    )
    return response.choices[0].message.content.strip()

# 🔹 3. GPT-4o로 UI 개선점 도출 (설명 + 이미지 동시 입력)
def generate_ui_improvement_suggestions_with_image_and_description(image_path, description):
    base64_image = encode_image_to_base64(image_path)
    system_prompt = {
        "You're participating in an interview where you'll be looking at an app image and sharing your honest thoughts.\n"
        "- The goal is to help improve the app by making it easier to use and more enjoyable.\n" 
        "- You're just a regular user with no special knowledge about mobile apps or design. \n"
        "- So answer like you would in a real conversation—naturally and casually. \n" 
        "- You don’t need to use any difficult or technical words, and your answers don’t have to be long or super detailed. \n"
        "- Just look at the image, check out the graphics and text, and respond based on what you understand. \n"
        "- If you don’t see an image, please ask for the image to be shown first. \n"
    }
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"This is the UI description:\n\n{description}\n\nPlease suggest improvements based on this description and the image."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        temperature=0.7,
        max_tokens=500
    )
    return response.choices[0].message.content.strip()

# 🔹 4. 개선 반영된 생성용 프롬프트 구성
def create_improved_ui_prompt(description, suggestions):
    return (
        "Create a redesigned version of the following UI based on the described layout and these improvements.\n"
        f"Layout Description: {description}\n"
        f"Suggested Improvements: {suggestions}\n"
        "Design it in a clean, modern, and professional style."
    )

# 🔹 5. DALL·E 3로 이미지 생성
def generate_redesigned_ui(prompt, filename="redesigned_ui_add_description.png"):
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1
    )
    image_url = response.data[0].url
    img_data = requests.get(image_url).content
    with open(filename, "wb") as f:
        f.write(img_data)
    return image_url, filename

# 🔹 6. 전체 실행 흐름
if __name__ == "__main__":
    input_image = "test.jpeg"  # 분석할 이미지 경로

    print("🔍 UI 설명 생성 중...")
    description = generate_ui_description(input_image)
    print("📝 설명 완료:\n", description)

    print("💡 설명 + 이미지 기반 개선사항 도출 중...")
    suggestions = generate_ui_improvement_suggestions_with_image_and_description(input_image, description)
    print("✅ 개선사항:\n", suggestions)

    improved_prompt = create_improved_ui_prompt(description, suggestions)
    print("🎨 최종 프롬프트:\n", improved_prompt)

    print("📐 새로운 UI 생성 중...")
    image_url, saved_path = generate_redesigned_ui(improved_prompt)
    print(f"🖼️ 저장 완료: {saved_path}\n")
