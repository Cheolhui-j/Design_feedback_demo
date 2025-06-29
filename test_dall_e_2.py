import openai
import requests

from PIL import Image

# JPEG 파일 로드
img = Image.open("test.jpeg").convert("RGBA")

# 흰 배경을 투명하게 (선택적 처리)
datas = img.getdata()
newData = []
for item in datas:
    if item[:3] == (255, 255, 255):  # 완전한 흰색 배경
        newData.append((255, 255, 255, 0))
    else:
        newData.append(item)
img.putdata(newData)

# PNG로 저장
img.save("test.png")

# OpenAI 클라이언트 생성
client = openai.OpenAI(api_key="")

# 입력 정보
input_image_path = "test.png"
prompt = "흰색 부분을 검은색으로 변경해주세요"

# 이미지 편집 요청
with open(input_image_path, "rb") as image_file:
    response = client.images.edit(
        image=image_file,
        prompt=prompt,
        n=1,
        size="1024x1024",
        response_format="url"
    )

# 결과 이미지 다운로드
edited_image_url = response.data[0].url
output_image_path = "output_ui.png"

image_bytes = requests.get(edited_image_url).content
with open(output_image_path, "wb") as f:
    f.write(image_bytes)

print(f"개선된 UI 이미지가 저장되었습니다: {output_image_path}")
