import torch
from diffusers import StableDiffusionInstructPix2PixPipeline
from PIL import Image
from io import BytesIO
import openai
import base64

# 1. OpenAI API 준비
openai.api_key = ""

def encode_image_to_base64(pil_image):
    buffered = BytesIO()
    pil_image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def generate_edit_prompt(image: Image.Image):
    base64_image = encode_image_to_base64(image)
    
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a senior UX designer giving constructive feedback about UI designs."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Please suggest a UI improvement for this image in one sentence."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        temperature=0.5,
        max_tokens=100
    )
    
    prompt = response.choices[0].message.content
    return prompt

# 2. InstructPix2Pix 모델 준비
pipe = StableDiffusionInstructPix2PixPipeline.from_pretrained(
    "timbrooks/instruct-pix2pix",
    torch_dtype=torch.float16,
    safety_checker=None
).to("cuda")

# 3. 입력 이미지 불러오기
input_image = Image.open("test.jpeg").convert("RGB")

# 4. OpenAI에 이미지 보내서 수정 프롬프트 얻기
generated_prompt = generate_edit_prompt(input_image)
print(f"✅ OpenAI가 생성한 프롬프트: {generated_prompt}")

# 5. 수정된 이미지 생성
edited_image = pipe(
    prompt=generated_prompt,
    image=input_image,
    num_inference_steps=50,
    image_guidance_scale=1.5,
    guidance_scale=7.5
).images[0]

# 6. 결과 저장
edited_image.save("edited_result.png")
print("✅ 수정된 이미지를 저장했습니다!")
